import pygame
import sys
from student import Student
from ui import StatusBar, Button

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Caffeine & Chaos")

clock = pygame.time.Clock()

student = Student()

# Status bars
bars = [
    StatusBar(30, 80, 220, 20, "Knowledge"),
    StatusBar(30, 120, 220, 20, "Sleep"),
    StatusBar(30, 160, 220, 20, "Health"),
    StatusBar(30, 200, 220, 20, "Stress"),
    StatusBar(30, 240, 220, 20, "Motivation"),
]

# Buttons
study_btn = Button(350, 450, 120, 40, "Study")
sleep_btn = Button(500, 450, 120, 40, "Sleep")
relax_btn = Button(650, 450, 120, 40, "Relax")
attend_class_btn = Button(350, 500, 120, 40, "Attend Class")
drink_coffee_btn = Button(500, 500, 120, 40, "Drink Coffee")
eat_btn = Button(650, 500, 120, 40, "Eat")

font = pygame.font.SysFont(None, 28)
message_font = pygame.font.SysFont(None, 24)
messages = []

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        new_messages = []
        if study_btn.clicked(event):
            new_messages.extend(student.study())

        if sleep_btn.clicked(event):
            new_messages.extend(student.rest())

        if relax_btn.clicked(event):
            new_messages.extend(student.take_break())

        if attend_class_btn.clicked(event):
            new_messages.extend(student.attend_class())

        if drink_coffee_btn.clicked(event):
            new_messages.extend(student.drink_coffee())

        if eat_btn.clicked(event):
            new_messages.extend(student.eat())


        if new_messages:
            messages.extend(new_messages)
            messages = messages[-5:] # Keep last 5 messages

    screen.fill((30, 30, 30))

    title = font.render("Caffeine & Chaos", True, (255, 255, 255))
    screen.blit(title, (30, 20))

    # Display messages
    y_offset = 280
    for msg in messages:
        msg_surface = message_font.render(msg, True, (255, 255, 0)) # Yellow messages
        screen.blit(msg_surface, (30, y_offset))
        y_offset += 25


    # Draw bars
    bars[0].draw(screen, student.knowledge)
    bars[1].draw(screen, student.sleep)
    bars[2].draw(screen, student.health)
    bars[3].draw(screen, student.stress)
    bars[4].draw(screen, student.motivation)

    # Draw buttons
    study_btn.draw(screen)
    sleep_btn.draw(screen)
    relax_btn.draw(screen)
    attend_class_btn.draw(screen)
    drink_coffee_btn.draw(screen)
    eat_btn.draw(screen)


    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()

