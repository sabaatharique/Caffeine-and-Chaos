import pygame

def main_menu(screen, background_image, start_button):
    screen.blit(background_image, (0, 0))
    start_button.draw(screen)

def game_screen(screen, background_image, student, bars, buttons, messages, message_font):
    screen.blit(background_image, (0, 0))

    y_offset = 220
    for msg in messages:
        msg_surface = message_font.render(msg, True, (255, 255, 0))
        screen.blit(msg_surface, (30, y_offset))
        y_offset += 30

    bars[0].draw(screen, student.knowledge)
    bars[1].draw(screen, student.sleep)
    bars[2].draw(screen, student.health)
    bars[3].draw(screen, student.stress)
    bars[4].draw(screen, student.motivation)

    for button in buttons:
        button.draw(screen)
