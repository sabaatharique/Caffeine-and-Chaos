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
        msg_box_x = bar_margin
        msg_box_y = 380

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
        sick_font = pygame.font.Font("assets/fonts/Papernotes.otf", 26)
        sick_surf = sick_font.render(
            " YOU ARE SICK: STUDY -50%, CLASSES BLOCKED",
            True, (255, 50, 50)
        )
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
        repeat_week_btn.draw(screen)
    quit_btn.draw(screen)
    repeat_box.draw(screen)
    if week_repeat_box is not None:
        week_repeat_box.draw(screen)
    alert_box.draw(screen)


# Shared helpers 

def _draw_results_bg(screen, accent_color, top_bar_color):
    """Draw dark gradient background + decorative top bar."""
    WIDTH, HEIGHT = screen.get_width(), screen.get_height()
    bg = pygame.Surface((WIDTH, HEIGHT))
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(8  + 25 * t)
        g = int(8  + 18 * t)
        b = int(35 + 55 * t)
        pygame.draw.line(bg, (r, g, b), (0, y), (WIDTH, y))
    screen.blit(bg, (0, 0))
    pygame.draw.rect(screen, top_bar_color, (0, 0, WIDTH, 5))


def _draw_course_card(screen, course, card_x, card_y, card_w,
                      font_h, font_b, font_d,
                      show_final=False, attendance_blocked=False):
    """
    Draw a single scrollable course card.
    Returns the y-position *after* the card (next card's card_y).
    """
    # Real-time attendance (against occurred classes) for display & eligibility badge
    occ_att_pct = course.get_occurred_attendance_percentage()
    att_ok       = course.is_attendance_eligible()
    att_color    = (50, 220, 120) if att_ok else (220, 60, 60)

    # Build assessment rows
    rows = []
    
    # 1. Attendance row
    att_str = f"{occ_att_pct:.0f}%  ({course.attended_classes}/{course.occurred_classes})"
    if attendance_blocked:
        att_str += "  ** BARRED (< 85%) **"
    rows.append(("Attendance:", att_str, att_color))

    # 2. Theory / Lab marks
    if course.course_type == "Theory":
        if course.quiz_marks:
            max_mark = 5 * course.credits
            marks_str = "  ".join(f"Q{i+1}: {m / 100 * max_mark:.1f}/{max_mark}" for i, m in enumerate(course.quiz_marks))
            rows.append(("Quizzes:", marks_str, None))
        if course.mid_mark is not None:
            rows.append(("Midterm:", f"{course.mid_mark:.1f}%", None))
        if show_final and course.final_mark is not None:
            rows.append(("Final Exam:", f"{course.final_mark:.1f}%", None))
    elif course.course_type == "Lab":
        if course.lab_evaluations:
            evals_str = "  ".join(f"E{i+1}: {m:.0f}%" for i, m in enumerate(course.lab_evaluations))
            rows.append(("Lab Evals:", evals_str, None))
        if course.lab_mid is not None:
            rows.append(("Lab Mid:", f"{course.lab_mid:.1f}%", None))
        if show_final and course.lab_final is not None:
            rows.append(("Lab Final:", f"{course.lab_final:.1f}%", None))

    # 3. Final Grade
    if show_final:
        pct = course.calculate_total_marks()
        letter = course.get_letter_grade()
        gp = course.calculate_grade()
        if pct is not None:
            val_col = (
                (80, 255, 140)  if pct >= 75 else
                (180, 220, 255) if pct >= 60 else
                (255, 200, 80)  if pct >= 50 else
                (255, 130, 80)  if pct >= 40 else
                (255, 60, 60)
            )
            rows.append(("Grade:", f"{pct:.1f}%  {letter}  (GP {gp:.2f})", val_col))

    lh = max(font_d.get_height(), font_b.get_height()) + 8
    card_h = 14 + font_h.get_height() + 10 + lh * len(rows) + 6
    card_h = max(card_h, 80)

    # Background
    card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
    card_surf.fill((20, 20, 42, 220))
    screen.blit(card_surf, (card_x, card_y))

    border_col = (220, 60, 60) if attendance_blocked else (80, 60, 160)
    pygame.draw.rect(screen, border_col, (card_x, card_y, card_w, card_h), 2, border_radius=8)

    cy = card_y + 12

    # Course name + type badge
    badge_col = (80, 180, 255) if course.course_type == "Theory" else (80, 230, 180)
    name_surf = font_h.render(f"{course.name}  ({course.credits} credits)", True, badge_col)
    screen.blit(name_surf, (card_x + 14, cy))
    cy += name_surf.get_height() + 12

    # Assessment rows
    for label, value, color in rows:
        lbl_surf = font_d.render(label, True, (150, 145, 195))
        val_color = color if color else (220, 215, 240)
        val_surf = font_b.render(value, True, val_color)
        
        screen.blit(lbl_surf, (card_x + 14, cy))
        screen.blit(val_surf, (card_x + 14 + lbl_surf.get_width() + 12, cy))
        cy += max(lbl_surf.get_height(), val_surf.get_height()) + 8

    return card_y + card_h + 8


# Midterm Results Screen 

def midterm_results_screen(screen, course_manager, continue_btn, scroll_y=0):
    """
    Shown after Midterm Exams are taken (after week 7).
    Displays per-course: quiz history, attendance bar, midterm mark.
    Returns content_height for scroll management.
    """
    WIDTH, HEIGHT = screen.get_width(), screen.get_height()
    _draw_results_bg(screen, (200, 160, 255), (100, 80, 200))

    title_font  = pygame.font.Font("assets/fonts/Papernotes.otf", 42)
    sub_font    = pygame.font.Font("assets/fonts/Papernotes.otf", 24)
    head_font   = pygame.font.Font("assets/fonts/Papernotes.otf", 24)
    body_font   = pygame.font.Font("assets/fonts/Papernotes.otf", 20)
    detail_font = pygame.font.Font("assets/fonts/Papernotes.otf", 18)

    # Header
    title_surf = title_font.render("Post-Midterm Summary", True, (200, 160, 255))
    screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, 14))
    sub_surf = sub_font.render("Weeks 1 - 7", True, (160, 148, 210))
    screen.blit(sub_surf, (WIDTH // 2 - sub_surf.get_width() // 2, 54))

    # Scrollable region
    content_top = 82
    strip_h = 90
    screen.set_clip((0, content_top, WIDTH, HEIGHT - content_top - strip_h))

    card_w  = WIDTH - 60
    card_x  = 30
    cy      = content_top + 8 - int(scroll_y)
    courses = course_manager.courses

    for course in courses:
        att_blocked = not course.is_attendance_eligible()
        cy = _draw_course_card(screen, course, card_x, cy, card_w,
                               head_font, body_font, detail_font,
                               show_final=False,
                               attendance_blocked=att_blocked)

    content_height = cy + int(scroll_y) - content_top + 120

    # Attendance warning
    blocked = [c for c in courses if not c.is_attendance_eligible()]
    if blocked:
        warn_y = cy + 6
        warn_surf = sub_font.render(
            f"WARNING: {len(blocked)} course(s) below 85% attendance — Final Exam may be blocked!",
            True, (255, 90, 70))
        screen.blit(warn_surf, (WIDTH // 2 - warn_surf.get_width() // 2, warn_y))

    screen.set_clip(None)

    # Footer fade effect
    fade_h = 90
    fade = pygame.Surface((WIDTH, fade_h), pygame.SRCALPHA)
    for i in range(fade_h):
        alpha = int(200 * (i / fade_h))
        pygame.draw.line(fade, (8, 8, 35, alpha), (0, fade_h - 1 - i), (WIDTH, fade_h - 1 - i))
    screen.blit(fade, (0, HEIGHT - fade_h))

    # Continue button
    continue_btn.rect.centerx = WIDTH // 2
    continue_btn.rect.y       = HEIGHT - 64
    continue_btn.draw(screen)

    return content_height


# Exam Screen

def exam_screen(screen, exam_type, continue_btn, font, course_manager=None):
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

    pygame.draw.rect(screen, (100, 80, 200), (0, 0, WIDTH, 6))

    # Card
    card_w, card_h = 600, 320
    card_x = (WIDTH - card_w) // 2
    card_y = (HEIGHT - card_h) // 2 - 20
    card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
    card_surf.fill((20, 20, 50, 220))
    screen.blit(card_surf, (card_x, card_y))
    pygame.draw.rect(screen, (120, 100, 220), (card_x, card_y, card_w, card_h), 2, border_radius=10)

    title_font  = pygame.font.Font("assets/fonts/Papernotes.otf", 38)
    sub_font    = pygame.font.Font("assets/fonts/Papernotes.otf", 22)
    detail_font = pygame.font.Font("assets/fonts/Papernotes.otf", 17)
    warn_font   = pygame.font.Font("assets/fonts/Papernotes.otf", 15)

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

    pygame.draw.circle(screen, color_accent, (WIDTH // 2, card_y + 52), 26)
    pygame.draw.circle(screen, (20, 20, 50),  (WIDTH // 2, card_y + 52), 20)

    title_surf = title_font.render(title_text, True, color_accent)
    screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, card_y + 84))

    sub_surf = sub_font.render(sub_text, True, (210, 210, 255))
    screen.blit(sub_surf, (WIDTH // 2 - sub_surf.get_width() // 2, card_y + 136))

    detail_surf = detail_font.render(detail_text, True, (160, 160, 200))
    screen.blit(detail_surf, (WIDTH // 2 - detail_surf.get_width() // 2, card_y + 168))

    # Attendance warnings for finals
    blocked_courses = []
    if exam_type == "final" and course_manager is not None:
        blocked_courses = [c for c in course_manager.courses if not c.is_attendance_eligible()]

    if blocked_courses:
        warn_y = card_y + 200
        pygame.draw.line(screen, (180, 60, 60),
                         (card_x + 30, warn_y - 4), (card_x + card_w - 30, warn_y - 4), 1)
        for c in blocked_courses:
            att = c.get_attendance_percentage()
            w_surf = warn_font.render(
                f"BARRED: {c.name}  ({att:.0f}% < 85%) — will score 0", True, (255, 90, 70))
            screen.blit(w_surf, (WIDTH // 2 - w_surf.get_width() // 2, warn_y))
            warn_y += w_surf.get_height() + 3
        hint_surf = warn_font.render("Barred courses automatically score 0.", True, (130, 130, 170))
        screen.blit(hint_surf, (WIDTH // 2 - hint_surf.get_width() // 2, warn_y + 6))
    else:
        pygame.draw.line(screen, (80, 80, 140),
                         (card_x + 40, card_y + 212), (card_x + card_w - 40, card_y + 212), 1)
        hint_surf = detail_font.render("Press Continue when you're ready.", True, (130, 130, 170))
        screen.blit(hint_surf, (WIDTH // 2 - hint_surf.get_width() // 2, card_y + 226))

    continue_btn.draw(screen)


# Semester End Screen

def semester_end_screen(screen, student, avg_knowledge, quit_btn, font,
                        course_manager, scroll_y=0):
    """
    Comprehensive final-semester results page.
    Shows per-course breakdown of all quizzes, lab evals, mid & final marks,
    attendance, letter grade, and GPA.  Scrollable.
    """
    WIDTH, HEIGHT = screen.get_width(), screen.get_height()
    _draw_results_bg(screen, (100, 255, 140), (60, 200, 100))

    title_font  = pygame.font.Font("assets/fonts/Papernotes.otf", 44)
    sub_font    = pygame.font.Font("assets/fonts/Papernotes.otf", 24)
    head_font   = pygame.font.Font("assets/fonts/Papernotes.otf", 24)
    body_font   = pygame.font.Font("assets/fonts/Papernotes.otf", 20)
    detail_font = pygame.font.Font("assets/fonts/Papernotes.otf", 18)
    gpa_font    = pygame.font.Font("assets/fonts/Papernotes.otf", 48)

    # Header
    title_surf = title_font.render("Semester Complete!", True, (100, 255, 140))
    screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, 14))
    sub_surf = sub_font.render("Full Semester Summary", True, (160, 230, 180))
    screen.blit(sub_surf, (WIDTH // 2 - sub_surf.get_width() // 2, 56))

    # Scrollable content area
    content_top = 84
    strip_h     = 100
    screen.set_clip((0, content_top, WIDTH, HEIGHT - content_top - strip_h))

    card_w  = WIDTH - 60
    card_x  = 30
    cy      = content_top + 8 - int(scroll_y)
    courses = course_manager.courses

    for course in courses:
        att_blocked = not course.is_attendance_eligible()
        cy = _draw_course_card(screen, course, card_x, cy, card_w,
                               head_font, body_font, detail_font,
                               show_final=True,
                               attendance_blocked=att_blocked)

    content_height = cy + int(scroll_y) - content_top + 120
    screen.set_clip(None)

    # GPA strip at the bottom 
    strip_y = HEIGHT - strip_h
    strip_surf = pygame.Surface((WIDTH, strip_h), pygame.SRCALPHA)
    strip_surf.fill((10, 30, 20, 245))
    screen.blit(strip_surf, (0, strip_y))
    pygame.draw.line(screen, (60, 200, 100), (0, strip_y), (WIDTH, strip_y), 2)

    cgpa = course_manager.calculate_cgpa()
    cgpa_surf = gpa_font.render(f"GPA: {cgpa:.2f}", True, (120, 255, 120))
    screen.blit(cgpa_surf, (WIDTH // 2 - cgpa_surf.get_width() // 2, strip_y + 16))

    bye_surf = detail_font.render("Thanks for playing Caffeine & Chaos!", True, (90, 190, 110))
    screen.blit(bye_surf, (WIDTH // 2 - bye_surf.get_width() // 2, strip_y + 70))

    # Bottom fade
    fade = pygame.Surface((WIDTH, 70), pygame.SRCALPHA)
    for i in range(70):
        alpha = int(210 * (i / 70))
        pygame.draw.line(fade, (8, 22, 12, alpha), (0, 69 - i), (WIDTH, 69 - i))
    screen.blit(fade, (0, strip_y - 70))

    # Quit button sits in the GPA strip
    quit_btn.rect.centerx = WIDTH - 80
    quit_btn.rect.y       = strip_y + 30
    quit_btn.draw(screen)

    return content_height
