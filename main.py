import pygame
import sys

from student import Student
from courses import CourseManager
from events import wifi_failure_event
from environment import DAY_START, DAY_END, format_time, draw_clock, outage_overlap
from ui import StatusBar, Button, InputBox, NumberBox, AlertBox, SetupWizard
from screens import main_menu, game_screen, day_end_screen

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

print(f"Time of day: {format_time(time_of_day)}")

student        = Student()
course_manager = CourseManager()

day_actions  = []
daily_outages = wifi_failure_event()


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
            day_msgs = self.student.end_of_day()
            self.msgs.extend(day_msgs)
            self.msgs.append(f"Day {self.current_day} completed (fast-forward).")
            if any("Burnout!" in m for m in day_msgs):
                self.burnout_occurred = True
                self.msgs.append("Loop paused. You need to recover!")
                self.done = True
                return day_msgs + [f"Day {self.current_day} completed (fast-forward)."], None
            if self.days_done >= self.total_days:
                self.done = True
                return day_msgs + [f"Day {self.current_day} completed (fast-forward)."], None
            # Start next day
            self._start_new_day()
            return day_msgs + [f"Day {self.current_day - 1} completed (fast-forward)."], None

        action, hours, data = self.actions[self.action_idx]
        action_start = self.time_cursor
        action_end   = self.time_cursor + hours

        # Fire an outage interrupt before this action if one overlaps
        if self._outage_idx < len(self._day_outages):
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

        # Run the action
        new_msgs = []
        overlap  = outage_overlap(self._day_outages, action_start, action_end)
        wifi_on  = (overlap > 0 and action == 'study')

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

        self.time_cursor    = action_end
        self.action_idx    += 1
        self.current_action = action
        self.msgs.extend(new_msgs)

        pygame.time.wait(300)   # slight pause so replay is watchable
        return new_msgs, None

    def last_msgs(self, n=5):
        return self.msgs[-n:]


# Game states
MAIN_MENU = "main_menu"
SETUP_SCREEN = "setup_screen"
GAME_SCREEN = "game_screen"
DAY_END_SCREEN = "day_end_screen"
current_screen_state = MAIN_MENU

# Assets
main_bg = pygame.image.load("assets/images/main.jpg")
bg_map  = {
    'study':   pygame.image.load("assets/images/study.jpg"),
    'sleep':   pygame.image.load("assets/images/sleep.jpg"),
    'relax':   pygame.image.load("assets/images/break.jpg"),
    'coffee':  pygame.image.load("assets/images/coffee.jpg"),
    'eat':     pygame.image.load("assets/images/eat.jpg"),
    'default': pygame.image.load("assets/images/study.jpg"),
}
current_game_bg = bg_map['default']

# Fonts
button_font  = pygame.font.Font("assets/fonts/Papernotes.otf", 22)
message_font = pygame.font.Font("assets/fonts/Papernotes.otf", 20)
input_font   = pygame.font.Font("assets/fonts/Papernotes.otf", 16)
clock_font   = pygame.font.Font("assets/fonts/Digital-7.ttf",  50)
date_font    = pygame.font.Font("assets/fonts/Digital-7.ttf",  35)
alert_title_font = pygame.font.Font("assets/fonts/Papernotes.otf", 28)
alert_body_font  = pygame.font.Font("assets/fonts/Papernotes.otf", 22)

# UI Widgets
input_box  = InputBox(message_font, input_font)
repeat_box = NumberBox(message_font, input_font)
alert_box  = AlertBox(alert_title_font, alert_body_font)
wizard     = SetupWizard(message_font, input_font, button_font)

pending_action: str | None = None

# Status bars
bar_w     = 130
bar_h     = 16
bar_space = (WIDTH - 6 * bar_w) / 7
bars = [
    StatusBar(bar_space,              60, bar_w, bar_h, "Knowledge",  message_font),
    StatusBar(bar_space*2 + bar_w,    60, bar_w, bar_h, "Sleep",      message_font),
    StatusBar(bar_space*3 + bar_w*2,  60, bar_w, bar_h, "Health",     message_font),
    StatusBar(bar_space*4 + bar_w*3,  60, bar_w, bar_h, "Stress",     message_font),
    StatusBar(bar_space*5 + bar_w*4,  60, bar_w, bar_h, "Motivation", message_font),
    StatusBar(bar_space*6 + bar_w*5,  60, bar_w, bar_h, "Hunger",     message_font),
]

# Action buttons
start_btn = Button(WIDTH - 160, HEIGHT - 80, 120, 40, "Start", button_font, 'black')

btn_w     = 140
btn_h     = 40
btn_space = (WIDTH - 5 * btn_w) / 6
study_btn       = Button(btn_space,              HEIGHT - 80, btn_w, btn_h, "Study",  button_font)
sleep_btn       = Button(btn_space*2 + btn_w,    HEIGHT - 80, btn_w, btn_h, "Sleep",  button_font)
relax_btn       = Button(btn_space*3 + btn_w*2,  HEIGHT - 80, btn_w, btn_h, "Relax",  button_font)
drink_coffee_btn= Button(btn_space*4 + btn_w*3,  HEIGHT - 80, btn_w, btn_h, "Coffee", button_font)
eat_btn         = Button(btn_space*5 + btn_w*4,  HEIGHT - 80, btn_w, btn_h, "Food",   button_font)
game_buttons = [study_btn, sleep_btn, relax_btn, drink_coffee_btn, eat_btn]

# Day-end buttons
_btn_y      = HEIGHT // 2 + 40
continue_btn = Button(WIDTH // 2 - 196, _btn_y, 114, 40, "Continue", button_font)
repeat_btn   = Button(WIDTH // 2 -  57, _btn_y, 114, 40, "Repeat",   button_font)
quit_btn     = Button(WIDTH // 2 +  82, _btn_y, 114, 40, "Quit",     button_font)

messages: list[str]              = []
replay_runner: ReplayRunner | None = None


# ── Helper: handle day-end trigger ───────────────────────────────────
def _check_day_end(new_msgs: list[str]) -> list[str]:
    """Call end_of_day if the day clock has run out; return extra messages."""
    global day_over, burnout_active, current_screen_state
    if round(time_of_day * 60) >= round(DAY_END * 60):
        eod_msgs = student.end_of_day()
        new_msgs.extend(eod_msgs)
        new_msgs.append(f"Day {day_count} is over!")
        print(f"Day {day_count} ended.")
        if any("Burnout!" in m for m in eod_msgs):
            burnout_active = True
        if any("recovered from burnout" in m for m in eod_msgs):
            burnout_active = False
        day_over = True
        current_screen_state = DAY_END_SCREEN
    return new_msgs


# Main loop
running = True
while running:
    remaining_hours = DAY_END - time_of_day

    # -- Button enable state --
    if day_over or remaining_hours <= 0:
        for btn in game_buttons:
            btn.enabled = False
    else:
        study_btn.enabled        = student.action_status['study']  and remaining_hours > 0
        sleep_btn.enabled        = student.action_status['sleep']  and remaining_hours > 0
        relax_btn.enabled        = student.action_status['relax']  and remaining_hours > 0
        eat_btn.enabled          = student.action_status['eat']    and remaining_hours >= 0.5
        drink_coffee_btn.enabled = student.action_status['coffee'] and remaining_hours >= 0.25

    repeat_btn.enabled = not burnout_active

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Main Menu
        if current_screen_state == MAIN_MENU:
            if start_btn.clicked(event):
                wizard.reset()
                current_screen_state = SETUP_SCREEN

        # Setup Screen
        elif current_screen_state == SETUP_SCREEN:
            wizard.handle_event(event)
            if wizard.done:
                student = Student(student_type=wizard.result["student_type"])
                course_manager.setup_from_wizard(wizard.result)
                current_screen_state = GAME_SCREEN

        # Game Screen
        elif current_screen_state == GAME_SCREEN:
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
                        alert_box.open(
                            f"WiFi Outage - Day {day_count}",
                            f"WiFi was down for {dur_min} minutes during your {pending_action} session!",
                            color_type="yellow"
                        )

                    current_game_bg = bg_map.get(pending_action, bg_map['default'])
                    record_action(pending_action, hours, target_course)
                    time_of_day   += hours
                    pending_action = None
                    print(f"Time of day: {format_time(time_of_day)}")
                    _check_day_end(new_messages)

            else:
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

            if new_messages:
                messages.extend(new_messages)
                messages = messages[-5:]

        # Day-End Screen
        elif current_screen_state == DAY_END_SCREEN:
            # AlertBox intercepts all input while active during replay 
            if alert_box.active:
                dismissed = alert_box.handle_event(event)
                # After dismissal, tick the runner once more to continue
                if dismissed and replay_runner and not replay_runner.done:
                    step_msgs, alert_info = replay_runner.tick()
                    if alert_info:
                        alert_box.open(*alert_info)
                    messages   = replay_runner.last_msgs()
                    day_count  = replay_runner.current_day
                    time_of_day = replay_runner.time_cursor
                    if replay_runner.done and replay_runner.burnout_occurred:
                        burnout_active = True

            elif repeat_box.active:
                n = repeat_box.handle_event(event)
                if n is not None:
                    replay_runner = ReplayRunner(student, course_manager, day_actions, n, day_count)
                    messages = []

            else:
                if continue_btn.clicked(event):
                    replay_runner = None
                    day_count += 1
                    time_of_day = DAY_START
                    day_over = False
                    day_actions.clear()
                    current_game_bg = bg_map['default']
                    daily_outages = wifi_failure_event()  # generate new outages for next live day
                    messages = [f"Day {day_count} begins!"]
                    print(f"\n--- Day {day_count} ---")
                    print(f"Time of day: {format_time(time_of_day)}")
                    current_screen_state = GAME_SCREEN

                if repeat_btn.clicked(event):
                    if day_actions:
                        repeat_box.open("Repeat for how many more days?", max_value=30)
                    else:
                        messages = ["No actions recorded to repeat."]

                if quit_btn.clicked(event):
                    running = False

    if (current_screen_state == DAY_END_SCREEN
            and replay_runner is not None
            and not replay_runner.done
            and not alert_box.active
            and not repeat_box.active):
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

    # Draw
    screen.fill((30, 30, 30))

    if current_screen_state == MAIN_MENU:
        main_menu(screen, main_bg, start_btn)

    elif current_screen_state == SETUP_SCREEN:
        wizard.draw(screen)

    elif current_screen_state == GAME_SCREEN:
        avg_k = course_manager.get_average_knowledge()
        game_screen(screen, current_game_bg, student, bars, game_buttons, messages, message_font, bar_space)
        # Manually draw bars[0] (Knowledge) with the calculated average
        bars[0].draw(screen, avg_k)
        
        draw_clock(screen, clock_font, date_font, time_of_day, day_count, bar_space)

        input_box.draw(screen)
        repeat_box.draw(screen)
        alert_box.draw(screen)

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
        )

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
