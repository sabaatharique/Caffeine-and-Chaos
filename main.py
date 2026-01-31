# main.py
import pygame
import sys
from student import Student
from ui import StatusBar, Button

pygame.init()

WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Student State Demo")

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

font = pygame.font.SysFont(None, 28)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if study_btn.clicked(event):
            student.study()

        if sleep_btn.clicked(event):
            student.rest()

        if relax_btn.clicked(event):
            student.relax()

    screen.fill((30, 30, 30))

    title = font.render("Student Simulation", True, (255, 255, 255))
    screen.blit(title, (30, 20))

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

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()

