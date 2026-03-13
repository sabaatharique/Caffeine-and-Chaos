import pygame


def main_menu(screen, background_image, start_button):
    screen.blit(background_image, (0, 0))
    start_button.draw(screen)


def game_screen(screen, background_image, student, bars, buttons,
                messages, message_font, bar_margin):
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


def day_end_screen(screen, background_image, student, bars, game_buttons,
                   messages, message_font, bar_space,
                   draw_clock_fn, clock_font, date_font,
                   time_of_day, day_count,
                   avg_knowledge, burnout_active,
                   continue_btn, repeat_btn, quit_btn,
                   repeat_box, alert_box):
    """Draw the full day-end overlay (background + dim + summary + buttons)."""
    WIDTH, HEIGHT = screen.get_width(), screen.get_height()

    # Base game screen (behind the overlay)
    game_screen(screen, background_image, student, bars, game_buttons,
                messages, message_font, bar_space)

    # Clock before overlay so it gets dimmed with everything else
    draw_clock_fn(screen, clock_font, date_font, time_of_day, day_count, bar_space)

    # Dark overlay
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    screen.blit(overlay, (0, 0))

    # Re-draw status bars AFTER overlay so they stay bright
    for bar in bars:
        value = (
            avg_knowledge        if bar.label == "Knowledge"   else
            student.sleep        if bar.label == "Sleep"       else
            student.health       if bar.label == "Health"      else
            student.stress       if bar.label == "Stress"      else
            student.motivation   if bar.label == "Motivation"  else
            student.hunger       if bar.label == "Hunger"      else 0
        )
        bar.draw(screen, value)

    # Title
    title_font = pygame.font.Font("assets/fonts/Papernotes.otf", 32)
    title_surf = title_font.render(f"Day {day_count} Complete!", True, (255, 255, 255))
    screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, HEIGHT // 2 - 60))

    # Burnout notice OR continue prompt
    if burnout_active:
        burnout_surf = message_font.render(
            f"You're burned out and need to recover for {student.burnout_days_remaining} days!",
            True, (255, 90, 90)
        )
        screen.blit(burnout_surf,
                    (WIDTH // 2 - burnout_surf.get_width() // 2, HEIGHT // 2 - 10))
    else:
        prompt_surf = message_font.render(
            "Continue, repeat today's actions, or quit?", True, (200, 200, 200)
        )
        screen.blit(prompt_surf,
                    (WIDTH // 2 - prompt_surf.get_width() // 2, HEIGHT // 2 - 10))

    # Buttons & widgets
    continue_btn.draw(screen)
    repeat_btn.draw(screen)
    quit_btn.draw(screen)
    repeat_box.draw(screen)
    alert_box.draw(screen)
