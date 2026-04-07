import pygame
from environment import day_name


def main_menu(screen, background_image, start_button, continue_button=None):
    screen.blit(background_image, (0, 0))
    start_button.draw(screen)
    if continue_button is not None:
        continue_button.draw(screen)


def save_prompt_screen(screen, yes_btn, no_btn, font):
    """Draw a semi-transparent 'Save before quitting?' dialog."""
    WIDTH, HEIGHT = screen.get_width(), screen.get_height()

    # Dim the whole screen
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 200))
    screen.blit(overlay, (0, 0))

    # Card background
    card_w, card_h = 420, 180
    card_x = (WIDTH - card_w) // 2
    card_y = (HEIGHT - card_h) // 2
    card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
    card_surf.fill((30, 30, 50, 230))
    screen.blit(card_surf, (card_x, card_y))

    # Border
    pygame.draw.rect(screen, (120, 100, 200), (card_x, card_y, card_w, card_h), 2, border_radius=8)

    # Title
    title_font = pygame.font.Font("assets/fonts/Papernotes.otf", 28)
    title_surf = title_font.render("Save Progress?", True, (255, 255, 255))
    screen.blit(title_surf, (card_x + card_w // 2 - title_surf.get_width() // 2, card_y + 22))

    # Sub-text
    sub_surf = font.render("Do you want to save before quitting?", True, (200, 200, 200))
    screen.blit(sub_surf, (card_x + card_w // 2 - sub_surf.get_width() // 2, card_y + 68))

    yes_btn.draw(screen)
    no_btn.draw(screen)


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
                   repeat_box, alert_box,
                   week_count=1, day_in_week=1,
                   repeat_week_btn=None, week_repeat_box=None):
    """Draw the full day-end overlay (background + dim + summary + buttons)."""
    WIDTH, HEIGHT = screen.get_width(), screen.get_height()

    # Base game screen (behind the overlay)
    game_screen(screen, background_image, student, bars, game_buttons,
                messages, message_font, bar_space)

    # Clock before overlay so it gets dimmed with everything else
    draw_clock_fn(screen, clock_font, date_font, time_of_day, day_count, bar_space,
                  week_count=week_count, day_in_week=day_in_week)

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
    screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, HEIGHT // 2 - 80))

    # Week subtitle
    week_label_font = pygame.font.Font("assets/fonts/Papernotes.otf", 22)
    if day_in_week == 7:
        wk_label = f"Week {week_count}, {day_name(day_in_week)} - Week Complete!"
        wk_color = (120, 255, 160)
    else:
        wk_label = f"Week {week_count}, {day_name(day_in_week)}"
        wk_color = (180, 230, 255)
    wk_surf = week_label_font.render(wk_label, True, wk_color)
    screen.blit(wk_surf, (WIDTH // 2 - wk_surf.get_width() // 2, HEIGHT // 2 - 46))

    # Burnout notice OR continue prompt
    if burnout_active:
        burnout_surf = message_font.render(
            f"You're burned out and need to recover for {student.burnout_days_remaining} days!",
            True, (255, 90, 90)
        )
        screen.blit(burnout_surf,
                    (WIDTH // 2 - burnout_surf.get_width() // 2, HEIGHT // 2 - 10))
    else:
        if day_in_week == 7:
            prompt_text = "Week complete! Continue, repeat day, repeat whole week, or quit?"
        else:
            days_left = 7 - day_in_week
            prompt_text = f"Continue, repeat today, or quit?  ({days_left} day(s) until Repeat Week)"
        prompt_surf = message_font.render(prompt_text, True, (200, 200, 200))
        screen.blit(prompt_surf,
                    (WIDTH // 2 - prompt_surf.get_width() // 2, HEIGHT // 2 + 6))

    # Buttons & widgets
    continue_btn.draw(screen)
    repeat_btn.draw(screen)
    if repeat_week_btn is not None:
        repeat_week_btn.draw(screen)   # always drawn; enabled only on day 7
    quit_btn.draw(screen)
    repeat_box.draw(screen)
    if week_repeat_box is not None:
        week_repeat_box.draw(screen)
    alert_box.draw(screen)
