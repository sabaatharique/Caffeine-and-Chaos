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
            # Colour-code sickness messages for instant recognition
            if msg.startswith("[SICK!]"):
                msg_color = (255, 80, 80)      # bright red — onset
            elif msg.startswith("[SICK]"):
                msg_color = (255, 160, 40)     # amber — still sick
            elif msg.startswith("[RECOVERED]"):
                msg_color = (80, 255, 140)     # lime green — recovery
            else:
                msg_color = (255, 255, 0)      # default yellow
            msg_surface = message_font.render(msg, True, msg_color)
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
                   repeat_week_btn=None, week_repeat_box=None,
                   sick_active=False):
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

    # Sickness notice (shown even alongside burnout — they can co-exist)
    if sick_active:
        # Larger font for sickness notice
        sick_font = pygame.font.Font("assets/fonts/Papernotes.otf", 26)
        sick_surf = sick_font.render(
            " YOU ARE SICK: STUDY -50% | CLASSES BLOCKED",
            True, (255, 50, 50)
        )
        # Add a subtle background for the sickness notice to pop more
        s_bg_rect = sick_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30))
        s_bg_rect.inflate_ip(20, 10)
        pygame.draw.rect(screen, (40, 0, 0, 200), s_bg_rect, border_radius=5)
        screen.blit(sick_surf, (WIDTH // 2 - sick_surf.get_width() // 2, HEIGHT // 2 - 40))

    # Burnout notice OR continue prompt
    notice_y = HEIGHT // 2 + (16 if sick_active else 0)
    if burnout_active:
        burnout_surf = message_font.render(
            f"You're burned out and need to recover for {student.burnout_days_remaining} days!",
            True, (255, 90, 90)
        )
        screen.blit(burnout_surf,
                    (WIDTH // 2 - burnout_surf.get_width() // 2, notice_y - 10))
    else:
        if day_in_week == 7:
            prompt_text = "Week complete! Continue, repeat day, repeat whole week, or quit?"
        else:
            days_left = 7 - day_in_week
            prompt_text = f"Continue, repeat today, or quit?  ({days_left} day(s) until Repeat Week)"
        prompt_surf = message_font.render(prompt_text, True, (200, 200, 200))
        screen.blit(prompt_surf,
                    (WIDTH // 2 - prompt_surf.get_width() // 2, notice_y + 6))

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


def exam_screen(screen, exam_type, continue_btn, font):
    """Full-screen splash shown for mid or final exams."""
    WIDTH, HEIGHT = screen.get_width(), screen.get_height()

    # Dark gradient background
    bg = pygame.Surface((WIDTH, HEIGHT))
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(10 + 30 * t)
        g = int(10 + 10 * t)
        b = int(40 + 60 * t)
        pygame.draw.line(bg, (r, g, b), (0, y), (WIDTH, y))
    screen.blit(bg, (0, 0))

    # Decorative top bar
    pygame.draw.rect(screen, (100, 80, 200), (0, 0, WIDTH, 6))

    # Card
    card_w, card_h = 560, 280
    card_x = (WIDTH - card_w) // 2
    card_y = (HEIGHT - card_h) // 2 - 30
    card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
    card_surf.fill((20, 20, 50, 220))
    screen.blit(card_surf, (card_x, card_y))
    pygame.draw.rect(screen, (120, 100, 220), (card_x, card_y, card_w, card_h), 2, border_radius=10)

    title_font  = pygame.font.Font("assets/fonts/Papernotes.otf", 38)
    sub_font    = pygame.font.Font("assets/fonts/Papernotes.otf", 22)
    detail_font = pygame.font.Font("assets/fonts/Papernotes.otf", 18)

    if exam_type == "mid":
        title_text   = "Midterm Exams"
        sub_text     = "Weeks 1-7 are behind you."
        detail_text  = "Show what you've learned!"
        color_accent = (200, 160, 255)
    else:
        title_text   = "Final Exams"
        sub_text     = "The semester has been a journey."
        detail_text  = "Give it everything you've got!"
        color_accent = (255, 200, 100)

    # Emoji icon simulation via colored circle
    pygame.draw.circle(screen, color_accent,
                       (WIDTH // 2, card_y + 52), 26)
    pygame.draw.circle(screen, (20, 20, 50),
                       (WIDTH // 2, card_y + 52), 20)

    title_surf = title_font.render(title_text, True, color_accent)
    screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, card_y + 86))

    sub_surf = sub_font.render(sub_text, True, (210, 210, 255))
    screen.blit(sub_surf, (WIDTH // 2 - sub_surf.get_width() // 2, card_y + 138))

    detail_surf = detail_font.render(detail_text, True, (160, 160, 200))
    screen.blit(detail_surf, (WIDTH // 2 - detail_surf.get_width() // 2, card_y + 170))

    # Divider
    pygame.draw.line(screen, (80, 80, 140),
                     (card_x + 40, card_y + 210), (card_x + card_w - 40, card_y + 210), 1)

    hint_surf = detail_font.render("Press Continue when you're ready.", True, (130, 130, 170))
    screen.blit(hint_surf, (WIDTH // 2 - hint_surf.get_width() // 2, card_y + 224))

    continue_btn.draw(screen)


def semester_end_screen(screen, student, avg_knowledge, quit_btn, font):
    """Shown after the final exam — semester complete!"""
    WIDTH, HEIGHT = screen.get_width(), screen.get_height()

    # Dark background
    bg = pygame.Surface((WIDTH, HEIGHT))
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(5 + 20 * t)
        g = int(20 + 40 * t)
        b = int(10 + 30 * t)
        pygame.draw.line(bg, (r, g, b), (0, y), (WIDTH, y))
    screen.blit(bg, (0, 0))
    pygame.draw.rect(screen, (60, 200, 100), (0, 0, WIDTH, 6))

    title_font  = pygame.font.Font("assets/fonts/Papernotes.otf", 42)
    sub_font    = pygame.font.Font("assets/fonts/Papernotes.otf", 22)
    stat_font   = pygame.font.Font("assets/fonts/Papernotes.otf", 20)
    detail_font = pygame.font.Font("assets/fonts/Papernotes.otf", 16)

    # Card
    card_w, card_h = 580, 340
    card_x = (WIDTH - card_w) // 2
    card_y = (HEIGHT - card_h) // 2 - 20
    card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
    card_surf.fill((10, 30, 20, 220))
    screen.blit(card_surf, (card_x, card_y))
    pygame.draw.rect(screen, (60, 200, 100), (card_x, card_y, card_w, card_h), 2, border_radius=10)

    # Gold star decoration
    pygame.draw.circle(screen, (255, 220, 50), (WIDTH // 2, card_y + 44), 28)
    pygame.draw.circle(screen, (10, 30, 20),   (WIDTH // 2, card_y + 44), 20)

    title_surf = title_font.render("Semester Complete!", True, (100, 255, 140))
    screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, card_y + 76))

    sub_surf = sub_font.render("You survived 15 weeks — congratulations!", True, (200, 255, 220))
    screen.blit(sub_surf, (WIDTH // 2 - sub_surf.get_width() // 2, card_y + 126))

    # Stat summary
    pygame.draw.line(screen, (40, 120, 60),
                     (card_x + 50, card_y + 162), (card_x + card_w - 50, card_y + 162), 1)

    stats = [
        ("Knowledge",   f"{avg_knowledge:.1f} / 100",  (120, 220, 255)),
        ("Health",      f"{student.health:.1f} / 100", (255, 140, 140)),
        ("Stress",      f"{student.stress:.1f} / 100", (255, 200,  80)),
        ("Motivation",  f"{student.motivation:.1f} / 100", (160, 255, 160)),
    ]
    col_x = [card_x + 60, card_x + 60 + (card_w - 120) // 2]
    for i, (label, value, color) in enumerate(stats):
        cx = col_x[i % 2]
        cy = card_y + 174 + (i // 2) * 38
        lbl_surf = stat_font.render(f"{label}:", True, (160, 200, 160))
        val_surf = stat_font.render(value, True, color)
        screen.blit(lbl_surf, (cx, cy))
        screen.blit(val_surf, (cx + 130, cy))

    hint_surf = detail_font.render("Thanks for playing Caffeine & Chaos!", True, (100, 160, 100))
    screen.blit(hint_surf, (WIDTH // 2 - hint_surf.get_width() // 2, card_y + 296))

    quit_btn.draw(screen)
