import pygame
import sys
from student import Student
from courses import CourseManager
from ui import StatusBar, Button, InputBox, NumberBox, AlertBox, SetupWizard
from screens import main_menu, game_screen
from events import wifi_failure_event

pygame.init()

WIDTH, HEIGHT = 1000, 650
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Caffeine & Chaos")

clock = pygame.time.Clock()
time_of_day = 8
DAY_START = 8
DAY_END = 32
day_over = False
day_count = 1
burnout_active = False   # True while student is recovering from burnout

def format_time(hour):
    total_minutes = round(hour * 60)
    h = (total_minutes // 60) % 24
    m = total_minutes % 60
    if h == 0:
        return f"12:{m:02d} AM"
    elif h < 12:
        return f"{h}:{m:02d} AM"
    elif h == 12:
        return f"12:{m:02d} PM"
    else:
        return f"{h - 12}:{m:02d} PM"

print(f"Time of day: {format_time(time_of_day)}")

def draw_clock(screen, clock_font, date_font, time_of_day, day_count, bar_space):
    clock_color = (255, 255, 0)
    time_str = format_time(time_of_day)
    time_surf = clock_font.render(time_str, True, clock_color)
    day_surf = date_font.render(f"Day {day_count}", True, clock_color)
    
    box_w = max(time_surf.get_width(), day_surf.get_width()) + 20
    box_h = time_surf.get_height() + day_surf.get_height() + 5
    box_x = WIDTH - bar_space - box_w
    box_y = 95
    
    clock_bg = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    clock_bg.fill((0, 0, 0, 180))
    screen.blit(clock_bg, (box_x, box_y))
    
    screen.blit(time_surf, (box_x + box_w - time_surf.get_width() - 10, 100))
    screen.blit(day_surf, (box_x + box_w - day_surf.get_width() - 10, 100 + time_surf.get_height() - 10))

student = Student()
course_manager = CourseManager()

day_actions = []
# Outages for the current live day (list of {"start": h, "duration": h})
daily_outages = wifi_failure_event()

def record_action(action: str, hours: float, data=None):
    day_actions.append((action, hours, data))

def outage_overlap(outages, t_start, t_end):
    """Return total hours of outage overlap in [t_start, t_end)."""
    total = 0.0
    for o in outages:
        o_start = o["start"]
        o_end = o["start"] + o["duration"]
        overlap = max(0.0, min(t_end, o_end) - max(t_start, o_start))
        total += overlap
    return total


class ReplayRunner:
    def __init__(self, student, course_manager, actions, n, start_day):
        self.student = student
        self.course_manager = course_manager
        self.actions = list(actions)
        self.total_days = n
        self.current_day = start_day
        self.days_done = 0
        self.action_idx = 0
        self.time_cursor = float(DAY_START)    # simulated time within the replayed day
        self.current_action = None

        # Pending alert: set when an outage fires, cleared after player dismisses
        self.pending_alert = None   # (title, body) tuple or None

        self.msgs = []
        self.done = False
        self.burnout_occurred = False

        # Generate outages for first replayed day
        self._day_outages    = wifi_failure_event()
        self._outage_idx     = 0   # next unprocessed outage in _day_outages

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
        action_end = self.time_cursor + hours

        # Check if any un-processed outage starts before this action ends
        if self._outage_idx < len(self._day_outages):
            outage = self._day_outages[self._outage_idx]
            if outage["start"] < action_end:
                # Fire the outage interrupt BEFORE running the action
                self._outage_idx += 1
                dur_min = round(outage["duration"] * 60)
                at_time = format_time(outage["start"])
                title = f"WiFi Outage!"
                body  = (f"At {at_time} on Day {self.current_day}, wifi went down for {dur_min} minutes.")
                
                # Check for study session interruption
                o_start = outage["start"]
                o_end = o_start + outage["duration"]
                overlap = max(0.0, min(action_end, o_end) - max(action_start, o_start))
                if overlap > 0 and action == 'study':
                    interrupted_min = round(overlap * 60)
                    body += f"\nYour study session was interrupted for {interrupted_min} minutes."

                return [], (title, body, "yellow")

        # Run the action
        new_msgs = []
        overlap  = outage_overlap(self._day_outages, action_start, action_end)
        wifi_on  = (overlap > 0 and action == 'study')

        if action == 'study' and self.student.action_status['study']:
            # Use recorded course data if available, otherwise fallback
            target = data if data else next((c for c in self.course_manager.courses if c.course_type == "Theory"), self.course_manager.courses[0])
            avg = self.course_manager.get_average_knowledge()
            new_msgs.extend(self.student.apply_hunger_decay(hours))
            new_msgs.extend(self.student.study(course=target, hours=hours, avg_knowledge=avg, wifi_penalty=wifi_on))
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

        self.time_cursor = action_end
        self.action_idx += 1
        self.current_action = action
        self.msgs.extend(new_msgs)
        
        # Slow down the fast-forward slightly for better visibility
        pygame.time.wait(300)
        
        return new_msgs, None

    def last_msgs(self, n=5):
        return self.msgs[-n:]


# Game states
MAIN_MENU = "main_menu"
SETUP_SCREEN = "setup_screen"
GAME_SCREEN = "game_screen"
DAY_END_SCREEN = "day_end_screen"
current_screen_state = MAIN_MENU

# Load images
main_bg = pygame.image.load("assets/images/main.jpg")
bg_map = {
    'study': pygame.image.load("assets/images/study.jpg"),
    'sleep': pygame.image.load("assets/images/sleep.jpg"),
    'relax': pygame.image.load("assets/images/break.jpg"),
    'coffee': pygame.image.load("assets/images/coffee.jpg"),
    'eat': pygame.image.load("assets/images/eat.jpg"),
    'default': pygame.image.load("assets/images/study.jpg")
}
current_game_bg = bg_map['default']

button_font = pygame.font.Font("assets/fonts/Papernotes.otf", 22)
message_font = pygame.font.Font("assets/fonts/Papernotes.otf", 20)
input_font = pygame.font.Font("assets/fonts/Papernotes.otf", 16)
input_box = InputBox(message_font, input_font)
repeat_box = NumberBox(message_font, input_font)
alert_title_font = pygame.font.Font("assets/fonts/Papernotes.otf", 28)
alert_body_font = pygame.font.Font("assets/fonts/Papernotes.otf", 22)
alert_box = AlertBox(alert_title_font, alert_body_font)
wizard = SetupWizard(message_font, input_font, button_font)
clock_font = pygame.font.Font("assets/fonts/Digital-7.ttf", 50)
date_font = pygame.font.Font("assets/fonts/Digital-7.ttf", 35)
pending_action = None  

# Status bars
bar_w = 130
bar_h = 16
bar_space = (WIDTH - 6*(bar_w)) / 7
bars = [
    StatusBar(bar_space, 60, bar_w, bar_h, "Knowledge", message_font),
    StatusBar(bar_space*2 + bar_w, 60, bar_w, bar_h, "Sleep", message_font),
    StatusBar(bar_space*3 + bar_w*2, 60, bar_w, bar_h, "Health", message_font),
    StatusBar(bar_space*4 + bar_w*3, 60, bar_w, bar_h, "Stress", message_font),
    StatusBar(bar_space*5 + bar_w*4, 60, bar_w, bar_h, "Motivation", message_font),
    StatusBar(bar_space*6 + bar_w*5, 60, bar_w, bar_h, "Hunger", message_font),
]

# Buttons
start_btn = Button(WIDTH - 160, HEIGHT - 80, 120, 40, "Start", button_font, 'black')
 
btn_w = 140
btn_h = 40
btn_space = (WIDTH - 5*(btn_w)) / 6
study_btn = Button(btn_space, HEIGHT - 80, btn_w, btn_h, "Study", button_font)
sleep_btn = Button(btn_space*2 + btn_w, HEIGHT - 80, btn_w, btn_h, "Sleep", button_font)
relax_btn = Button(btn_space*3 + btn_w*2, HEIGHT - 80, btn_w, btn_h, "Relax", button_font)
drink_coffee_btn = Button(btn_space*4 + btn_w*3, HEIGHT - 80, btn_w, btn_h, "Coffee", button_font)
eat_btn = Button(btn_space*5 + btn_w*4, HEIGHT - 80, btn_w, btn_h, "Food", button_font)

game_buttons = [study_btn, sleep_btn, relax_btn, drink_coffee_btn, eat_btn]

# Day-end buttons
_btn_y = HEIGHT // 2 + 40
continue_btn = Button(WIDTH // 2 - 196, _btn_y, 114, 40, "Continue", button_font)
repeat_btn = Button(WIDTH // 2 -  57, _btn_y, 114, 40, "Repeat", button_font)
quit_btn = Button(WIDTH // 2 + 82,  _btn_y, 114, 40, "Quit", button_font)

messages = []
replay_runner: ReplayRunner | None = None  # active replay state machine

running = True
while running:
    remaining_hours = DAY_END - time_of_day

    # Update button states (disabled when day is over)
    if day_over or remaining_hours <= 0:
        for btn in game_buttons:
            btn.enabled = False
    else:
        study_btn.enabled = student.action_status['study'] and remaining_hours > 0
        sleep_btn.enabled = student.action_status['sleep'] and remaining_hours > 0
        relax_btn.enabled = student.action_status['relax'] and remaining_hours > 0
        eat_btn.enabled = student.action_status['eat'] and remaining_hours >= 0.5
        drink_coffee_btn.enabled = student.action_status['coffee'] and remaining_hours >= 0.25

    # Update day-end button states
    repeat_btn.enabled = not burnout_active

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if current_screen_state == MAIN_MENU:
            if start_btn.clicked(event):
                wizard.reset()
                current_screen_state = SETUP_SCREEN

        elif current_screen_state == SETUP_SCREEN:
            wizard.handle_event(event)
            if wizard.done:
                # Initialize student and courses with wizard results
                student = Student(student_type=wizard.result["student_type"])
                course_manager.setup_from_wizard(wizard.result)
                current_screen_state = GAME_SCREEN

        elif current_screen_state == GAME_SCREEN:
            new_messages = []

            if alert_box.active:
                alert_box.handle_event(event)

            elif repeat_box.active:
                n = repeat_box.handle_event(event)
                if n is not None:
                    replay_runner = ReplayRunner(student, course_manager, day_actions, n, day_count)
                    messages = []
                    day_over = True
                    current_screen_state = DAY_END_SCREEN

            elif input_box.active:
                res = input_box.handle_event(event)
                if res is not None:
                    # Unpack if study (tuple), otherwise it's just a float
                    if pending_action == 'study':
                        hours, target_course = res
                    else:
                        hours = res
                        target_course = None

                    t_before = time_of_day
                    t_after  = time_of_day + hours

                    # Compute wifi overlap for this action window
                    overlap = outage_overlap(daily_outages, t_before, t_after)
                    wifi_affected = (overlap > 0 and pending_action == 'study')

                    new_messages.extend(student.apply_hunger_decay(hours))
                    if pending_action == 'study':
                        avg_k = course_manager.get_average_knowledge()
                        new_messages.extend(student.study(course=target_course, hours=hours, avg_knowledge=avg_k, wifi_penalty=wifi_affected))
                    elif pending_action == 'sleep':
                        new_messages.extend(student.rest(hours=hours))
                    elif pending_action == 'relax':
                        new_messages.extend(student.take_break(hours=hours))

                    # Show popup for ANY action affected by an outage
                    if overlap > 0:
                        dur_min = round(overlap * 60)
                        alert_box.open(
                            f"WiFi Outage  -  Day {day_count}",
                            f"WiFi was down for {dur_min} minutes during your {pending_action} session!",
                            color_type="yellow"
                        )
                    current_game_bg = bg_map.get(pending_action, bg_map['default'])
                    record_action(pending_action, hours, target_course)
                    time_of_day += hours
                    print(f"Time of day: {format_time(time_of_day)}")
                    pending_action = None
                    
                    # Round to nearest minute to avoid float precision issues
                    if round(time_of_day * 60) >= round(DAY_END * 60):
                        day_over = True
                        eod_msgs = student.end_of_day()
                        new_messages.extend(eod_msgs)
                        new_messages.append(f"Day {day_count} is over!")
                        print(f"Day {day_count} ended.")
                        if any("Burnout!" in m for m in eod_msgs):
                            burnout_active = True
                        if any("recovered from burnout" in m for m in eod_msgs):
                            burnout_active = False
                        current_screen_state = DAY_END_SCREEN

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
                    if round(time_of_day * 60) >= round(DAY_END * 60):
                        day_over = True
                        eod_msgs = student.end_of_day()
                        new_messages.extend(eod_msgs)
                        new_messages.append(f"Day {day_count} is over!")
                        print(f"Day {day_count} ended.")
                        if any("Burnout!" in m for m in eod_msgs):
                            burnout_active = True
                        if any("recovered from burnout" in m for m in eod_msgs):
                            burnout_active = False
                        current_screen_state = DAY_END_SCREEN

                if eat_btn.clicked(event):
                    new_messages.extend(student.apply_hunger_decay(0.5))
                    new_messages.extend(student.eat())
                    current_game_bg = bg_map['eat']
                    record_action('eat', 0.5)
                    time_of_day += 0.5  # 30 minutes
                    print(f"Time of day: {format_time(time_of_day)}")
                    if round(time_of_day * 60) >= round(DAY_END * 60):
                        day_over = True
                        eod_msgs = student.end_of_day()
                        new_messages.extend(eod_msgs)
                        new_messages.append(f"Day {day_count} is over!")
                        print(f"Day {day_count} ended.")
                        if any("Burnout!" in m for m in eod_msgs):
                            burnout_active = True
                        if any("recovered from burnout" in m for m in eod_msgs):
                            burnout_active = False
                        current_screen_state = DAY_END_SCREEN

            if new_messages:
                messages.extend(new_messages)
                messages = messages[-5:]

        elif current_screen_state == DAY_END_SCREEN:
            # AlertBox intercepts all input while active during replay 
            if alert_box.active:
                dismissed = alert_box.handle_event(event)
                # After dismissal, tick the runner once more to continue
                if dismissed and replay_runner and not replay_runner.done:
                    step_msgs, alert_info = replay_runner.tick()
                    if alert_info:
                        alert_box.open(*alert_info)
                    messages = replay_runner.last_msgs()
                    # Sync global state for UI
                    day_count = replay_runner.current_day
                    time_of_day = replay_runner.time_cursor
                    if replay_runner.done:
                        if replay_runner.burnout_occurred:
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
        # Sync global state for UI
        day_count = replay_runner.current_day
        time_of_day = replay_runner.time_cursor
        if replay_runner.current_action:
            current_game_bg = bg_map.get(replay_runner.current_action, bg_map['default'])
        if replay_runner.done:
            if replay_runner.burnout_occurred:
                burnout_active = True

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
        # Draw game screen first (background and base UI)
        game_screen(screen, current_game_bg, student, bars, game_buttons, messages, message_font, bar_space)
        
        # Draw clock BEFORE overlay so it is dimmed
        draw_clock(screen, clock_font, date_font, time_of_day, day_count, bar_space)

        # Draw day-end overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # Re-draw status bars AFTER overlay to keep them bright
        avg_k = course_manager.get_average_knowledge()
        for bar in bars:
            bar.draw(screen, avg_k if bar.label == "Knowledge" else
                             student.sleep if bar.label=="Sleep" else 
                             student.health if bar.label=="Health" else
                             student.stress if bar.label=="Stress" else
                             student.motivation if bar.label=="Motivation" else
                             student.hunger if bar.label=="Hunger" else 0)
        
        title_font = pygame.font.Font("assets/fonts/Papernotes.otf", 32)
        title_surf = title_font.render(f"Day {day_count} Complete!", True, (255, 255, 255))
        screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, HEIGHT // 2 - 60))

        if burnout_active:
            burnout_surf = message_font.render(
                f"You're burned out and need to recover for {student.burnout_days_remaining} days!",
                True, (255, 90, 90)
            )
            screen.blit(burnout_surf, (WIDTH // 2 - burnout_surf.get_width() // 2, HEIGHT // 2 - 10))
        else:
            prompt_surf = message_font.render(
                "Continue, repeat today's actions, or quit?", True, (200, 200, 200)
            )
            screen.blit(prompt_surf, (WIDTH // 2 - prompt_surf.get_width() // 2, HEIGHT // 2 - 10))
        continue_btn.draw(screen)
        repeat_btn.draw(screen)
        quit_btn.draw(screen)
        repeat_box.draw(screen)
        alert_box.draw(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
