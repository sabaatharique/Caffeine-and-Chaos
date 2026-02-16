import pygame
import sys
from student import Student
from ui import StatusBar, Button, InputBox
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
input_box = InputBox(message_font)
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
continue_btn = Button(WIDTH // 2 - 134, HEIGHT // 2 + 30, 124, 40, "Continue", button_font)
quit_btn = Button(WIDTH // 2 + 10, HEIGHT // 2 + 30, 124, 40, "Quit", button_font)

messages = []

running = True
while running:
    remaining_hours = DAY_END - time_of_day

    # Update button states (disabled when day is over)
    if day_over or remaining_hours <= 0:
        for btn in game_buttons:
            btn.enabled = False
    else:
        study_btn.enabled = student.action_status['study'] and remaining_hours >= 1
        sleep_btn.enabled = student.action_status['sleep'] and remaining_hours >= 1
        relax_btn.enabled = student.action_status['relax'] and remaining_hours >= 1
        eat_btn.enabled = student.action_status['eat'] and remaining_hours >= 0.5
        drink_coffee_btn.enabled = student.action_status['coffee'] and remaining_hours >= 0.25

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if current_screen_state == MAIN_MENU:
            if start_btn.clicked(event):
                current_screen_state = GAME_SCREEN
        elif current_screen_state == GAME_SCREEN:
            new_messages = []

            # If the input box is active, feed events to it
            if input_box.active:
                hours = input_box.handle_event(event)
                if hours is not None:
                    # Execute the pending action with the entered hours
                    if pending_action == 'study':
                        new_messages.extend(student.study(hours=hours))
                    elif pending_action == 'sleep':
                        new_messages.extend(student.rest(hours=hours))
                    elif pending_action == 'relax':
                        new_messages.extend(student.take_break(hours=hours))
                    # Advance time of day
                    time_of_day += hours
                    print(f"Time of day: {format_time(time_of_day)}")
                    pending_action = None
                    if time_of_day >= DAY_END:
                        day_over = True
                        new_messages.extend(student.end_of_day())
                        new_messages.append(f"Day {day_count} is over!")
                        print(f"Day {day_count} ended.")
                        current_screen_state = DAY_END_SCREEN
            else:
                # Open the input prompt for actions that need hours
                remaining_hours = DAY_END - time_of_day
                remaining_whole = int(remaining_hours)

                if study_btn.clicked(event):
                    pending_action = 'study'
                    cap = min(student.max_hours('study'), remaining_whole)
                    input_box.open('study', cap)

                if sleep_btn.clicked(event):
                    pending_action = 'sleep'
                    cap = min(student.max_hours('sleep'), remaining_whole)
                    input_box.open('sleep', cap)

                if relax_btn.clicked(event):
                    pending_action = 'relax'
                    cap = min(student.max_hours('relax'), remaining_whole)
                    input_box.open('relax', cap)

                # Instant actions (fixed durations)
                if drink_coffee_btn.clicked(event):
                    new_messages.extend(student.drink_coffee())
                    time_of_day += 0.25  # 15 minutes
                    print(f"Time of day: {format_time(time_of_day)}")
                    if time_of_day >= DAY_END:
                        day_over = True
                        new_messages.extend(student.end_of_day())
                        new_messages.append(f"Day {day_count} is over!")
                        print(f"Day {day_count} ended.")
                        current_screen_state = DAY_END_SCREEN

                if eat_btn.clicked(event):
                    new_messages.extend(student.eat())
                    time_of_day += 0.5  # 30 minutes
                    print(f"Time of day: {format_time(time_of_day)}")
                    if time_of_day >= DAY_END:
                        day_over = True
                        new_messages.extend(student.end_of_day())
                        new_messages.append(f"Day {day_count} is over!")
                        print(f"Day {day_count} ended.")
                        current_screen_state = DAY_END_SCREEN

            if new_messages:
                messages.extend(new_messages)
                messages = messages[-5:]

        elif current_screen_state == DAY_END_SCREEN:
            if continue_btn.clicked(event):
                day_count += 1
                time_of_day = DAY_START
                day_over = False
                messages = [f"Day {day_count} begins!"]
                print(f"\n--- Day {day_count} ---")
                print(f"Time of day: {format_time(time_of_day)}")
                current_screen_state = GAME_SCREEN
            if quit_btn.clicked(event):
                running = False

    screen.fill((30, 30, 30))

    if current_screen_state == MAIN_MENU:
        main_menu(screen, main_bg, start_btn)
    elif current_screen_state == GAME_SCREEN:
        game_screen(screen, study_bg, student, bars, game_buttons, messages, message_font)
        input_box.draw(screen)
    elif current_screen_state == DAY_END_SCREEN:
        game_screen(screen, study_bg, student, bars, game_buttons, messages, message_font)
        # Draw day-end overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))
        title_font = pygame.font.Font("assets/fonts/Papernotes.otf", 32)
        title_surf = title_font.render(f"Day {day_count} Complete!", True, (255, 255, 255))
        screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, HEIGHT // 2 - 50))
        prompt_surf = message_font.render("Do you want to continue to the next day?", True, (200, 200, 200))
        screen.blit(prompt_surf, (WIDTH // 2 - prompt_surf.get_width() // 2, HEIGHT // 2 - 10))
        continue_btn.draw(screen)
        quit_btn.draw(screen)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
