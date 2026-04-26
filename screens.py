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
        msg_box_x = 50
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
            screen.blit(msg_surface, (msg_box_x, y_offset))
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
                   sick_active=False, exam_week_label=None):
    """Draw the full day-end overlay (background + dim + summary + buttons)."""
    WIDTH, HEIGHT = screen.get_width(), screen.get_height()

    # Base game screen (behind the overlay)
    game_screen(screen, background_image, student, bars, game_buttons,
                messages, message_font, bar_space)

    # Clock before overlay so it gets dimmed with everything else
    draw_clock_fn(screen, clock_font, date_font, time_of_day, day_count, bar_space,
                  week_count=week_count, day_in_week=day_in_week,
                  exam_week_label=exam_week_label)

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
    _disp_wk = exam_week_label if exam_week_label else f"Week {week_count}"
    
    if day_in_week == 7:
        wk_label = f"{_disp_wk}, {day_name(day_in_week)} - Week Complete!"
        wk_color = (120, 255, 160)
    else:
        wk_label = f"{_disp_wk}, {day_name(day_in_week)}"
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
        if course.scheduled_quizzes:
            max_mark = 5 * course.credits
            parts = []
            for q in sorted(course.scheduled_quizzes, key=lambda q: q["quiz_number"]):
                if q["taken"] and not q["missed"] and q["mark"] is not None:
                    parts.append(f"Q{q['quiz_number']}: {q['mark'] / 100 * max_mark:.1f}/{max_mark}")
                else:
                    parts.append(f"Q{q['quiz_number']}: 0/{max_mark}")
            marks_str = "  ".join(parts)
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
            f"WARNING: {len(blocked)} course(s) below 85% attendance - Final Exam may be blocked!",
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




def post_mid_choice_screen(screen, repeat_btn, manual_btn, font):
    """
    After midterm results, ask the player whether to replay the pre-mid
    lifestyle pattern for the remaining post-mid weeks, or play manually.
    """
    WIDTH, HEIGHT = screen.get_width(), screen.get_height()

    # Dim overlay
    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 210))
    screen.blit(overlay, (0, 0))

    # Card
    card_w, card_h = 540, 280
    card_x = (WIDTH  - card_w) // 2
    card_y = (HEIGHT - card_h) // 2 - 20
    card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
    card_surf.fill((20, 20, 45, 235))
    screen.blit(card_surf, (card_x, card_y))
    pygame.draw.rect(screen, (100, 80, 220),
                     (card_x, card_y, card_w, card_h), 2, border_radius=10)

    # Title
    title_font = pygame.font.Font("assets/fonts/Papernotes.otf", 30)
    title_surf = title_font.render("Post-Midterm Plan", True, (255, 220, 80))
    screen.blit(title_surf,
                (card_x + card_w // 2 - title_surf.get_width() // 2, card_y + 24))

    # Body lines
    lines = [
        "Midterms are done. What's your plan for the rest of the semester?",
        "",
        "  Repeat Pre-Mid Style  →  automatically replays your pre-mid week",
        "  pattern (actions, hours, courses) for all remaining class weeks.",
        "  Quizzes and labs will still interrupt for you to decide.",
        "",
        "  Play Manually  →  you control every day as usual.",
    ]
    body_font = pygame.font.Font("assets/fonts/Papernotes.otf", 17)
    y = card_y + 74
    for line in lines:
        surf = body_font.render(line, True, (210, 205, 235))
        screen.blit(surf, (card_x + 20, y))
        y += surf.get_height() + 3

    repeat_btn.draw(screen)
    manual_btn.draw(screen)


# Exam Period Screens

def exam_schedule_screen(screen, exam_type: str, schedule: list, continue_btn, font) -> None:

    from environment import DAYS_OF_WEEK
    WIDTH, HEIGHT = screen.get_width(), screen.get_height()

    # Background
    bg = pygame.Surface((WIDTH, HEIGHT))
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(10 + 20 * t)
        g = int(10 + 15 * t)
        b = int(50 + 60 * t)
        pygame.draw.line(bg, (r, g, b), (0, y), (WIDTH, y))
    screen.blit(bg, (0, 0))

    is_final = (exam_type == "final")
    accent = (255, 200, 100) if is_final else (200, 160, 255)
    top_bar = (160, 120, 60)  if is_final else (100, 80, 200)
    pygame.draw.rect(screen, top_bar, (0, 0, WIDTH, 5))

    title_font = pygame.font.Font("assets/fonts/Papernotes.otf", 38)
    sub_font = pygame.font.Font("assets/fonts/Papernotes.otf", 22)
    row_font = pygame.font.Font("assets/fonts/Papernotes.otf", 20)
    detail_font = pygame.font.Font("assets/fonts/Papernotes.otf", 17)

    header_text = "Final Examination Schedule" if is_final else "Midterm Examination Schedule"
    title_surf = title_font.render(header_text, True, accent)
    screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, 18))

    if is_final:
        subtitle = "Exam Week 1 / 2 / 3  (Tuesday / Friday)"
    else:
        subtitle = "Exam Week 1 / 2  (Monday / Wednesday / Friday)"
    sub_surf = sub_font.render(subtitle, True, (180, 180, 220))
    screen.blit(sub_surf, (WIDTH // 2 - sub_surf.get_width() // 2, 62))

    # Table
    card_w = 680
    card_x = (WIDTH - card_w) // 2
    row_h = 46
    start_y = 108

    for i, entry in enumerate(schedule):
        course = entry["course"]
        week = entry["week"]
        day_idx = entry["day_idx"]
        day_str = DAYS_OF_WEEK[day_idx]

        row_y = start_y + i * row_h
        is_first = (i == 0)

        bg_col = (50, 35, 100) if is_first else ((30, 28, 60) if i % 2 == 0 else (22, 20, 48))
        border_col = accent if is_first else (60, 55, 120)

        row_rect = pygame.Rect(card_x, row_y, card_w, row_h - 4)
        pygame.draw.rect(screen, bg_col, row_rect, border_radius=6)
        pygame.draw.rect(screen, border_col, row_rect, 2, border_radius=6)

        # Course name
        name_col = accent if is_first else (220, 215, 245)
        name_surf = row_font.render(course.name, True, name_col)
        screen.blit(name_surf, (card_x + 16, row_y + (row_h - 4 - name_surf.get_height()) // 2))

        # Day + Week label
        base_wk = schedule[0]["week"]
        exam_wk_n = week - base_wk + 1
        slot_str = f"Exam Week {exam_wk_n} - {day_str}"
        slot_surf = row_font.render(slot_str, True, (160, 200, 255) if is_first else (160, 155, 200))
        screen.blit(slot_surf, (card_x + card_w - slot_surf.get_width() - 16,
                                row_y + (row_h - 4 - slot_surf.get_height()) // 2))

        if is_first:
            arrow_surf = detail_font.render("< Next", True, (120, 255, 140))
            screen.blit(arrow_surf, (card_x + card_w // 2 - arrow_surf.get_width() // 2,
                                     row_y + (row_h - 4 - arrow_surf.get_height()) // 2))

    # Continue button
    continue_btn.text = "Start Exams"
    continue_btn.rect.centerx = WIDTH // 2
    continue_btn.rect.y = HEIGHT - 68
    continue_btn.draw(screen)


def exam_prep_screen(screen, exam_entry: dict, days_until: int, exam_idx: int, total_exams: int,
                     copy_all: bool, copy_checkbox, begin_btn, font) -> None:
    
    from environment import DAYS_OF_WEEK
    WIDTH, HEIGHT = screen.get_width(), screen.get_height()

    bg = pygame.Surface((WIDTH, HEIGHT))
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(8 + 22 * t)
        g = int(8 + 14 * t)
        b = int(40 + 55 * t)
        pygame.draw.line(bg, (r, g, b), (0, y), (WIDTH, y))
    screen.blit(bg, (0, 0))
    pygame.draw.rect(screen, (80, 60, 160), (0, 0, WIDTH, 5))

    title_font = pygame.font.Font("assets/fonts/Papernotes.otf", 34)
    sub_font = pygame.font.Font("assets/fonts/Papernotes.otf", 22)
    body_font = pygame.font.Font("assets/fonts/Papernotes.otf", 19)

    # Progress
    prog_str = f"Exam {exam_idx + 1} of {total_exams}"
    prog_surf = body_font.render(prog_str, True, (140, 140, 200))
    screen.blit(prog_surf, (WIDTH // 2 - prog_surf.get_width() // 2, 18))

    course = exam_entry["course"]
    week = exam_entry["week"]
    day_idx = exam_entry["day_idx"]
    day_str = DAYS_OF_WEEK[day_idx]

    # Card
    card_w, card_h = 560, 280
    card_x = (WIDTH - card_w) // 2
    card_y = HEIGHT // 2 - card_h // 2 - 30
    card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
    card_surf.fill((20, 18, 50, 220))
    screen.blit(card_surf, (card_x, card_y))
    pygame.draw.rect(screen, (100, 80, 200), (card_x, card_y, card_w, card_h), 2, border_radius=10)

    title_surf = title_font.render(f"Next Exam: {course.name}", True, (200, 160, 255))
    screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, card_y + 22))

    # "Exam Week X" label instead of internal week number
    base_wk   = exam_entry.get("_base_week", exam_entry["week"])  # fallback
    # We don't have the schedule base easily here; just show day+week in friendly form
    exam_wk_label = f"Exam Week {exam_idx + 1}"
    date_surf = sub_font.render(f"{day_str}, {exam_wk_label}", True, (180, 220, 255))
    screen.blit(date_surf, (WIDTH // 2 - date_surf.get_width() // 2, card_y + 72))

    if days_until == 0:
        dur_text = "Exam is today!"
        dur_col = (255, 180, 60)
    elif days_until == 1:
        dur_text = "1 day until exam"
        dur_col = (200, 255, 160)
    else:
        dur_text = f"{days_until} days until exam"
        dur_col = (160, 200, 255)
    dur_surf = body_font.render(dur_text, True, dur_col)
    screen.blit(dur_surf, (WIDTH // 2 - dur_surf.get_width() // 2, card_y + 112))

    hint_surf = body_font.render("Study strategy: play each prep day normally.", True, (150, 145, 200))
    screen.blit(hint_surf, (WIDTH // 2 - hint_surf.get_width() // 2, card_y + 150))

    # Checkbox (only from exam 1 onward)
    if exam_idx >= 1 and copy_checkbox is not None:
        copy_checkbox.rect.x = WIDTH // 2 - 130
        copy_checkbox.rect.y = card_y + 196
        copy_checkbox.draw(screen)

    # Begin button
    begin_btn.text = "Begin Prep"
    begin_btn.rect.centerx = WIDTH // 2
    begin_btn.rect.y = HEIGHT - 68
    begin_btn.draw(screen)


def exam_taking_screen(screen, exam_entry: dict, exam_type: str,
                       take_btn, skip_btn, font) -> None:
    from environment import DAYS_OF_WEEK
    WIDTH, HEIGHT = screen.get_width(), screen.get_height()

    is_final = (exam_type == "final")
    accent = (255, 200, 100) if is_final else (200, 160, 255)
    top_col = (160, 120, 60) if is_final else (100, 80, 200)

    bg = pygame.Surface((WIDTH, HEIGHT))
    for y in range(HEIGHT):
        t = y / HEIGHT
        r = int(12 + 25 * t)
        g = int(8  + 10 * t)
        b = int(45 + 55 * t)
        pygame.draw.line(bg, (r, g, b), (0, y), (WIDTH, y))
    screen.blit(bg, (0, 0))
    pygame.draw.rect(screen, top_col, (0, 0, WIDTH, 5))

    title_font = pygame.font.Font("assets/fonts/Papernotes.otf", 38)
    sub_font = pygame.font.Font("assets/fonts/Papernotes.otf", 23)
    detail_font = pygame.font.Font("assets/fonts/Papernotes.otf", 18)

    exam_label = "Final Exam" if is_final else "Midterm Exam"
    course = exam_entry["course"]

    card_w, card_h = 600, 300
    card_x = (WIDTH - card_w) // 2
    card_y = HEIGHT // 2 - card_h // 2 - 20
    card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
    card_surf.fill((20, 18, 52, 220))
    screen.blit(card_surf, (card_x, card_y))
    pygame.draw.rect(screen, accent, (card_x, card_y, card_w, card_h), 2, border_radius=10)

    # Decorative circle
    pygame.draw.circle(screen, accent, (WIDTH // 2, card_y + 50), 28)
    pygame.draw.circle(screen, (20, 18, 52), (WIDTH // 2, card_y + 50), 22)

    title_text = f"{course.name} - {exam_label}"
    title_surf = title_font.render(title_text, True, accent)
    screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, card_y + 86))

    flavour = ("The exam hall falls silent. Pencils down..."
               if is_final else
               "The room is tense. You flip open the paper...")
    flav_surf = sub_font.render(flavour, True, (200, 195, 240))
    screen.blit(flav_surf, (WIDTH // 2 - flav_surf.get_width() // 2, card_y + 142))

    hint_surf = detail_font.render("Press Take Exam when you're ready.", True, (130, 125, 180))
    screen.blit(hint_surf, (WIDTH // 2 - hint_surf.get_width() // 2, card_y + 188))

    pygame.draw.line(screen, (60, 55, 120),
                     (card_x + 40, card_y + 224), (card_x + card_w - 40, card_y + 224), 1)

    take_btn.text = "Take Exam"
    take_btn.rect.centerx = WIDTH // 2 - 70
    take_btn.rect.y = HEIGHT - 68
    take_btn.draw(screen)

    skip_btn.text = "Skip"
    skip_btn.rect.centerx = WIDTH // 2 + 70
    skip_btn.rect.y = HEIGHT - 68
    skip_btn.draw(screen)



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
                        course_manager, scroll_y=0, next_btn=None):
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

    # Quit button (right side of GPA strip) — same position on both pages
    quit_btn.rect.centerx = WIDTH - 80
    quit_btn.rect.y       = strip_y + 30
    quit_btn.draw(screen)

    # Next-page button (left side of strip)
    if next_btn is not None:
        next_btn.rect.centerx = 80
        next_btn.rect.y = strip_y + 30
        next_btn.draw(screen)

    return content_height


# Semester Stats Screen (Page 2)

def semester_stats_screen(screen, student, course_manager, prev_btn, quit_btn, scroll_y=0, next_btn=None):
    """
    Second page of the semester-end screen.
    Two-column scrollable card grid of lifetime stats.
    Returns content_height for scroll clamping in the caller.
    """
    WIDTH, HEIGHT = screen.get_width(), screen.get_height()
    _draw_results_bg(screen, (100, 255, 140), (60, 200, 100))

    title_font  = pygame.font.Font("assets/fonts/Papernotes.otf", 42)
    sub_font    = pygame.font.Font("assets/fonts/Papernotes.otf", 22)
    label_font  = pygame.font.Font("assets/fonts/Papernotes.otf", 16)
    value_font  = pygame.font.Font("assets/fonts/Papernotes.otf", 22)
    sec_font    = pygame.font.Font("assets/fonts/Papernotes.otf", 18)
    detail_font = pygame.font.Font("assets/fonts/Papernotes.otf", 18)
    gpa_font    = pygame.font.Font("assets/fonts/Papernotes.otf", 48)

    # Header
    title_surf = title_font.render("Semester Stats", True, (100, 255, 140))
    screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, 10))
    sub_surf = sub_font.render("A look back at your semester", True, (160, 230, 180))
    screen.blit(sub_surf, (WIDTH // 2 - sub_surf.get_width() // 2, 52))

    # Compute assessment counts from course_manager
    quizzes_taken = sum(1 for c in course_manager.courses if c.course_type == "Theory"
                         for q in c.scheduled_quizzes if q.get("taken") and not q.get("missed"))
    quizzes_missed = sum(1 for c in course_manager.courses if c.course_type == "Theory"
                         for q in c.scheduled_quizzes if q.get("missed"))
    labs_taken = sum(1 for c in course_manager.courses if c.course_type == "Lab"
                         for la in getattr(c, "scheduled_lab_assessments", [])
                         if la.get("taken") and not la.get("missed"))
    labs_missed = sum(1 for c in course_manager.courses if c.course_type == "Lab"
                         for la in getattr(c, "scheduled_lab_assessments", [])
                         if la.get("missed"))

    s = student.stats
    attended = s["classes_attended"]
    skipped = s["classes_skipped"]
    att_rate = (attended / max(1, attended + skipped)) * 100

    # Card data 
    sections = [
        ("Time Spent", [
            ("Hours Studied", f"{s['hours_studied']:.1f} h"),
            ("Hours in Class", f"{s['hours_in_class']:.1f} h"),
            ("Hours Slept", f"{s['hours_slept']:.1f} h"),
            ("Hours Relaxed", f"{s['hours_relaxed']:.1f} h"),
            ("Hours Without WiFi", f"{s['hours_wifi_outage']:.1f} h"),
        ]),
        ("Health Events", [
            ("Times Fallen Sick", str(s["times_sick"])),
            ("Total Sick Days", str(s["total_sick_days"])),
            ("Longest Sick Streak", f"{s['longest_sick_streak']} day(s)"),
            ("Burnout Episodes", str(s["burnout_occurrences"])),
            ("Days Burnt Out", str(s["days_burnt_out"])),
        ]),
        ("Daily Life", [
            ("Coffees Drunk", str(s["coffees_drunk"])),
            ("Meals Eaten", str(s["meals_eaten"])),
            ("Classes Attended", str(attended)),
            ("Classes Skipped", str(skipped)),
            ("Attendance Rate", f"{att_rate:.0f}%"),
        ]),
        ("Assessments", [
            ("Quizzes Taken", str(quizzes_taken)),
            ("Quizzes Missed", str(quizzes_missed)),
            ("Lab Assessments Taken", str(labs_taken)),
            ("Lab Assessments Missed", str(labs_missed)),
        ]),
        ("Peak Stats", [
            ("Peak Stress", f"{s['peak_stress']:.0f} / 100"),
            ("Lowest Health", f"{s['lowest_health']:.0f} / 100"),
            ("Peak Motivation", f"{s['peak_motivation']:.0f} / 100"),
        ]),
    ]

    # Layout
    content_top = 84
    strip_h = 100
    clip_h = HEIGHT - content_top - strip_h

    COL_GAP = 20
    COL_W = (WIDTH - 60 - COL_GAP) // 2
    left_x = 30
    right_x = left_x + COL_W + COL_GAP

    CARD_PAD = 10
    CARD_GAP = 8
    SEC_H = sec_font.get_height() + 6
    ROW_H = max(label_font.get_height(), value_font.get_height()) + 6

    def _card_height(rows):
        return CARD_PAD + SEC_H + len(rows) * ROW_H + CARD_PAD

    def _draw_card(cx, cy, cw, sec_title, rows):
        """Draw one stat card; cy is the already-scrolled canvas y."""
        card_h = _card_height(rows)
        card_surf = pygame.Surface((cw, card_h), pygame.SRCALPHA)
        card_surf.fill((18, 30, 22, 215))
        screen.blit(card_surf, (cx, cy))
        pygame.draw.rect(screen, (60, 200, 100), (cx, cy, cw, card_h), 2, border_radius=8)

        sec_surf = sec_font.render(sec_title, True, (100, 230, 140))
        screen.blit(sec_surf, (cx + CARD_PAD, cy + CARD_PAD))
        ry = cy + CARD_PAD + SEC_H

        for lbl, val in rows:
            lbl_surf = label_font.render(lbl + ":", True, (140, 190, 155))
            val_surf = value_font.render(val, True, (220, 245, 225))
            screen.blit(lbl_surf, (cx + CARD_PAD,
                                   ry + (ROW_H - lbl_surf.get_height()) // 2))
            screen.blit(val_surf, (cx + cw - CARD_PAD - val_surf.get_width(),
                                   ry + (ROW_H - val_surf.get_height()) // 2))
            ry += ROW_H

        return cy + card_h + CARD_GAP

    # Distribute: left col = sections 0,1,2 ; right col = sections 3,4
    left_secs = sections[:3]
    right_secs = sections[3:]

    # Measure the taller column to derive total content height
    left_h = sum(_card_height(s[1]) + CARD_GAP for s in left_secs)
    right_h = sum(_card_height(s[1]) + CARD_GAP for s in right_secs)
    content_height = max(left_h, right_h) + 120   
    # Scrollable clip region
    screen.set_clip((0, content_top, WIDTH, clip_h))

    start_y = content_top + 8 - int(scroll_y)

    ly = start_y
    for sec in left_secs:
        ly = _draw_card(left_x, ly, COL_W, sec[0], sec[1])

    ry_pos = start_y
    for sec in right_secs:
        ry_pos = _draw_card(right_x, ry_pos, COL_W, sec[0], sec[1])

    # Footer fade (matches results page)
    fade_h = 90
    fade = pygame.Surface((WIDTH, fade_h), pygame.SRCALPHA)
    for i in range(fade_h):
        alpha = int(200 * (i / fade_h))
        pygame.draw.line(fade, (8, 8, 35, alpha), (0, fade_h - 1 - i), (WIDTH, fade_h - 1 - i))
    screen.blit(fade, (0, HEIGHT - fade_h))

    screen.set_clip(None)

    # Bottom strip — same dimensions as semester_end_screen 
    strip_y = HEIGHT - strip_h
    strip_surf = pygame.Surface((WIDTH, strip_h), pygame.SRCALPHA)
    strip_surf.fill((10, 30, 20, 245))
    screen.blit(strip_surf, (0, strip_y))
    pygame.draw.line(screen, (60, 200, 100), (0, strip_y), (WIDTH, strip_y), 2)

    hint_surf = detail_font.render("How did your semester treat you?", True, (90, 190, 110))
    screen.blit(hint_surf, (WIDTH // 2 - hint_surf.get_width() // 2, strip_y + 16))

    # "Results" on the left
    prev_btn.rect.centerx = 80
    prev_btn.rect.y = strip_y + 30
    prev_btn.draw(screen)
    
    if next_btn is not None:
        next_btn.rect.centerx = 80 + 120
        next_btn.rect.y = strip_y + 30
        next_btn.draw(screen)

    # Quit on the right — identical to page 0
    quit_btn.rect.centerx = WIDTH - 80
    quit_btn.rect.y = strip_y + 30
    quit_btn.draw(screen)

    return content_height


def compute_optimal_path(student, course_manager) -> dict:
    """ Computes the retrospective optimal study path based on actual semester execution. """
    from courses import Course

    target_cgpa = student.target_cgpa
    if target_cgpa <= 0:
        return {} # No target set

    # Find uniform required percentage across courses to hit target CGPA
    # Grade jumps at 40, 45, 50, 55, 60, 65, 70, 75, 80
    test_pcts = [40, 45, 50, 55, 60, 65, 70, 75, 80]
    target_pct = 80.0
    for p in test_pcts:
        if Course._percentage_to_grade_point(p) >= target_cgpa:
            target_pct = float(p)
            break

    # Use end-of-semester stats
    s = student.stats
    sleep = student.sleep
    health = student.health
    stress = student.stress
    motivation = student.motivation

    # Compute global efficiency
    avg_knowledge = course_manager.get_average_knowledge()
    efficiency = (sleep + health + (100 - stress) + (100 - motivation) + avg_knowledge) / 500.0

    optimal_data = {
        "target_cgpa": target_cgpa,
        "achieved_cgpa": course_manager.calculate_cgpa(),
        "courses": [],
        "actual_study": s.get("hours_studied", 0.0)
    }

    total_optimal_study = 0.0
    
    for c in course_manager.courses:
        # Expected knowledge
        expected_knowledge = 10.0 + (c.occurred_classes / max(1, c.total_classes)) * 90.0 if c.total_classes > 0 else 100.0
        req_k = Course.required_knowledge_for_pct(target_pct, sleep, health, stress, expected_knowledge, course_type=c.course_type)
        
        actual_k = c.knowledge
        gap_k = req_k - actual_k
        
        # Invert learning: gain = hours * study_knowledge_rate * efficiency * knowledge_mult
        study_knowledge_rate = 0.8 * student.type_mult
        if gap_k > 0:
            optimal_hours = gap_k / max(0.001, (study_knowledge_rate * efficiency))
        else:
            optimal_hours = 0.0
            
        optimal_data["courses"].append({
            "name": c.name,
            "required_knowledge": req_k,
            "actual_knowledge": actual_k,
            "gap_knowledge": gap_k,
            "optimal_hours": optimal_hours,
            "attendance_blocked": not c.is_attendance_eligible()
        })
        
        total_optimal_study += optimal_hours

    optimal_data["total_optimal_study"] = total_optimal_study
    semester_study_days = 105 - s.get("total_sick_days", 0) - s.get("days_burnt_out", 0)
    if semester_study_days > 0:
        optimal_data["optimal_study_per_day"] = total_optimal_study / semester_study_days
        actual_study_hours = s.get("hours_studied", 0.0)
        optimal_data["actual_study_per_day"] = actual_study_hours / semester_study_days
        optimal_data["gap_per_day"] = optimal_data["optimal_study_per_day"] - optimal_data["actual_study_per_day"]
        optimal_data["lost_days"] = s.get("total_sick_days", 0) + s.get("days_burnt_out", 0)
        optimal_data["total_days"] = semester_study_days
        
        theoretical_daily_max = 24.0
        optimal_data["theoretical_daily_max"] = 12 # heuristics
    else:
        optimal_data["optimal_study_per_day"] = 0
        optimal_data["actual_study_per_day"] = 0
        optimal_data["gap_per_day"] = 0
        optimal_data["lost_days"] = 0
        optimal_data["theoretical_daily_max"] = 24

    return optimal_data


def semester_optimal_screen(screen, optimal_data, prev_btn, quit_btn, scroll_y=0):
    WIDTH, HEIGHT = screen.get_width(), screen.get_height()
    _draw_results_bg(screen, (10, 20, 30), (30, 50, 70))

    title_font = pygame.font.Font("assets/fonts/Papernotes.otf", 42)
    sub_font = pygame.font.Font("assets/fonts/Papernotes.otf", 22)
    label_font = pygame.font.Font("assets/fonts/Papernotes.otf", 18)
    value_font = pygame.font.Font("assets/fonts/Papernotes.otf", 22)
    detail_font = pygame.font.Font("assets/fonts/Papernotes.otf", 18)

    # Header
    title_surf = title_font.render("Your Optimal Path", True, (100, 200, 255))
    screen.blit(title_surf, (WIDTH // 2 - title_surf.get_width() // 2, 10))
    sub_surf = sub_font.render("Based on your student profile and actual semester", True, (160, 200, 230))
    screen.blit(sub_surf, (WIDTH // 2 - sub_surf.get_width() // 2, 52))
    
    if not optimal_data:
        err_surf = title_font.render("No Target CGPA Set.", True, (255, 100, 100))
        screen.blit(err_surf, (WIDTH // 2 - err_surf.get_width() // 2, HEIGHT // 2))
        return HEIGHT

    # Top summary
    tgt_cgpa = optimal_data["target_cgpa"]
    ach_cgpa = optimal_data["achieved_cgpa"]
    gap_cgpa = ach_cgpa - tgt_cgpa
    
    sum_str = f"Target CGPA: {tgt_cgpa:.2f}    Achieved: {ach_cgpa:.2f}    Gap: {gap_cgpa:+.2f}"
    sum_surf = value_font.render(sum_str, True, (255,255,255))
    screen.blit(sum_surf, (WIDTH // 2 - sum_surf.get_width() // 2, 85))

    # Single most actionable number
    opt_pd = optimal_data["optimal_study_per_day"]
    act_pd = optimal_data["actual_study_per_day"]
    tot_opt = optimal_data["total_optimal_study"]
    act_tot = optimal_data.get("actual_study", 0.0)
    gap_tot = tot_opt - act_tot
    
    col = (255,255,100) if gap_tot > 0 else (100,255,100)
    act_text1 = f"You needed ~{opt_pd:.1f} hrs of focused study per day."
    act_text2 = f"You averaged {act_pd:.1f} hrs. Gap: {gap_tot:+.1f} hours over the semester."
    
    at_surf1 = value_font.render(act_text1, True, col)
    screen.blit(at_surf1, (WIDTH // 2 - at_surf1.get_width() // 2, 120))
    at_surf2 = detail_font.render(act_text2, True, (220,220,240))
    screen.blit(at_surf2, (WIDTH // 2 - at_surf2.get_width() // 2, 150))
    
    content_top = 180
    strip_h = 100
    clip_h = HEIGHT - content_top - strip_h
    
    screen.set_clip((0, content_top, WIDTH, clip_h))
    
    cw = WIDTH - 60
    cx = 30
    cy = content_top + 10 - int(scroll_y)
    
    CARD_PAD = 12
    for c in optimal_data["courses"]:
        card_h = 105
        card_surf = pygame.Surface((cw, card_h), pygame.SRCALPHA)
        card_surf.fill((20, 20, 40, 215))
        screen.blit(card_surf, (cx, cy))
        
        bcol = (255,100,100) if c["attendance_blocked"] else (100, 160, 255)
        pygame.draw.rect(screen, bcol, (cx, cy, cw, card_h), 2, border_radius=8)
        
        name_surf = value_font.render(c["name"], True, (200, 230, 255))
        screen.blit(name_surf, (cx + CARD_PAD, cy + CARD_PAD))
        
        if c["attendance_blocked"]:
            bsurf = detail_font.render("LIMITING FACTOR: ATTENDANCE BLOCKED", True, (255, 100, 100))
            screen.blit(bsurf, (cx + cw - CARD_PAD - bsurf.get_width(), cy + CARD_PAD))
            
        rk = c["required_knowledge"]
        ak = c["actual_knowledge"]
        gk = c["gap_knowledge"]
        oh = c["optimal_hours"]
        
        str1 = f"Knowledge to hit target: {rk:.1f}%    Actual: {ak:.1f}%    Gap: {gk:+.1f}%"
        s1 = label_font.render(str1, True, (200, 200, 200))
        screen.blit(s1, (cx + CARD_PAD, cy + 45))
        
        str2 = f"Optimal Study Time Required: {oh:.1f} hrs (Total this Semester)"
        scol = (150, 255, 150) if oh <= act_pd else (255, 200, 150)
        s2 = label_font.render(str2, True, scol)
        screen.blit(s2, (cx + CARD_PAD, cy + 70))
        
        cy += card_h + 10
        
    if optimal_data.get("lost_days", 0) > 0:
        ls_surf = detail_font.render(f"Note: You lost {optimal_data['lost_days']} study days to illness/burnout.", True, (255, 150, 150))
        screen.blit(ls_surf, (cx + CARD_PAD, cy))
        cy += 30

    if optimal_data["optimal_study_per_day"] > optimal_data["theoretical_daily_max"]:
        fw_surf = detail_font.render("Warning: Target may have been out of reach for your stats. (Required > Max Daily)", True, (255, 100, 100))
        screen.blit(fw_surf, (cx + CARD_PAD, cy))
        cy += 30
        
    content_height = cy + int(scroll_y) - content_top + 160
    screen.set_clip(None)

    # Bottom strip — same dimensions as semester_end_screen 
    strip_y = HEIGHT - strip_h
    strip_surf = pygame.Surface((WIDTH, strip_h), pygame.SRCALPHA)
    strip_surf.fill((10, 30, 40, 245))
    screen.blit(strip_surf, (0, strip_y))
    pygame.draw.line(screen, (100, 200, 255), (0, strip_y), (WIDTH, strip_y), 2)

    prev_btn.rect.centerx = 80
    prev_btn.rect.y = strip_y + 30
    prev_btn.draw(screen)

    # Quit on the right — identical to other pages
    quit_btn.rect.centerx = WIDTH - 80
    quit_btn.rect.y = strip_y + 30
    quit_btn.draw(screen)

    return content_height