import pygame

def main_menu(screen, background_image, start_button):
    screen.blit(background_image, (0, 0))
    start_button.draw(screen)

def game_screen(screen, background_image, student, bars, buttons, messages, message_font, bar_margin):
    screen.blit(background_image, (0, 0))

    # Draw Message Box Background
    if messages:
        msg_box_w = 265
        msg_box_h = len(messages) * 30 + 20
        msg_box_x = bar_margin
        msg_box_y = 210
        
        msg_overlay = pygame.Surface((msg_box_w, msg_box_h), pygame.SRCALPHA)
        msg_overlay.fill((0, 0, 0, 180))
        screen.blit(msg_overlay, (msg_box_x, msg_box_y))

        y_offset = msg_box_y + 10
        for msg in messages:
            msg_surface = message_font.render(msg, True, (255, 255, 0))
            screen.blit(msg_surface, (msg_box_x + 10, y_offset))
            y_offset += 30

    # bars[0] (Knowledge) is drawn separately in main.py to show average
    bars[1].draw(screen, student.sleep)
    bars[2].draw(screen, student.health)
    bars[3].draw(screen, student.stress)
    bars[4].draw(screen, student.motivation)
    bars[5].draw(screen, student.hunger)

    for button in buttons:
        button.draw(screen)
