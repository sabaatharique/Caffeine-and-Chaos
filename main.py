import pygame
import sys
from student import Student
from ui import StatusBar, Button, InputBox, NumberBox
from screens import main_menu, game_screen

pygame.init()

WIDTH, HEIGHT = 800, 600
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

student = Student()

day_actions = []

def record_action(action: str, hours: float):
    day_actions.append((action, hours))

def replay_days(student, actions, n: int, start_day: int):
    msgs = []
    current_day = start_day
    burnout_occurred = False
    for _ in range(n):
        current_day += 1
        for action, hours in actions:
            if action == 'study' and student.action_status['study']:
                msgs.extend(student.apply_hunger_decay(hours))
                msgs.extend(student.study(hours=hours))
            elif action == 'sleep' and student.action_status['sleep']:
                msgs.extend(student.apply_hunger_decay(hours))
                msgs.extend(student.rest(hours=hours))
            elif action == 'relax' and student.action_status['relax']:
                msgs.extend(student.apply_hunger_decay(hours))
                msgs.extend(student.take_break(hours=hours))
            elif action == 'eat' and student.action_status['eat']:
                msgs.extend(student.apply_hunger_decay(0.5))
                msgs.extend(student.eat())
            elif action == 'coffee' and student.action_status['coffee']:
                msgs.extend(student.apply_hunger_decay(0.25))
                msgs.extend(student.drink_coffee())
        day_msgs = student.end_of_day()
        msgs.extend(day_msgs)
        msgs.append(f"Day {current_day} completed (fast-forward).")
        # Stop replay if burnout was triggered this day
        if any("Burnout!" in m for m in day_msgs):
            burnout_occurred = True
            msgs.append("Loop paused. You need to recover!")
            break
    return current_day, msgs, burnout_occurred

# Game states
MAIN_MENU = "main_menu"
GAME_SCREEN = "game_screen"
DAY_END_SCREEN = "day_end_screen"
current_screen_state = MAIN_MENU

# Load images
main_bg = pygame.image.load("assets/images/main.jpg")
study_bg = pygame.image.load("assets/images/study.jpg")

button_font = pygame.font.Font("assets/fonts/Papernotes.otf", 22)
message_font = pygame.font.Font("assets/fonts/Papernotes.otf", 20)
input_font = pygame.font.Font("assets/fonts/Papernotes.otf", 16)
input_box = InputBox(message_font, input_font)
repeat_box = NumberBox(message_font, input_font)
pending_action = None  # tracks which action is waiting for hour input

# Status bars
bars = [
    StatusBar(30, 60, 124, 20, "Knowledge", message_font),
    StatusBar(184, 60, 124, 20, "Sleep", message_font),
    StatusBar(338, 60, 124, 20, "Health", message_font),
    StatusBar(492, 60, 124, 20, "Stress", message_font),
    StatusBar(646, 60, 124, 20, "Motivation", message_font),
]

# Buttons
start_btn = Button(WIDTH - 154, HEIGHT - 70, 124, 40, "Start", button_font)
study_btn = Button(30, 520, 124, 40, "Study", button_font)
sleep_btn = Button(184, 520, 124, 40, "Sleep", button_font)
relax_btn = Button(338, 520, 124, 40, "Relax", button_font)
drink_coffee_btn = Button(492, 520, 124, 40, "Drink Coffee", button_font)
eat_btn = Button(646, 520, 124, 40, "Eat", button_font)

game_buttons = [study_btn, sleep_btn, relax_btn, drink_coffee_btn, eat_btn]

# Day-end buttons  
_btn_y = HEIGHT // 2 + 40
continue_btn = Button(WIDTH // 2 - 196, _btn_y, 114, 40, "Continue", button_font)
repeat_btn   = Button(WIDTH // 2 -  57, _btn_y, 114, 40, "Repeat",   button_font)
quit_btn     = Button(WIDTH // 2 + 82,  _btn_y, 114, 40, "Quit",     button_font)

messages = []

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
                current_screen_state = GAME_SCREEN

        elif current_screen_state == GAME_SCREEN:
            new_messages = []

            if repeat_box.active:
                n = repeat_box.handle_event(event)
                if n is not None:
                    day_count, replay_msgs, replay_burnout = replay_days(student, day_actions, n, day_count)
                    messages = replay_msgs[-5:]
                    if replay_burnout:
                        burnout_active = True
                    current_screen_state = DAY_END_SCREEN
                    day_over = True

            elif input_box.active:
                hours = input_box.handle_event(event)
                if hours is not None:
                    new_messages.extend(student.apply_hunger_decay(hours))
                    if pending_action == 'study':
                        new_messages.extend(student.study(hours=hours))
                    elif pending_action == 'sleep':
                        new_messages.extend(student.rest(hours=hours))
                    elif pending_action == 'relax':
                        new_messages.extend(student.take_break(hours=hours))
                    record_action(pending_action, hours)
                    time_of_day += hours
                    print(f"Time of day: {format_time(time_of_day)}")
                    pending_action = None
                    if time_of_day >= DAY_END:
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
                    input_box.open('study', cap)

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
                    record_action('coffee', 0.25)
                    time_of_day += 0.25  # 15 minutes
                    print(f"Time of day: {format_time(time_of_day)}")
                    if time_of_day >= DAY_END:
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
                    record_action('eat', 0.5)
                    time_of_day += 0.5  # 30 minutes
                    print(f"Time of day: {format_time(time_of_day)}")
                    if time_of_day >= DAY_END:
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
            if repeat_box.active:
                n = repeat_box.handle_event(event)
                if n is not None:
                    day_count, replay_msgs, replay_burnout = replay_days(student, day_actions, n, day_count)
                    messages = replay_msgs[-5:]
                    if replay_burnout:
                        burnout_active = True

            else:
                if continue_btn.clicked(event):
                    day_count += 1
                    time_of_day = DAY_START
                    day_over = False
                    day_actions.clear()
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

    screen.fill((30, 30, 30))

    if current_screen_state == MAIN_MENU:
        main_menu(screen, main_bg, start_btn)
    elif current_screen_state == GAME_SCREEN:
        game_screen(screen, study_bg, student, bars, game_buttons, messages, message_font)
        input_box.draw(screen)
        repeat_box.draw(screen)
    elif current_screen_state == DAY_END_SCREEN:
        game_screen(screen, study_bg, student, bars, game_buttons, messages, message_font)
        # Draw day-end overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        title_font = pygame.font.Font("assets/fonts/Papernotes.otf", 32)
        title_surf = title_font.render(f"Day {day_count} Complete!", True, (255, 255, 255))
        screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, HEIGHT // 2 - 60))
        
        if burnout_active:
            burnout_surf = message_font.render(f"You're burned out and need to recover for {student.burnout_days_remaining} days!", True, (255, 90, 90))
            screen.blit(burnout_surf, (WIDTH // 2 - burnout_surf.get_width() // 2, HEIGHT // 2 - 10))
        else:
            prompt_surf = message_font.render("Continue, repeat today's actions, or quit?", True, (200, 200, 200))
            screen.blit(prompt_surf, (WIDTH // 2 - prompt_surf.get_width() // 2, HEIGHT // 2 - 10))
        continue_btn.draw(screen)
        repeat_btn.draw(screen)
        quit_btn.draw(screen)
        repeat_box.draw(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
