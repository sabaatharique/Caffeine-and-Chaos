import pygame
import sys

from student import Student
from courses import CourseManager
from events import wifi_failure_event
from environment import DAY_START, DAY_END, format_time, draw_clock, outage_overlap, day_name, get_todays_classes
from ui import (StatusBar, Button, InputBox, NumberBox, AlertBox,
                SetupWizard, ScheduleBuilder, ClassInterruptBox,
                QuizResultBox, AcademicDashboard, QuizWeekPromptBox,
                QuizInterruptBox, LabAssessmentInterruptBox, LabAssessmentResultBox)
from screens import (main_menu, game_screen, day_end_screen, save_prompt_screen,
                     exam_screen, midterm_results_screen, semester_end_screen,
                     semester_stats_screen)
from savegame import save_game, load_game, delete_save, save_exists

# Window & clock
pygame.init()

WIDTH, HEIGHT = 1000, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Caffeine & Chaos")

clock = pygame.time.Clock()

# Game state
time_of_day   = DAY_START
day_count     = 1
day_over      = False
burnout_active = False   # True while student is recovering from burnout
sick_active    = False   # True while student is sick

# Week tracking
week_count = 1 # current week number (starts at 1)
day_in_week = 1 # day within the current week (1-7)
week_actions: list[list] = [] # accumulated per-day action lists for current week
_current_day_actions_snapshot: list = [] # snapshot of day_actions at week-day start

print(f"Time of day: {format_time(time_of_day)}")

student = Student()
course_manager = CourseManager()

day_actions = []
daily_outages = wifi_failure_event()
week_replay_runner: "WeekReplayRunner | None" = None

# Class interrupt state (reset each day)
todays_classes: list = []   # [(start_h, end_h, course), ...]
_classes_resolved: set = set() # start_hours already handled today
_pending_class: tuple | None = None  # class currently shown in interrupt box
_classes_populated_for_day: int = 0  # day_count when todays_classes was last built

# Quiz interrupt state  
_quizzes_resolved_today: set = set()
# Each element is a tuple: (course_name, week, day_idx)
# Reset every time day_count increments, the same way _classes_resolved is reset.

# Lab assessment interrupt state
_lab_assessments_resolved_today: set = set()
# Each element is a tuple: (course_name, assessment_type)
# Reset every time day_count increments.


def record_action(action: str, hours: float, data=None):
    day_actions.append((action, hours, data))


# Replay State Machine
class ReplayRunner:
    """Drives fast-forward replay of a recorded day, one action per tick."""

    def __init__(self, student, course_manager, actions, n, start_day):
        self.student = student
        self.course_manager = course_manager
        self.actions = list(actions)
        self.total_days = n
        self.current_day = start_day
        self.days_done = 0
        self.action_idx = 0
        self.time_cursor = float(DAY_START)
        self.current_action = None

        self.pending_alert = None   # (title, body) or None
        self.msgs = []
        self.done = False
        self.burnout_occurred = False
        self.pending_quiz: tuple | None = None   # (quiz_dict, course) when waiting for player
        self.pending_lab_assessment: tuple | None = None  # (assessment_dict, course)

        self._day_outages = wifi_failure_event()
        self._outage_idx = 0

        self._start_new_day()

    def _start_new_day(self):
        self.current_day += 1
        self.days_done += 1
        self.action_idx = 0
        self.time_cursor = float(DAY_START)
        self._day_outages = wifi_failure_event()
        self._outage_idx = 0

    def tick(self):
        # If all days are done, finish up
        if self.days_done > self.total_days:
            self.done = True
            return [], None

        # If all actions for this day are done, run end_of_day
        if self.action_idx >= len(self.actions):
            sweep_missed_assessments(self.course_manager, self.current_day, self.msgs)
            day_msgs = self.student.end_of_day()
            self.msgs.extend(day_msgs)
            self.msgs.append(f"Day {self.current_day} completed (fast-forward).")
            
            alert_info = None
            if any("[SICK!]" in m for m in day_msgs):
                alert_info = (
                    "YOU'RE SICK!",
                    "You've fallen ill!  Health -10, Stress +10.\n"
                    "Efficiency is halved and classes are blocked.\n"
                    "REST UP OR YOUR STATS WILL CRUMBLE!",
                    "sickness"
                )
            elif any("[RECOVERED]" in m for m in day_msgs):
                self.msgs = [m for m in self.msgs if not m.startswith('[SICK')]
                alert_info = (
                    "RECOVERED!",
                    "You've fought off the illness and are back to full efficiency.\n"
                    "Your learning and attendance potential are restored.\n"
                    "STAY VIGILANT!",
                    "recovery"
                )

            if any("Burnout!" in m for m in day_msgs):
                self.burnout_occurred = True
                self.msgs.append("Loop paused. You need to recover!")
                self.done = True
                return day_msgs + [f"Day {self.current_day} completed (fast-forward)."], alert_info
            
            if self.days_done >= self.total_days:
                self.done = True
                return day_msgs + [f"Day {self.current_day} completed (fast-forward)."], alert_info
            
            # Start next day
            self._start_new_day()
            return day_msgs + [f"Day {self.current_day - 1} completed (fast-forward)."], alert_info

        action, hours, data = self.actions[self.action_idx]
        action_start = self.time_cursor
        action_end   = self.time_cursor + hours

        # Fire an outage interrupt before this action if one overlaps
        # Skip WiFi alerts during attend_class — player is not at home
        if self._outage_idx < len(self._day_outages) and action != 'attend_class':
            outage = self._day_outages[self._outage_idx]
            if outage["start"] < action_end:
                # Fire the outage interrupt BEFORE running the action
                self._outage_idx += 1
                dur_min = round(outage["duration"] * 60)
                at_time = format_time(outage["start"])
                title = "WiFi Outage!"
                body = (f"At {at_time} on Day {self.current_day}, "
                        f"wifi went down for {dur_min} minutes.")
                o_end = outage["start"] + outage["duration"]
                overlap = max(0.0, min(action_end, o_end) - max(action_start, outage["start"]))
                if overlap > 0 and action == 'study':
                    interrupted_min = round(overlap * 60)
                    body += f"\nYour study session was interrupted for {interrupted_min} minutes."
                    return [], (title, body, "yellow")
                else:
                    self.msgs.append(f"Notice: WiFi went down for {dur_min} mins (no effect on {action}).")

        # Run the action
        new_msgs = []
        _diw = ((self.current_day - 1) % 7) + 1
        _week = ((self.current_day - 1) // 7) + 1
        overlap  = outage_overlap(self._day_outages, action_start, action_end)
        wifi_on  = (overlap > 0 and action == 'study')
        if overlap > 0:
            self.student.stats["hours_wifi_outage"] += overlap

        _actual = None  # course found by attend_class lookup (used by silent resolution)
        if action == 'study' and self.student.action_status['study']:
            target  = data if data else next(
                (c for c in self.course_manager.courses if c.course_type == "Theory"),
                self.course_manager.courses[0]
            )
            avg = self.course_manager.get_average_knowledge()
            new_msgs.extend(self.student.apply_hunger_decay(hours))
            new_msgs.extend(self.student.study(course=target, hours=hours,
                                                avg_knowledge=avg, wifi_penalty=wifi_on))
            if wifi_on:
                new_msgs.append("WiFi was down during part of your study session!")
        elif action == 'sleep' and self.student.action_status['sleep']:
            new_msgs.extend(self.student.apply_hunger_decay(hours))
            new_msgs.extend(self.student.rest(hours=hours))
        elif action == 'relax' and self.student.action_status['relax']:
            new_msgs.extend(self.student.apply_hunger_decay(hours))
            new_msgs.extend(self.student.take_break(hours=hours))
        elif action == 'eat' and self.student.action_status['eat']:
            new_msgs.extend(self.student.apply_hunger_decay(0.5))
            new_msgs.extend(self.student.eat())
        elif action == 'coffee' and self.student.action_status['coffee']:
            new_msgs.extend(self.student.apply_hunger_decay(0.25))
            new_msgs.extend(self.student.drink_coffee())
        elif action == 'attend_class':
            if _diw <= 5:  # weekdays only
                _todays = get_todays_classes(self.course_manager.courses, _diw, _week)
                _actual = next((c for (s, e, c) in _todays if abs(s - action_start) < 0.1), None)
            else:
                _actual = None  # no classes on weekends
            if _actual:
                new_msgs.extend(self.student.attend_class(_actual, _week))

        # Silent Class Resolution (for missed/auto-attended classes during replay)
        # Runs for ALL action types. For 'attend_class' the directly-attended course
        # is tracked so we never double-count it.
        _directly_attended = _actual if action == 'attend_class' else None
        if _diw <= 5:
            _todays = get_todays_classes(self.course_manager.courses, _diw, _week)
            for s, e, c in _todays:
                if c is _directly_attended:
                    continue  # already handled above
                if action_start < e <= action_end:
                    if class_interrupt_box.attend_all:
                        new_msgs.extend(self.student.attend_class(c, _week))
                        new_msgs.append(f"Auto-attended {c.name} during replay.")
                    else:
                        c.occurred_classes += 1

        # Quiz interrupt — pause and let player decide
        from environment import SLOT_TIMES
        for c in self.course_manager.courses:
            if c.course_type != "Theory":
                continue
            for quiz in c.scheduled_quizzes:
                if quiz["taken"]:
                    continue
                _q_wk  = ((self.current_day - 1) // 7) + 1
                _q_diw = ((self.current_day - 1) % 7) + 1
                if quiz["week"] != _q_wk or quiz["day_idx"] != (_q_diw - 1):
                    continue
                start_h, _ = SLOT_TIMES[quiz["slot_idx"]]
                if not (action_start <= start_h < action_end or self.time_cursor >= start_h):
                    continue
                # Pause the runner — main loop will open QuizInterruptBox
                self.pending_quiz = (quiz, c)
                break
            if self.pending_quiz:
                break

        # Lab assessment interrupt — pause and let player decide
        if not self.pending_quiz:
            for c in self.course_manager.courses:
                if c.course_type != "Lab":
                    continue
                for la in c.scheduled_lab_assessments:
                    if la["taken"]:
                        continue
                    _la_wk  = ((self.current_day - 1) // 7) + 1
                    _la_diw = ((self.current_day - 1) % 7) + 1
                    if la["week"] != _la_wk or la["day_idx"] != (_la_diw - 1):
                        continue
                    start_h, _ = SLOT_TIMES[la["slot_idx"]]
                    if not (action_start <= start_h < action_end or self.time_cursor >= start_h):
                        continue
                    self.pending_lab_assessment = (la, c)
                    break
                if self.pending_lab_assessment:
                    break

        if self.pending_quiz or self.pending_lab_assessment:
            # Advance time/action BEFORE pausing so the interrupt fires at the right moment
            self.time_cursor    = action_end
            self.action_idx    += 1
            self.current_action = action
            self.msgs.extend(new_msgs)
            return new_msgs, None

        self.time_cursor    = action_end
        self.action_idx    += 1
        self.current_action = action
        self.msgs.extend(new_msgs)

        wait_time = 300
        if self.student.is_sick:
            wait_time = 800  # Slow down simulation when sick to make messages readable
        pygame.time.wait(wait_time)
        return new_msgs, None

    def last_msgs(self, n=5):
        return self.msgs[-n:]


# Week Replay State Machine
class WeekReplayRunner:
    """Replays a recorded week (up to 7 day-action-lists) for N additional weeks."""

    def __init__(self, student, course_manager, week_actions, n_weeks, start_day, start_week):
        """
        week_actions: list of up to 7 lists, each being the day_actions for that day.
        n_weeks:      how many additional weeks to replay.
        start_day:    day_count at the start of the replay.
        start_week:   week_count at the start of the replay.
        """
        self.student = student
        self.course_manager = course_manager
        # Deep-copy each day's action list so originals are untouched
        self.week_actions = [list(d) for d in week_actions]
        self.total_weeks  = n_weeks
        self.weeks_done   = 0
        self.current_day  = start_day
        self.current_week = start_week + 1
        self.day_in_week  = 0          # 0-indexed within the replaying week
        self.action_idx   = 0
        self.time_cursor  = float(DAY_START)

        self.pending_alert = None
        self.msgs = []
        self.done = False
        self.burnout_occurred = False
        self.current_action = None
        self.quiz_week_pending = False   # True when next week has quizzes — awaiting player choice
        self.pending_quiz: tuple | None = None   # (quiz_dict, course) when waiting for player
        self.pending_lab_assessment: tuple | None = None  # (assessment_dict, course)

        self._day_outages = wifi_failure_event()
        self._outage_idx  = 0

        # Rewind quiz taken/missed flags for every week we're about to fast-forward
        for w in range(start_week + 1, start_week + n_weeks + 1):
            self.course_manager.reset_quizzes_for_week(w)

    #  helpers
    def _start_new_day(self):
        self.current_day   += 1
        self.action_idx     = 0
        self.time_cursor    = float(DAY_START)
        self._day_outages   = wifi_failure_event()
        self._outage_idx    = 0

    def _start_new_week(self):
        """Advance week counter and reset day pointer. Does NOT advance current_day."""
        self.weeks_done   += 1
        self.day_in_week   = 0
        self.current_week += 1
        # Rewind quizzes for the week we're about to replay
        self.course_manager.reset_quizzes_for_week(self.current_week)

    @property
    def current_day_in_week(self):
        """1-based day index within the replaying week."""
        return self.day_in_week + 1

    def get_next_week_assessments(self) -> list[dict]:
        """Return enriched dicts for untaken quizzes and lab tests in current_week."""
        from environment import SLOT_TIMES, DAYS_OF_WEEK, format_time
        result = []
        for course in self.course_manager.courses:
            if course.course_type == "Theory":
                for quiz in course.scheduled_quizzes:
                    if quiz["taken"]:
                        continue
                    if quiz["week"] == self.current_week:
                        day_str  = DAYS_OF_WEEK[quiz["day_idx"]]
                        start_h, _ = SLOT_TIMES[quiz["slot_idx"]]
                        result.append({
                            "day":         day_str,
                            "time":        format_time(start_h),
                            "course_name": course.name,
                            "event_name":  f"Quiz {quiz['quiz_number']}",
                        })
            elif course.course_type == "Lab":
                for la in getattr(course, "scheduled_lab_assessments", []):
                    if la["taken"]:
                        continue
                    if la["week"] == self.current_week:
                        day_str  = DAYS_OF_WEEK[la["day_idx"]]
                        start_h, _ = SLOT_TIMES[la["slot_idx"]]
                        atype = la["assessment_type"].replace('_', ' ').title()
                        result.append({
                            "day":         day_str,
                            "time":        format_time(start_h),
                            "course_name": course.name,
                            "event_name":  atype,
                        })
        return result

    # tick
    def tick(self):
        """Advance by one action; return (new_msgs, alert_info)."""
        if self.done:
            return [], None

        # All weeks done?
        if self.weeks_done >= self.total_weeks:
            self.done = True
            return [], None

        # All days in this week done?
        if self.day_in_week >= len(self.week_actions):
            completed_week = self.current_week
            self._start_new_week()   # bumps weeks_done, current_week; does NOT touch current_day
            if self.weeks_done >= self.total_weeks:
                self.done = True
                return [f"Week {completed_week} completed (fast-forward)."], None
            # Check if the new week has any upcoming quizzes or labs
            assessments = self.get_next_week_assessments()
            if assessments:
                self.quiz_week_pending = True
                msg = f"Week {completed_week} done! Week {self.current_week} has assessments scheduled."
                self.msgs.append(msg)
                return [msg], None   # Pause — main loop will handle the prompt
            # No quizzes — start next week immediately
            self._start_new_day()
            msg = f"Week {completed_week} done! Week {self.current_week} begins (fast-forward)."
            self.msgs.append(msg)
            return [msg], None

        actions = self.week_actions[self.day_in_week]

        # All actions for this day done?
        if self.action_idx >= len(actions):
            sweep_missed_assessments(self.course_manager, self.current_day, self.msgs)
            day_msgs = self.student.end_of_day()
            self.msgs.extend(day_msgs)
            self.msgs.append(f"Day {self.current_day} completed (fast-forward).")
            
            alert_info = None
            if any("[SICK!]" in m for m in day_msgs):
                alert_info = (
                    "YOU'RE SICK!",
                    "You've fallen ill!  Health -10, Stress +10.\n"
                    "Efficiency is halved and classes are blocked.\n"
                    "REST UP OR YOUR STATS WILL CRUMBLE!",
                    "sickness"
                )
            elif any("[RECOVERED]" in m for m in day_msgs):
                self.msgs = [m for m in self.msgs if not m.startswith('[SICK')]
                alert_info = (
                    "RECOVERED!",
                    "You've fought off the illness and are back to full efficiency.\n"
                    "Your learning and attendance potential are restored.\n"
                    "STAY VIGILANT!",
                    "recovery"
                )

            if any("Burnout!" in m for m in day_msgs):
                self.burnout_occurred = True
                self.done = True
                return day_msgs + [f"Day {self.current_day} completed (fast-forward)."], alert_info
            
            self.day_in_week += 1
            # Only start next day now if there are more days this week;
            # otherwise let the week-boundary tick handle it cleanly.
            if self.day_in_week < len(self.week_actions):
                self._start_new_day()
            return day_msgs + [f"Day {self.current_day} completed (fast-forward)."], alert_info

        action, hours, data = actions[self.action_idx]
        action_start = self.time_cursor
        action_end   = self.time_cursor + hours

        # WiFi outage interrupt — suppressed during attend_class (player is at university)
        if self._outage_idx < len(self._day_outages) and action != 'attend_class':
            outage = self._day_outages[self._outage_idx]
            if outage["start"] < action_end:
                self._outage_idx += 1
                dur_min = round(outage["duration"] * 60)
                at_time = format_time(outage["start"])
                title = "WiFi Outage!"
                body  = (f"At {at_time} on Day {self.current_day}, "
                         f"wifi went down for {dur_min} minutes.")
                o_end   = outage["start"] + outage["duration"]
                overlap = max(0.0, min(action_end, o_end) - max(action_start, outage["start"]))
                if overlap > 0 and action == 'study':
                    body += f"\nYour study session was interrupted for {round(overlap*60)} minutes."
                    return [], (title, body, "yellow")
                else:
                    self.msgs.append(f"Notice: WiFi went down for {dur_min} mins (no effect on {action}).")

        # Run action
        new_msgs = []
        _diw = ((self.current_day - 1) % 7) + 1
        _week = ((self.current_day - 1) // 7) + 1
        overlap  = outage_overlap(self._day_outages, action_start, action_end)
        wifi_on  = (overlap > 0 and action == 'study')
        if overlap > 0:
            self.student.stats["hours_wifi_outage"] += overlap

        _actual = None  # course found by attend_class lookup (used by silent resolution)
        if action == 'study' and self.student.action_status['study']:
            target = data if data else next(
                (c for c in self.course_manager.courses if c.course_type == "Theory"),
                self.course_manager.courses[0]
            )
            avg = self.course_manager.get_average_knowledge()
            new_msgs.extend(self.student.apply_hunger_decay(hours))
            new_msgs.extend(self.student.study(course=target, hours=hours,
                                                avg_knowledge=avg, wifi_penalty=wifi_on))
            if wifi_on:
                new_msgs.append("WiFi was down during part of your study session!")
        elif action == 'sleep' and self.student.action_status['sleep']:
            new_msgs.extend(self.student.apply_hunger_decay(hours))
            new_msgs.extend(self.student.rest(hours=hours))
        elif action == 'relax' and self.student.action_status['relax']:
            new_msgs.extend(self.student.apply_hunger_decay(hours))
            new_msgs.extend(self.student.take_break(hours=hours))
        elif action == 'eat' and self.student.action_status['eat']:
            new_msgs.extend(self.student.apply_hunger_decay(0.5))
            new_msgs.extend(self.student.eat())
        elif action == 'coffee' and self.student.action_status['coffee']:
            new_msgs.extend(self.student.apply_hunger_decay(0.25))
            new_msgs.extend(self.student.drink_coffee())
        elif action == 'attend_class':
            # Use the class actually scheduled on this replay day at this time slot.
            if _diw <= 5:
                _todays = get_todays_classes(self.course_manager.courses, _diw, _week)
                _actual = next((c for (s, e, c) in _todays if abs(s - action_start) < 0.1), None)
            else:
                _actual = None
            if _actual:
                new_msgs.extend(self.student.attend_class(_actual, _week))

        # Silent Class Resolution (for all classes during week replay)
        # Runs for ALL action types. Week repeat always attends all scheduled classes
        # on the replayed days — class_interrupt_box.attend_all is always False by
        # the time WeekReplayRunner starts (reset at each day-end), so we don't gate
        # on it here. The directly-attended course is skipped to avoid double-counting.
        _directly_attended = _actual if action == 'attend_class' else None
        if _diw <= 5:
            _todays = get_todays_classes(self.course_manager.courses, _diw, _week)
            for s, e, c in _todays:
                if c is _directly_attended:
                    continue  # already handled above
                if action_start < e <= action_end:
                    new_msgs.extend(self.student.attend_class(c, _week))
                    new_msgs.append(f"Auto-attended {c.name} during week replay.")

        # Quiz interrupt — pause and let player decide
        from environment import SLOT_TIMES
        for c in self.course_manager.courses:
            if c.course_type != "Theory":
                continue
            for quiz in c.scheduled_quizzes:
                if quiz["taken"]:
                    continue
                if quiz["week"] != self.current_week or quiz["day_idx"] != (self.current_day_in_week - 1):
                    continue
                start_h, _ = SLOT_TIMES[quiz["slot_idx"]]
                if not (action_start <= start_h < action_end or self.time_cursor >= start_h):
                    continue
                self.pending_quiz = (quiz, c)
                break
            if self.pending_quiz:
                break

        # Lab assessment interrupt — pause and let player decide
        if not self.pending_quiz:
            for c in self.course_manager.courses:
                if c.course_type != "Lab":
                    continue
                for la in c.scheduled_lab_assessments:
                    if la["taken"]:
                        continue
                    if la["week"] != self.current_week or la["day_idx"] != (self.current_day_in_week - 1):
                        continue
                    start_h, _ = SLOT_TIMES[la["slot_idx"]]
                    if not (action_start <= start_h < action_end or self.time_cursor >= start_h):
                        continue
                    self.pending_lab_assessment = (la, c)
                    break
                if self.pending_lab_assessment:
                    break

        if self.pending_quiz or self.pending_lab_assessment:
            self.time_cursor  = action_end
            self.action_idx  += 1
            self.current_action = action
            self.msgs.extend(new_msgs)
            return new_msgs, None

        self.time_cursor  = action_end
        self.action_idx  += 1
        self.current_action = action
        self.msgs.extend(new_msgs)

        wait_time = 50
        if self.student.is_sick:
            wait_time = 400  # Slower for week replay when sick
        pygame.time.wait(wait_time)
        return new_msgs, None

    def last_msgs(self, n=5):
        return self.msgs[-n:]



# Game states
MAIN_MENU = "main_menu"
SETUP_SCREEN = "setup_screen"
GAME_SCREEN = "game_screen"
DAY_END_SCREEN = "day_end_screen"
EXAM_SCREEN = "exam_screen"
MIDTERM_RESULTS_SCREEN = "midterm_results_screen"
SEMESTER_END_SCREEN = "semester_end_screen"
SAVE_PROMPT = "save_prompt"
current_screen_state = MAIN_MENU

# Scroll state for results pages
_results_scroll_y = 0.0
_results_content_h = 0
_sem_end_page = 0   # 0 = results page, 1 = stats page

# Semester tracking
exam_type = "mid"   # "mid" or "final"


def get_semester_phase(wk: int) -> str:
    """Return the current semester phase based on week number."""
    if wk <= 7:
        return "pre_mid"
    elif wk <= 15:
        return "post_mid"
    else:
        return "done"


def _max_week_repeats(wk: int) -> int:
    """Maximum additional weeks a player may replay from week wk."""
    phase = get_semester_phase(wk)
    if phase == "pre_mid":
        return max(0, 7 - wk)
    elif phase == "post_mid":
        return max(0, 15 - wk)
    return 0

# Assets
main_bg = pygame.image.load("assets/images/main.jpg")
bg_map  = {
    'study':        pygame.image.load("assets/images/study.jpg"),
    'sleep':        pygame.image.load("assets/images/sleep.jpg"),
    'relax':        pygame.image.load("assets/images/break.jpg"),
    'coffee':       pygame.image.load("assets/images/coffee.jpg"),
    'eat':          pygame.image.load("assets/images/eat.jpg"),
    'attend_class': pygame.image.load("assets/images/class.jpg"),
    'burnout':      pygame.image.load("assets/images/burnout.jpg"),
    'sick':         pygame.image.load("assets/images/burnout.jpg"),  # reuse burnout bg for now
    'default':      pygame.image.load("assets/images/study.jpg"),
}
current_game_bg = bg_map['default']

# Fonts
button_font  = pygame.font.Font("assets/fonts/Papernotes.otf", 22)
message_font = pygame.font.Font("assets/fonts/Papernotes.otf", 20)
input_font   = pygame.font.Font("assets/fonts/Papernotes.otf", 16)
clock_font   = pygame.font.Font("assets/fonts/Digital-7.ttf",  50)
date_font    = pygame.font.Font("assets/fonts/Digital-7.ttf",  30)
alert_title_font = pygame.font.Font("assets/fonts/Papernotes.otf", 28)
alert_body_font  = pygame.font.Font("assets/fonts/Papernotes.otf", 22)

# UI Widgets
input_box  = InputBox(message_font, input_font)
repeat_box = NumberBox(message_font, input_font)
alert_box  = AlertBox(alert_title_font, alert_body_font)
class_interrupt_box = ClassInterruptBox(button_font, input_font)
wizard     = SetupWizard(message_font, input_font, button_font)
quiz_result_box = QuizResultBox(WIDTH, HEIGHT)
quiz_week_prompt_box = QuizWeekPromptBox(alert_title_font, alert_body_font)
quiz_interrupt_box = QuizInterruptBox(button_font, input_font)
lab_assessment_interrupt_box = LabAssessmentInterruptBox(button_font, input_font)
lab_assessment_result_box = LabAssessmentResultBox(WIDTH, HEIGHT)
academic_dashboard = AcademicDashboard(
    WIDTH, HEIGHT,
    message_font,
    message_font,
)

pending_action: str | None = None

# Status bars
bar_w = 130
bar_h = 16
bar_space = (WIDTH - 6 * bar_w) / 7
bars = [
    StatusBar(bar_space, 60, bar_w, bar_h, "Knowledge", message_font),
    StatusBar(bar_space*2 + bar_w, 60, bar_w, bar_h, "Sleep", message_font),
    StatusBar(bar_space*3 + bar_w*2, 60, bar_w, bar_h, "Health", message_font),
    StatusBar(bar_space*4 + bar_w*3, 60, bar_w, bar_h, "Stress", message_font),
    StatusBar(bar_space*5 + bar_w*4, 60, bar_w, bar_h, "Motivation", message_font),
    StatusBar(bar_space*6 + bar_w*5, 60, bar_w, bar_h, "Hunger", message_font),
]

# Action buttons
start_btn = Button(WIDTH - 160, HEIGHT - 80, 120, 40, "New Game", button_font, 'black')

# Main-menu "Continue" button (shown only when a save file exists)
continue_menu_btn = Button(WIDTH - 160, HEIGHT - 130, 120, 40, "Continue", button_font, 'black')

btn_w = 140
btn_h = 40
btn_space = (WIDTH - 5 * btn_w) / 6
study_btn = Button(btn_space, HEIGHT - 80, btn_w, btn_h, "Study", button_font)
sleep_btn = Button(btn_space*2 + btn_w, HEIGHT - 80, btn_w, btn_h, "Sleep", button_font)
relax_btn = Button(btn_space*3 + btn_w*2, HEIGHT - 80, btn_w, btn_h, "Relax", button_font)
drink_coffee_btn = Button(btn_space*4 + btn_w*3, HEIGHT - 80, btn_w, btn_h, "Coffee", button_font)
eat_btn = Button(btn_space*5 + btn_w*4, HEIGHT - 80, btn_w, btn_h, "Food", button_font)
stats_btn = Button(btn_space*5 + btn_w*4, HEIGHT - 440, btn_w, btn_h, "Course Panel", button_font)

dashboard_btn = None   # Removed as it's now persistent
game_buttons = [study_btn, sleep_btn, relax_btn, drink_coffee_btn, eat_btn, stats_btn]

# Day-end buttons  (4 buttons: Continue | Repeat Day | Repeat Week | Quit)
_btn_y = HEIGHT // 2 + 50
_btn_w = 120
_total_btns = 4
_gap = (WIDTH - _total_btns * _btn_w) // (_total_btns + 1)
continue_btn = Button(_gap, _btn_y, _btn_w, 40, "Continue", button_font)
repeat_btn = Button(_gap * 2 + _btn_w, _btn_y, _btn_w, 40, "Repeat Day", button_font)
repeat_week_btn = Button(_gap * 3 + _btn_w * 2, _btn_y, _btn_w, 40, "Repeat Week", button_font)
quit_btn = Button(_gap * 4 + _btn_w * 3, _btn_y, _btn_w, 40, "Quit", button_font)

# Exam screen / semester end continue button (centred)
exam_continue_btn = Button(WIDTH // 2 - 60, HEIGHT // 2 + 110, 120, 40, "Continue", button_font)
sem_quit_btn = Button(WIDTH // 2 - 60, HEIGHT // 2 + 120, 120, 40, "Quit",     button_font)
sem_next_btn = Button(840, HEIGHT - 50, 100, 36, "Stats >",   button_font)
sem_prev_btn = Button( 60, HEIGHT - 50, 100, 36, "< Results", button_font)

# Save-prompt buttons (shown in the SAVE_PROMPT overlay)
_sp_y = HEIGHT // 2 + 20
_sp_gap = 20
_sp_w = 120
save_yes_btn = Button(WIDTH // 2 - _sp_w - _sp_gap // 2, _sp_y, _sp_w, 40, "Save & Quit", button_font)
save_no_btn  = Button(WIDTH // 2 + _sp_gap // 2,           _sp_y, _sp_w, 40, "Quit",       button_font)

week_repeat_box = NumberBox(message_font, input_font)

messages: list[str] = []
replay_runner: ReplayRunner | None = None

# Track the last non-prompt screen state so SAVE_PROMPT can render a backdrop
_last_game_screen: str = MAIN_MENU
_optimal_data = None


def sweep_missed_assessments(c_manager, d_count, out_list):
    """Mark unresolved quizzes/labs for today as missed and append notifications."""
    diw = ((d_count - 1) % 7) + 1
    wk = ((d_count - 1) // 7) + 1
    for c in c_manager.courses:
        if c.course_type == "Theory":
            for q in c.scheduled_quizzes:
                if not q["taken"] and q["week"] == wk and q["day_idx"] == (diw - 1):
                    q["taken"] = True
                    q["missed"] = True
                    out_list.append(f"[QUIZ] {c.name} — Quiz {q['quiz_number']} SKIPPED (timeout).")
        elif c.course_type == "Lab":
            for la in getattr(c, "scheduled_lab_assessments", []):
                if not la["taken"] and la["week"] == wk and la["day_idx"] == (diw - 1):
                    la["taken"] = True
                    la["missed"] = True
                    atype = la["assessment_type"].replace('_', ' ').title()
                    out_list.append(f"[LAB] {c.name} — {atype} SKIPPED (timeout).")


def _check_day_end(new_msgs: list[str]) -> list[str]:
    """Call end_of_day if the day clock has run out; return extra messages."""
    global day_over, burnout_active, sick_active, current_screen_state, current_game_bg
    if round(time_of_day * 60) >= round(DAY_END * 60):
        sweep_missed_assessments(course_manager, day_count, new_msgs)
        eod_msgs = student.end_of_day()
        new_msgs.extend(eod_msgs)
        new_msgs.append(f"Day {day_count} is over!")
        print(f"Day {day_count} ended.")
        if any("Burnout!" in m for m in eod_msgs):
            burnout_active = True
            current_game_bg = bg_map['burnout']
        if any("recovered from burnout" in m for m in eod_msgs):
            burnout_active = False
        # Sickness detection 
        sick_active = student.is_sick
        if any("[SICK!]" in m for m in eod_msgs):
            current_game_bg = bg_map.get('sick', bg_map['burnout'])
            alert_box.open(
                "YOU'RE SICK!",
                "You've fallen ill!  Health -10, Stress +10.\n"
                "Efficiency is halved and classes are blocked.\n"
                "REST UP OR YOUR STATS WILL CRUMBLE!",
                color_type="sickness"
            )
        elif any("[RECOVERED]" in m for m in eod_msgs):
            sick_active = False
            if not burnout_active:
                current_game_bg = bg_map['default']
            alert_box.open(
                "RECOVERED!",
                "You've fought off the illness and are back to full efficiency.\n"
                "Your learning and attendance potential are restored.\n"
                "STAY VIGILANT!",
                color_type="recovery"
            )
        # END sickness detection
        day_over = True
        current_screen_state = DAY_END_SCREEN
    return new_msgs


# Main loop
clock = pygame.time.Clock()
dt = 0
running = True
while running:
    dt = clock.tick(60) / 1000.0
    academic_dashboard.update(dt)
    
    remaining_hours = DAY_END - time_of_day

    # Derive week tracking from day_count (always consistent, works with any runner)
    day_in_week = ((day_count - 1) % 7) + 1   # 1-7
    week_count = ((day_count - 1) // 7) + 1  # 1, 2, ...

    # Button enable state
    if day_over or remaining_hours <= 0:
        for btn in game_buttons:
            if btn != stats_btn:
                btn.enabled = False
        stats_btn.enabled = True
    else:
        study_btn.enabled = student.action_status['study'] and remaining_hours > 0
        sleep_btn.enabled = student.action_status['sleep'] and remaining_hours > 0
        relax_btn.enabled = student.action_status['relax'] and remaining_hours > 0
        eat_btn.enabled = student.action_status['eat'] and remaining_hours >= 0.5
        drink_coffee_btn.enabled = student.action_status['coffee'] and remaining_hours >= 0.25

    # Phase-start flow constraints (week 1 = start of semester; week 8 = start of post-mid)
    if week_count in (1, 8) and day_in_week == 7:  # Sunday of phase week 1: can't repeat day
        repeat_btn.enabled = False
    else:
        repeat_btn.enabled = not burnout_active
    # Repeat Week: enabled once a full week (day 7) is complete
    repeat_week_btn.enabled = not burnout_active and day_in_week == 7

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            # Route X-button through save prompt (unless already on main menu with no progress)
            if current_screen_state == MAIN_MENU:
                running = False
            else:
                current_screen_state = SAVE_PROMPT

        # Mouse-wheel scrolling for results screens
        if event.type == pygame.MOUSEWHEEL:
            if current_screen_state == MIDTERM_RESULTS_SCREEN or current_screen_state == SEMESTER_END_SCREEN:
                _results_scroll_y -= event.y * 28
                _results_scroll_y = max(0.0, min(_results_scroll_y,
                                                  max(0.0, _results_content_h - HEIGHT + 120)))


        # Quiz & Lab result box dismissal
        if quiz_result_box.handle_event(event):
            continue    # event consumed; don't pass to buttons below
        if lab_assessment_result_box.handle_event(event):
            continue

        # Academic dashboard expansion/collapse
        if academic_dashboard.handle_event(event):
            continue

        # Save Prompt
        if current_screen_state == SAVE_PROMPT:
            if save_yes_btn.clicked(event):
                save_game(
                    student, course_manager,
                    time_of_day, day_count, week_count, day_in_week,
                    burnout_active, day_over,
                    day_actions, week_actions,
                    classes_resolved=_classes_resolved,
                    quizzes_resolved=_quizzes_resolved_today,
                    attend_all_today=class_interrupt_box.attend_all,
                )
                running = False
            if save_no_btn.clicked(event):
                running = False

        # Main Menu
        elif current_screen_state == MAIN_MENU:
            if start_btn.clicked(event):
                # New game: wipe any existing save
                delete_save()
                student = Student()
                course_manager = CourseManager()
                wizard.reset()
                current_screen_state = SETUP_SCREEN

            if save_exists() and continue_menu_btn.clicked(event):
                # Load saved game
                loaded = load_game(student, course_manager)
                if loaded:
                    time_of_day = loaded["time_of_day"]
                    day_count = loaded["day_count"]
                    week_count = loaded["week_count"]
                    day_in_week = loaded["day_in_week"]
                    burnout_active = loaded["burnout_active"]
                    day_over = loaded["day_over"]
                    day_actions[:] = loaded["day_actions"]
                    week_actions[:] = loaded["week_actions"]
                    # Restore class interrupt state
                    _classes_resolved.clear()
                    _classes_resolved.update(loaded.get("classes_resolved_today", set()))
                    # Restore quiz interrupt state
                    _quizzes_resolved_today.clear()
                    _quizzes_resolved_today.update(loaded.get("quizzes_resolved_today", set()))

                    class_interrupt_box.attend_all = loaded.get("attend_all_today", False)
                    daily_outages = wifi_failure_event()
                    messages = [f"Welcome back! Week {week_count} - {day_name(day_in_week)} (Day {day_count})"]

                    # Guard for old saves: generate quizzes if missing
                    for c in course_manager.courses:
                        if c.course_type == "Theory" and not c.scheduled_quizzes:
                            course_manager.schedule_all_quizzes()
                        if c.course_type == "Lab" and not getattr(c, "scheduled_lab_assessments", []):
                            course_manager.schedule_all_lab_assessments()

                    # Route to the correct screen based on saved state
                    if week_count > 15:
                        # Semester is over — generate finals if not already done and go to results
                        for c in course_manager.courses:
                            if c.course_type == "Theory" and c.final_mark is None:
                                if not c.is_attendance_eligible():
                                    c.final_mark = 0
                                else:
                                    c.generate_final_mark(week_count, student.stress, student.sleep, student.health, student.is_sick)
                            elif c.course_type == "Lab" and c.lab_final is None:
                                if not c.is_attendance_eligible():
                                    c.lab_final = 0
                                else:
                                    c.generate_lab_final(week_count, student.stress, student.health, student.is_sick)
                        _results_scroll_y = 0.0
                        _sem_end_page = 0
                        _last_game_screen = SEMESTER_END_SCREEN
                        current_screen_state = SEMESTER_END_SCREEN
                    elif day_over:
                        _last_game_screen = DAY_END_SCREEN
                        current_screen_state = DAY_END_SCREEN
                    else:
                        _last_game_screen = GAME_SCREEN
                        current_screen_state = GAME_SCREEN

        # Setup Screen
        elif current_screen_state == SETUP_SCREEN:
            # Initialise courses + schedule builder as soon as step 5 is reached
            if wizard.step == 5 and not getattr(wizard, '_schedule_initialised', False):
                student = Student(type_mult=wizard.result["type_mult"])
                course_manager.setup_from_wizard(wizard.result)
                wizard.schedule_builder.set_courses(course_manager.courses)
                wizard._schedule_initialised = True

            wizard.handle_event(event)

            if wizard.done:
                # Apply target cgpa
                student.target_cgpa = wizard.result.get("target_cgpa", 0.0)
                # Apply the schedule grid to each Course object
                course_manager.apply_schedule(wizard.result.get("schedule", {}))
                course_manager.schedule_all_quizzes()
                course_manager.schedule_all_lab_assessments()
                wizard._schedule_initialised = False
                current_screen_state = GAME_SCREEN

        # Game Screen
        elif current_screen_state == GAME_SCREEN:
            # Class interrupt: handle Attend / Skip 
            if class_interrupt_box.active:
                class_result = class_interrupt_box.handle_event(event)
                if class_result is not None and _pending_class is not None:
                    p_start, p_end, p_course = _pending_class
                    _classes_resolved.add(p_start)
                    _pending_class = None
                    if class_result == "attend":
                        new_msgs = student.attend_class(p_course, week_count)
                        record_action('attend_class', 1.25, p_course)
                        # Jump clock to the actual end of the class period
                        time_of_day = max(time_of_day, p_end)
                        current_game_bg = bg_map['attend_class']
                        print(f"Time of day: {format_time(time_of_day)}")
                        if new_msgs:
                            messages.extend(new_msgs)
                            messages = messages[-5:]
                        _check_day_end(messages)
                    elif class_result == "skip":
                        # Small motivation penalty for skipping
                        p_course.occurred_classes += 1   # class happened; player chose not to go
                        student.motivation -= 2
                        student.stats["classes_skipped"] += 1
                        student.clamp()
                        messages.append(f"Skipped {p_course.name}.")
                        messages = messages[-5:]
            new_messages = []

            if alert_box.active:
                alert_box.handle_event(event)

            elif repeat_box.active:
                n = repeat_box.handle_event(event)
                if n is not None:
                    replay_runner = ReplayRunner(student, course_manager, day_actions, n, day_count)
                    messages  = []
                    day_over  = True
                    current_screen_state = DAY_END_SCREEN

            elif input_box.active:
                res = input_box.handle_event(event)
                if res is not None:
                    if pending_action == 'study':
                        hours, target_course = res
                    else:
                        hours, target_course = res, None

                    t_before = time_of_day
                    t_after  = time_of_day + hours
                    overlap  = outage_overlap(daily_outages, t_before, t_after)
                    wifi_affected = (overlap > 0 and pending_action == 'study')
                    if overlap > 0:
                        student.stats["hours_wifi_outage"] += overlap

                    new_messages.extend(student.apply_hunger_decay(hours))
                    if pending_action == 'study':
                        avg_k = course_manager.get_average_knowledge()
                        new_messages.extend(student.study(
                            course=target_course, hours=hours,
                            avg_knowledge=avg_k, wifi_penalty=wifi_affected))
                    elif pending_action == 'sleep':
                        new_messages.extend(student.rest(hours=hours))
                    elif pending_action == 'relax':
                        new_messages.extend(student.take_break(hours=hours))

                    if overlap > 0:
                        dur_min = round(overlap * 60)
                        if pending_action == 'study':
                            alert_box.open(
                                f"WiFi Outage - Day {day_count}",
                                f"WiFi was down for {dur_min} minutes during your study session!\nLearning efficiency dropped and stress increased.",
                                color_type="yellow"
                            )
                        else:
                            new_messages.append(f"Notice: WiFi went down for {dur_min} mins (no effect on {pending_action}).")

                    current_game_bg = bg_map.get(pending_action, bg_map['default'])
                    record_action(pending_action, hours, target_course)
                    time_of_day   += hours
                    pending_action = None
                    print(f"Time of day: {format_time(time_of_day)}")
                    # Mid-day health collapse → fire sickness alert immediately
                    if any("[SICK!]" in m for m in new_messages) and not alert_box.active:
                        current_game_bg = bg_map.get('sick', bg_map['burnout'])
                        alert_box.open(
                            "YOU'VE COLLAPSED!",
                            "Your health hit ZERO mid-session!\n"
                            "Study and classes are BLOCKED.\n"
                            "REST or RELAX to start recovering.",
                            color_type="sickness"
                        )
                    _check_day_end(new_messages)

            elif lab_assessment_interrupt_box.active:
                la_result = lab_assessment_interrupt_box.handle_event(event)
                if la_result is not None:
                    la_course = lab_assessment_interrupt_box._course
                    la_type = lab_assessment_interrupt_box._assessment_type
                    for la in la_course.scheduled_lab_assessments:
                        if la["assessment_type"] == la_type and la["week"] == week_count:
                            if la_result == "skip" or student.is_sick:
                                la["missed"] = True
                                messages.append(f"[LAB] {la_course.name} — {la_type.replace('_', ' ').title()} SKIPPED.")
                                lab_assessment_result_box.open(la_course, missed=True, assessment_type=la_type.replace('_', ' ').title(), mark=0)
                            else:
                                la["missed"] = False
                                if la_type == 'lab_mid':
                                    mark = la_course.generate_lab_mid(week_count, student.stress, student.health)
                                else:
                                    mark = la_course.generate_lab_final(week_count, student.stress, student.health)
                                la["mark"] = mark
                                messages.append(f"[LAB] {la_course.name} — {la_type.replace('_', ' ').title()} taken. (Score: {mark:.1f})")
                                lab_assessment_result_box.open(la_course, missed=False, assessment_type=la_type.replace('_', ' ').title(), mark=mark)
                            break
                    messages = messages[-5:]

            elif not class_interrupt_box.active and not lab_assessment_interrupt_box.active:
                # Open the input prompt for actions that need hours
                remaining_hours = DAY_END - time_of_day

                if study_btn.clicked(event):
                    pending_action = 'study'
                    cap = min(student.max_hours('study'), remaining_hours)
                    # Pass all courses for selection
                    input_box.open('study', cap, courses=course_manager.courses)

                if sleep_btn.clicked(event):
                    pending_action = 'sleep'
                    cap = min(student.max_hours('sleep'), remaining_hours)
                    input_box.open('sleep', cap)

                if relax_btn.clicked(event):
                    pending_action = 'relax'
                    cap = min(student.max_hours('relax'), remaining_hours)
                    input_box.open('relax', cap)

                # Instant actions (fixed durations)
                if drink_coffee_btn.clicked(event):
                    new_messages.extend(student.apply_hunger_decay(0.25))
                    new_messages.extend(student.drink_coffee())
                    current_game_bg = bg_map['coffee']
                    record_action('coffee', 0.25)
                    time_of_day += 0.25  # 15 minutes
                    print(f"Time of day: {format_time(time_of_day)}")
                    _check_day_end(new_messages)

                if eat_btn.clicked(event):
                    new_messages.extend(student.apply_hunger_decay(0.5))
                    new_messages.extend(student.eat())
                    current_game_bg = bg_map['eat']
                    record_action('eat', 0.5)
                    time_of_day += 0.5  # 30 minutes
                    print(f"Time of day: {format_time(time_of_day)}")
                    _check_day_end(new_messages)

                if stats_btn.clicked(event):
                    academic_dashboard.expanded = not academic_dashboard.expanded

            if new_messages:
                messages.extend(new_messages)
                messages = messages[-5:]

            # Quiz interrupt trigger (GAME_SCREEN, weekdays only)
            if (current_screen_state == GAME_SCREEN
                    and not day_over
                    and not class_interrupt_box.active   # don't stack interrupts
                    and not quiz_result_box.active
                    and not alert_box.active
                    and not input_box.active
                    and day_in_week <= 5):               # no quizzes on weekends

                for course in course_manager.courses:
                    if course.course_type != "Theory":
                        continue
                    for quiz in course.scheduled_quizzes:
                        if quiz["taken"]:
                            continue

                        key = (course.name, quiz["quiz_number"])
                        if key in _quizzes_resolved_today:
                            continue

                        # Does this quiz match today?
                        if quiz["week"] != week_count:
                            continue
                        if quiz["day_idx"] != (day_in_week - 1):   # day_idx is 0-based
                            continue

                        # Has the clock reached the quiz slot?
                        from environment import SLOT_TIMES
                        start_h, end_h = SLOT_TIMES[quiz["slot_idx"]]

                        if time_of_day < start_h:
                            continue    # slot hasn't started yet

                        # Quiz fires
                        _quizzes_resolved_today.add(key)
                        quiz["taken"] = True

                        if student.is_sick:
                            quiz["missed"] = True
                            # mark stays None — result system will handle this in Phase 2
                            messages.append(f"[QUIZ] {course.name} — Quiz {quiz['quiz_number']} MISSED (sick).")
                        else:
                            mark = course.generate_quiz_mark(week_count, student.stress, student.sleep, student.health)
                            quiz["mark"] = mark
                            messages.append(f"[QUIZ] {course.name} — Quiz {quiz['quiz_number']} taken. (Score: {mark:.1f})")

                        messages = messages[-5:]   # keep message list tidy
                        break   # only one quiz popup at a time

            # Lab assessment interrupt trigger (GAME_SCREEN, weekdays only)
            if (current_screen_state == GAME_SCREEN
                    and not day_over
                    and not class_interrupt_box.active
                    and not quiz_result_box.active
                    and not lab_assessment_interrupt_box.active
                    and not alert_box.active
                    and not input_box.active
                    and day_in_week <= 5):

                for course in course_manager.courses:
                    if course.course_type != "Lab":
                        continue
                    for la in course.scheduled_lab_assessments:
                        if la["taken"]:
                            continue

                        key = (course.name, la["assessment_type"])
                        if key in _lab_assessments_resolved_today:
                            continue

                        if la["week"] != week_count:
                            continue
                        if la["day_idx"] != (day_in_week - 1):
                            continue

                        from environment import SLOT_TIMES
                        start_h, end_h = SLOT_TIMES[la["slot_idx"]]

                        if time_of_day < start_h:
                            continue    # slot hasn't started yet

                        # Assessment fires
                        _lab_assessments_resolved_today.add(key)
                        la["taken"] = True

                        if student.is_sick:
                            la["missed"] = True
                            messages.append(
                                f"[LAB] {course.name} — "
                                f"{la['assessment_type'].replace('_', ' ').title()} MISSED (sick).")
                        else:
                            lab_assessment_interrupt_box.open(course, la["assessment_type"])

                        messages = messages[-5:]
                        break

        # Day-End Screen
        elif current_screen_state == DAY_END_SCREEN:
            # Lab assessment interrupt (replay) — highest priority alongside quiz
            if lab_assessment_interrupt_box.active:
                choice = lab_assessment_interrupt_box.handle_event(event)
                if choice is not None:
                    runner = replay_runner if (replay_runner and replay_runner.pending_lab_assessment) else (
                             week_replay_runner if (week_replay_runner and week_replay_runner.pending_lab_assessment) else None)
                    if runner and runner.pending_lab_assessment:
                        la, course = runner.pending_lab_assessment
                        la["taken"] = True
                        if choice == "skip" or runner.student.is_sick:
                            la["missed"] = True
                            atype = la["assessment_type"].replace("_", " ").title()
                            msg = f"[LAB] {course.name} — {atype} SKIPPED."
                        else:
                            la["missed"] = False
                            if la["assessment_type"] == 'lab_mid':
                                mark = course.generate_lab_mid(getattr(runner, 'current_week', ((runner.current_day - 1) // 7) + 1), runner.student.stress, runner.student.health)
                            else:
                                mark = course.generate_lab_final(getattr(runner, 'current_week', ((runner.current_day - 1) // 7) + 1), runner.student.stress, runner.student.health)
                            la["mark"] = mark
                            atype = la["assessment_type"].replace("_", " ").title()
                            msg = f"[LAB] {course.name} — {atype} taken. (Score: {mark:.1f})"
                        runner.msgs.append(msg)
                        messages = runner.last_msgs()
                        runner.pending_lab_assessment = None

            # Quiz interrupt (replay) — highest priority
            elif quiz_interrupt_box.active:
                choice = quiz_interrupt_box.handle_event(event)
                if choice is not None:
                    # Resolve for whichever runner owns the pending quiz
                    runner = replay_runner if (replay_runner and replay_runner.pending_quiz) else (
                             week_replay_runner if (week_replay_runner and week_replay_runner.pending_quiz) else None)
                    if runner and runner.pending_quiz:
                        quiz, course = runner.pending_quiz
                        quiz["taken"] = True
                        if choice == "skip" or runner.student.is_sick:
                            quiz["missed"] = True
                            msg = f"[QUIZ] {course.name} — Quiz {quiz['quiz_number']} SKIPPED."
                        else:
                            quiz["missed"] = False
                            mark = course.generate_quiz_mark(getattr(runner, 'current_week', ((runner.current_day - 1) // 7) + 1), runner.student.stress, runner.student.sleep, runner.student.health)
                            quiz["mark"] = mark
                            msg = f"[QUIZ] {course.name} — Quiz {quiz['quiz_number']} taken. (Score: {mark:.1f})"
                        runner.msgs.append(msg)
                        messages = runner.last_msgs()
                        runner.pending_quiz = None

            # AlertBox intercepts all input while active during replay 
            elif alert_box.active:
                dismissed = alert_box.handle_event(event)
                # After dismissal, tick the active runner to continue
                if dismissed:
                    if replay_runner and not replay_runner.done:
                        step_msgs, alert_info = replay_runner.tick()
                        if alert_info:
                            alert_box.open(*alert_info)
                        messages   = replay_runner.last_msgs()
                        day_count  = replay_runner.current_day
                        time_of_day = replay_runner.time_cursor
                        if replay_runner.done and replay_runner.burnout_occurred:
                            burnout_active = True
                    elif week_replay_runner and not week_replay_runner.done:
                        step_msgs, alert_info = week_replay_runner.tick()
                        if alert_info:
                            alert_box.open(*alert_info)
                        messages    = week_replay_runner.last_msgs()
                        day_count   = week_replay_runner.current_day
                        week_count  = week_replay_runner.current_week
                        day_in_week = week_replay_runner.current_day_in_week
                        time_of_day = week_replay_runner.time_cursor
                        if week_replay_runner.done and week_replay_runner.burnout_occurred:
                            burnout_active = True

            elif quiz_week_prompt_box.active:
                choice = quiz_week_prompt_box.handle_event(event)
                if choice == "manual":
                    # Stop the repeat runner and let the player play this week themselves
                    week_replay_runner.quiz_week_pending = False
                    week_replay_runner = None
                    day_count += 1
                    time_of_day = DAY_START
                    day_over = False
                    day_actions.clear()
                    week_actions.clear()
                    current_game_bg = bg_map['default']
                    daily_outages = wifi_failure_event()
                    todays_classes.clear()
                    _classes_resolved.clear()
                    _quizzes_resolved_today.clear()
                    class_interrupt_box.attend_all = False
                    new_diy = ((day_count - 1) % 7) + 1
                    new_wk  = ((day_count - 1) // 7) + 1
                    messages = [f"Week {new_wk} begins — playing manually!"]
                    print(f"\n--- Week {new_wk} - {day_name(new_diy)} (Day {day_count}) [Manual] ---")
                    current_screen_state = GAME_SCREEN
                elif choice == "repeat":
                    # Resume the runner for this quiz week
                    week_replay_runner.quiz_week_pending = False
                    week_replay_runner._start_new_day()
                    messages = [f"Week {week_replay_runner.current_week} replay continues..."]

            elif week_repeat_box.active:
                n = week_repeat_box.handle_event(event)
                if n is not None:
                    # Full week = previous days + today (the 7th day)
                    full_week = list(week_actions) + [list(day_actions)]
                    while len(full_week) < 7:
                        full_week.append([])
                    
                    week_replay_runner = WeekReplayRunner(
                        student, course_manager,
                        full_week, n,
                        day_count, week_count
                    )
                    assessments = week_replay_runner.get_next_week_assessments()
                    if assessments:
                        week_replay_runner.quiz_week_pending = True
                        week_replay_runner.msgs.append(f"Week {week_replay_runner.current_week} begins but has assessments scheduled.")
                        quiz_week_prompt_box.open(week_replay_runner.current_week, assessments)
                    else:
                        week_replay_runner._start_new_day()
                        week_replay_runner.msgs.append(f"Week {week_replay_runner.current_week} begins (fast-forward).")
                    messages = []

            elif repeat_box.active:
                n = repeat_box.handle_event(event)
                if n is not None:
                    # Rewind quizzes for the exact day being repeated
                    course_manager.reset_quizzes_for_day(day_count)
                    replay_runner = ReplayRunner(student, course_manager, day_actions, n, day_count)
                    messages = []

            else:
                if stats_btn.clicked(event):
                    academic_dashboard.expanded = not academic_dashboard.expanded

                if continue_btn.clicked(event):
                    replay_runner = None
                    week_replay_runner = None
                    # Save or reset week_actions based on current day
                    if day_in_week == 7:      # completed last day of the week
                        week_actions.clear()  # fresh start for next week
                    else:
                        week_actions.append(list(day_actions))  # save for week replay
                    day_count += 1
                    # day_in_week / week_count re-derived next frame from new day_count
                    time_of_day = DAY_START
                    day_over = False
                    day_actions.clear()
                    current_game_bg = bg_map['default']
                    daily_outages = wifi_failure_event()
                    new_diy = ((day_count - 1) % 7) + 1
                    new_wk  = ((day_count - 1) // 7) + 1
                    messages = [f"Week {new_wk} - {day_name(new_diy)} begins!"]
                    print(f"\n--- Week {new_wk} - {day_name(new_diy)} (Day {day_count}) ---")
                    print(f"Time of day: {format_time(time_of_day)}")
                    # Reset class interrupt state for the new day
                    todays_classes.clear()
                    _classes_resolved.clear()
                    _quizzes_resolved_today.clear()
                    _lab_assessments_resolved_today.clear()
                    class_interrupt_box.attend_all = False
                    # --- Semester milestone check (boundary-crossing) ---
                    if week_count < 8 and new_wk >= 8:    # crossed into post-mid → mid exam
                        exam_type = "mid"
                        current_screen_state = EXAM_SCREEN
                    elif week_count < 16 and new_wk >= 16:  # crossed out of week 15 → final exam
                        exam_type = "final"
                        current_screen_state = EXAM_SCREEN
                    else:
                        current_screen_state = GAME_SCREEN

                if repeat_btn.clicked(event):
                    if day_actions:
                        # Cap repeats based on week/day-of-week to enforce game flow
                        SEMESTER_LAST_DAY = 7 * 15  # day 105 = end of week 15
                        # Unified capping logic for all weeks:
                        # Weekdays (1-5) can repeat up to Friday; Saturday (6) can repeat into Sunday; Sunday (7) zero.
                        if day_in_week <= 5:
                            max_rep = 5 - day_in_week
                        elif day_in_week == 6:
                            max_rep = 1
                        else:
                            max_rep = 0
                        if max_rep > 0:
                            repeat_box.open("Repeat for how many more days?", max_value=max_rep)
                        else:
                            messages = ["No repeats available for this day."]
                    else:
                        messages = ["No actions recorded to repeat."]

                if repeat_week_btn.clicked(event) and day_in_week == 7:
                    if week_actions or day_actions:
                        # Build full 7-day snapshot (previous 6 days + today)
                        _full_week_snapshot = list(week_actions) + [list(day_actions)]
                        max_wk = _max_week_repeats(week_count)
                        if max_wk > 0:
                            week_repeat_box.open(
                                "Repeat this week for how many more weeks?",
                                max_value=max_wk
                            )
                        else:
                            messages = ["No more weeks available — exam time!"]
                    else:
                        messages = ["No actions recorded this week."]

                if quit_btn.clicked(event):
                    current_screen_state = SAVE_PROMPT

        # Exam Screen
        elif current_screen_state == EXAM_SCREEN:
            if exam_continue_btn.clicked(event):
                if exam_type == "final":
                    # Apply 85% attendance rule: barred students get 0 on finals
                    for c in course_manager.courses:
                        if c.course_type == "Theory":
                            if not c.is_attendance_eligible():
                                c.final_mark = 0
                            else:
                                c.generate_final_mark(week_count, student.stress, student.sleep, student.health, student.is_sick)
                        elif c.course_type == "Lab":
                            if not c.is_attendance_eligible():
                                c.lab_final = 0
                            else:
                                c.generate_lab_final(week_count, student.stress, student.health, student.is_sick)
                    _results_scroll_y = 0.0
                    _sem_end_page = 0
                    current_screen_state = SEMESTER_END_SCREEN
                else:
                    # Mid exam done → generate mid marks then show midterm results
                    for c in course_manager.courses:
                        if c.course_type == "Theory":
                            c.generate_mid_mark(week_count, student.stress, student.sleep, student.health, student.is_sick)
                        elif c.course_type == "Lab":
                            c.generate_lab_mid(week_count, student.stress, student.health, student.is_sick)
                    _results_scroll_y = 0.0
                    current_screen_state = MIDTERM_RESULTS_SCREEN

        # Midterm Results Screen
        elif current_screen_state == MIDTERM_RESULTS_SCREEN:
            if exam_continue_btn.clicked(event):
                # Return to game for the post-midterm half
                day_over = False
                current_game_bg = bg_map['default']
                daily_outages = wifi_failure_event()
                todays_classes.clear()
                _classes_resolved.clear()
                _quizzes_resolved_today.clear()
                _lab_assessments_resolved_today.clear()
                class_interrupt_box.attend_all = False
                current_screen_state = GAME_SCREEN

        # Semester End Screen
        elif current_screen_state == SEMESTER_END_SCREEN:
            if _sem_end_page == 0:
                if sem_next_btn.clicked(event):
                    _sem_end_page = 1
                    _results_scroll_y = 0.0
                    sem_next_btn.text = "Optimal >"
                    sem_prev_btn.text = "< Results"
            elif _sem_end_page == 1:
                if sem_next_btn.clicked(event):
                    _sem_end_page = 2
                    _results_scroll_y = 0.0
                    sem_prev_btn.text = "< Stats"
                    # Calculate optimal data once when navigating to the screen
                    if _optimal_data is None:
                        from screens import compute_optimal_path
                        _optimal_data = compute_optimal_path(student, course_manager)
                if sem_prev_btn.clicked(event):
                    _sem_end_page = 0
                    _results_scroll_y = 0.0
                    sem_next_btn.text = "Stats >"
            elif _sem_end_page == 2:
                if sem_prev_btn.clicked(event):
                    _sem_end_page = 1
                    _results_scroll_y = 0.0
                    sem_next_btn.text = "Optimal >"
                    sem_prev_btn.text = "< Results"
                    
            if sem_quit_btn.clicked(event):
                running = False

    # Active replay tick (day runner)
    if (current_screen_state == DAY_END_SCREEN
            and replay_runner is not None
            and not replay_runner.done
            and not alert_box.active
            and not repeat_box.active
            and not week_repeat_box.active
            and not quiz_interrupt_box.active
            and not lab_assessment_interrupt_box.active):
        # Open interrupt box if runner is sitting on a pending quiz
        if replay_runner.pending_quiz:
            quiz, course = replay_runner.pending_quiz
            quiz_interrupt_box.open(course, quiz["quiz_number"])
        # Open lab interrupt box if runner is sitting on a pending lab assessment
        elif replay_runner.pending_lab_assessment:
            la, course = replay_runner.pending_lab_assessment
            lab_assessment_interrupt_box.open(course, la["assessment_type"])
        else:
            prev_day = replay_runner.current_day
            step_msgs, alert_info = replay_runner.tick()
            if alert_info:
                alert_box.open(*alert_info)
            messages = replay_runner.last_msgs()
            day_count = replay_runner.current_day
            time_of_day = replay_runner.time_cursor
            if replay_runner.current_action:
                current_game_bg = bg_map.get(replay_runner.current_action, bg_map['default'])
            if replay_runner.done and replay_runner.burnout_occurred:
                burnout_active = True
            # Sync sick_active from student truth
            sick_active = student.is_sick
            # Sync week_actions so weeks completed by replay are tracked
            if day_count != prev_day:
                new_diy = ((day_count - 1) % 7) + 1
                if new_diy == 1:
                    week_actions.clear()  # week boundary crossed
                else:
                    # Fill in any replayed days within this week
                    while len(week_actions) < new_diy - 1:
                        week_actions.append(list(day_actions))

    # Resolve quiz_interrupt_box choice for day runner
    if (not quiz_interrupt_box.active
            and replay_runner is not None
            and replay_runner.pending_quiz):
        quiz, course = replay_runner.pending_quiz
        # quiz_interrupt_box just closed — determine last result
        # We detect close by checking active went False (handled in event loop below)
        pass  # resolution handled in event section

    # Active replay tick (week runner)
    if (current_screen_state == DAY_END_SCREEN
            and week_replay_runner is not None
            and not week_replay_runner.done
            and not week_replay_runner.quiz_week_pending
            and not alert_box.active
            and not repeat_box.active
            and not week_repeat_box.active
            and not quiz_interrupt_box.active
            and not lab_assessment_interrupt_box.active):
        # Open interrupt box if runner is sitting on a pending quiz
        if week_replay_runner.pending_quiz:
            quiz, course = week_replay_runner.pending_quiz
            quiz_interrupt_box.open(course, quiz["quiz_number"])
        # Open lab interrupt box if runner is sitting on a pending lab assessment
        elif week_replay_runner.pending_lab_assessment:
            la, course = week_replay_runner.pending_lab_assessment
            lab_assessment_interrupt_box.open(course, la["assessment_type"])
        else:
            step_msgs, alert_info = week_replay_runner.tick()
            if alert_info:
                alert_box.open(*alert_info)
            messages = week_replay_runner.last_msgs()
            day_count = week_replay_runner.current_day
            week_count = week_replay_runner.current_week
            day_in_week = week_replay_runner.current_day_in_week
            time_of_day = week_replay_runner.time_cursor
            if week_replay_runner.current_action:
                current_game_bg = bg_map.get(week_replay_runner.current_action, bg_map['default'])
            if week_replay_runner.done and week_replay_runner.burnout_occurred:
                burnout_active = True
                current_game_bg = bg_map['burnout']
            # Sync sick_active from student truth
            sick_active = student.is_sick
            # If the runner just paused for a quiz-week prompt, open the dialog
            if (week_replay_runner.quiz_week_pending
                    and not quiz_week_prompt_box.active):
                assessments = week_replay_runner.get_next_week_assessments()
                quiz_week_prompt_box.open(week_replay_runner.current_week, assessments)
            # Check for exam milestone after week replay finishes
            if week_replay_runner.done and not week_replay_runner.burnout_occurred:
                # current_week is the last week the runner was in (7 or 15)
                if week_count == 7 and day_in_week == 7:
                    exam_type = "mid"
                    current_screen_state = EXAM_SCREEN
                elif week_count == 15 and day_in_week == 7:
                    exam_type = "final"
                    current_screen_state = EXAM_SCREEN

    # Class interrupt trigger (GAME_SCREEN, weekdays only)
    if (current_screen_state == GAME_SCREEN
            and not day_over
            and not class_interrupt_box.active
            and not alert_box.active
            and not input_box.active
            and not repeat_box.active):

        _trigger_diw = ((day_count - 1) % 7) + 1
        _trigger_week = ((day_count - 1) // 7) + 1

        # Repopulate the class list whenever the day has changed
        if day_count != _classes_populated_for_day:
            todays_classes.clear()
            _classes_populated_for_day = day_count
            todays_classes.extend(
                get_todays_classes(course_manager.courses, _trigger_diw, _trigger_week)
            )

        # Check for classes that are due or have passed
        for (start_h, end_h, cls_course) in todays_classes:
            if start_h in _classes_resolved:
                continue

            if time_of_day > end_h:
                # Class window is completely over — silently mark as missed
                _classes_resolved.add(start_h)
                cls_course.occurred_classes += 1   # it occurred; player wasn't there
                continue

            if time_of_day >= start_h:
                # Class is currently in session — prompt or auto-attend
                if class_interrupt_box.attend_all:
                    _classes_resolved.add(start_h)
                    new_msgs = student.attend_class(cls_course, week_count)
                    record_action('attend_class', 1.25, cls_course)
                    # Jump clock to the actual end of the class period
                    time_of_day = max(time_of_day, end_h)
                    current_game_bg = bg_map['attend_class']
                    print(f"Auto-attended {cls_course.name}. Time: {format_time(time_of_day)}")
                    if new_msgs:
                        messages.extend(new_msgs)
                        messages = messages[-5:]
                    _check_day_end(messages)
                else:
                    # Show the interrupt prompt
                    _pending_class = (start_h, end_h, cls_course)
                    att_pct = cls_course.get_attendance_percentage()
                    class_interrupt_box.open(cls_course, start_h, end_h, att_pct)
                break   # only one interrupt at a time

    # Track the last real screen (not the prompt) for backdrop rendering
    if current_screen_state != SAVE_PROMPT:
        _last_game_screen = current_screen_state

    # Draw
    screen.fill((30, 30, 30))

    if current_screen_state == SAVE_PROMPT:
        # Draw the backdrop of whatever screen the player was on
        if _last_game_screen == MAIN_MENU:
            main_menu(screen, main_bg, start_btn,
                      continue_button=continue_menu_btn if save_exists() else None)
        elif _last_game_screen == GAME_SCREEN:
            avg_k = course_manager.get_average_knowledge()
            game_screen(screen, current_game_bg, student, bars, game_buttons,
                        messages, message_font, bar_space)
            bars[0].draw(screen, avg_k)
            draw_clock(screen, clock_font, date_font, time_of_day, day_count, bar_space,
                       week_count=week_count, day_in_week=day_in_week)
            academic_dashboard.draw(screen, course_manager, week_count)
        elif _last_game_screen == DAY_END_SCREEN:
            avg_k = course_manager.get_average_knowledge()
            day_end_screen(
                screen, current_game_bg, student, bars, game_buttons,
                messages, message_font, bar_space,
                draw_clock, clock_font, date_font,
                time_of_day, day_count,
                avg_k, burnout_active,
                continue_btn, repeat_btn, quit_btn,
                repeat_box, alert_box,
                week_count=week_count, day_in_week=day_in_week,
                repeat_week_btn=repeat_week_btn,
                week_repeat_box=week_repeat_box,
                sick_active=sick_active,
            )
            academic_dashboard.draw(screen, course_manager, week_count)
        save_prompt_screen(screen, save_yes_btn, save_no_btn, message_font)

    elif current_screen_state == MAIN_MENU:
        main_menu(screen, main_bg, start_btn,
                  continue_button=continue_menu_btn if save_exists() else None)

    elif current_screen_state == SETUP_SCREEN:
        wizard.draw(screen)

    elif current_screen_state == GAME_SCREEN:
        avg_k = course_manager.get_average_knowledge()
        game_screen(screen, current_game_bg, student, bars, game_buttons, messages, message_font, bar_space)
        # Manually draw bars[0] (Knowledge) with the calculated average
        bars[0].draw(screen, avg_k)
        
        draw_clock(screen, clock_font, date_font, time_of_day, day_count, bar_space,
                   week_count=week_count, day_in_week=day_in_week)

        input_box.draw(screen)
        repeat_box.draw(screen)
        alert_box.draw(screen)
        class_interrupt_box.draw(screen)

        # Draw academic dashboard (behind quiz popup)
        academic_dashboard.draw(screen, course_manager, week_count)

        # Draw quiz result popup (topmost)
        quiz_result_box.draw(screen)
        lab_assessment_interrupt_box.draw(screen)
        lab_assessment_result_box.draw(screen)

    elif current_screen_state == DAY_END_SCREEN:
        avg_k = course_manager.get_average_knowledge()
        day_end_screen(
            screen, current_game_bg, student, bars, game_buttons,
            messages, message_font, bar_space,
            draw_clock, clock_font, date_font,
            time_of_day, day_count,
            avg_k, burnout_active,
            continue_btn, repeat_btn, quit_btn,
            repeat_box, alert_box,
            week_count=week_count, day_in_week=day_in_week,
            repeat_week_btn=repeat_week_btn,
            week_repeat_box=week_repeat_box,
            sick_active=sick_active,
        )
        stats_btn.draw(screen)
        academic_dashboard.draw(screen, course_manager, week_count)
        quiz_week_prompt_box.draw(screen)
        quiz_interrupt_box.draw(screen)   # replay quiz Take/Skip prompt
        lab_assessment_interrupt_box.draw(screen)  # replay lab Take/Skip prompt

    elif current_screen_state == EXAM_SCREEN:
        exam_screen(screen, exam_type, exam_continue_btn, message_font,
                    course_manager=course_manager)

    elif current_screen_state == MIDTERM_RESULTS_SCREEN:
        avg_k = course_manager.get_average_knowledge()
        _results_content_h = midterm_results_screen(
            screen, course_manager, exam_continue_btn,
            scroll_y=_results_scroll_y)

    elif current_screen_state == SEMESTER_END_SCREEN:
        avg_k = course_manager.get_average_knowledge()
        if _sem_end_page == 0:
            _results_content_h = semester_end_screen(
                screen, student, avg_k, sem_quit_btn, message_font,
                course_manager, scroll_y=_results_scroll_y,
                next_btn=sem_next_btn)
        elif _sem_end_page == 1:
            _results_content_h = semester_stats_screen(
                screen, student, course_manager,
                sem_prev_btn, sem_quit_btn,
                scroll_y=_results_scroll_y,
                next_btn=sem_next_btn)
        elif _sem_end_page == 2:
            from screens import semester_optimal_screen
            _results_content_h = semester_optimal_screen(
                screen, _optimal_data, sem_prev_btn, sem_quit_btn, scroll_y=_results_scroll_y)

    pygame.display.flip()

pygame.quit()
sys.exit()
