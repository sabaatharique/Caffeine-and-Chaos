import pygame
import sys
from student import Student
from ui import StatusBar, Button
from screens import main_menu, game_screen

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Caffeine & Chaos")

clock = pygame.time.Clock()

student = Student()

# Game states
MAIN_MENU = "main_menu"
GAME_SCREEN = "game_screen"
current_screen_state = MAIN_MENU

# Load images
main_bg = pygame.image.load("assets/images/main.jpg")
study_bg = pygame.image.load("assets/images/study.jpg")

button_font = pygame.font.Font("assets/fonts/Papernotes.otf", 22)
message_font = pygame.font.Font("assets/fonts/Papernotes.otf", 20)

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
messages = []

running = True
while running:
    # Update button states
    study_btn.enabled = student.action_status['study']
    sleep_btn.enabled = student.action_status['sleep']
    relax_btn.enabled = student.action_status['relax']
    eat_btn.enabled = student.action_status['eat']
    drink_coffee_btn.enabled = student.action_status['coffee']

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if current_screen_state == MAIN_MENU:
            if start_btn.clicked(event):
                current_screen_state = GAME_SCREEN
        elif current_screen_state == GAME_SCREEN:
            new_messages = []
            if study_btn.clicked(event):
                new_messages.extend(student.study())

            if sleep_btn.clicked(event):
                new_messages.extend(student.rest())

            if relax_btn.clicked(event):
                new_messages.extend(student.take_break())

            if drink_coffee_btn.clicked(event):
                new_messages.extend(student.drink_coffee())

            if eat_btn.clicked(event):
                new_messages.extend(student.eat())

            if new_messages:
                messages.extend(new_messages)
                messages = messages[-5:]

    screen.fill((30, 30, 30))

    if current_screen_state == MAIN_MENU:
        main_menu(screen, main_bg, start_btn)
    elif current_screen_state == GAME_SCREEN:
        game_screen(screen, study_bg, student, bars, game_buttons, messages, message_font)


    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
