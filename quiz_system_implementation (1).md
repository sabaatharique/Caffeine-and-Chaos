# Quiz System — Full Implementation Guide
### Caffeine & Chaos

---

## Overview

This document covers every line you need to add or change across four files:

| File | What changes |
|---|---|
| `courses.py` | Store quiz schedule on `Course`; add `schedule_all_quizzes()` to `CourseManager` |
| `ui.py` | `QuizResultBox` (interrupt popup) + `AcademicDashboard` (attendance + quiz panel) |
| `main.py` | State variables, quiz trigger loop, button wiring, dashboard toggle |
| `savegame.py` | Serialize / deserialize quiz schedules and resolved-today set |

The design deliberately leaves **mark entry** as a stub (`quiz["mark"] = None`) so you can wire a grade-entry screen later without touching the core scheduling logic.

---

## 1. `courses.py`

### 1a. Add fields to `Course.__init__`

Find the block that starts with `# Theory` and add one line directly above it:

```python
# Quizzes  ← ADD THIS WHOLE BLOCK
self.scheduled_quizzes: list[dict] = []
# Each entry (created by CourseManager.schedule_all_quizzes):
# {
#   "week":    int,   # 1-15
#   "day_idx": int,   # 0=Mon … 4=Fri
#   "slot_idx":int,   # index into SLOT_TIMES
#   "taken":   bool,  # True once the interrupt fires
#   "missed":  bool,  # True if player was sick when it fired
#   "mark":    None,  # reserved for later grade-entry
# }
```

Nothing else in `Course` needs to change right now.

---

### 1b. Add `schedule_all_quizzes()` to `CourseManager`

Paste this method anywhere inside `CourseManager` (after `apply_schedule` is a natural spot):

```python
# ── Quiz scheduling ────────────────────────────────────────────────────────

# Weighted probability per week for each quiz window.
# Index 0 = first week of the window.
_PRE_MID_WEIGHTS  = [1, 1, 2, 4, 5, 5, 4]   # weeks 1-7
_POST_MID_WEIGHTS = [1, 1, 2, 4, 5, 5, 4, 3] # weeks 8-15

def schedule_all_quizzes(self):
    """
    Assign 2 pre-midterm + 2 post-midterm quiz dates to every theory course.
    Call this ONCE after apply_schedule() so that weekly_slots are populated.

    Each quiz lands on one of the course's own class slots so it fires
    exactly when the player would normally be in lecture.
    """
    import random

    for course in self.courses:
        if course.course_type != "Theory":
            continue
        if not course.weekly_slots:
            continue  # shouldn't happen, but be safe

        course.scheduled_quizzes = []
        used: set[tuple[int, int]] = set()  # (week, day_idx) → no double-booking

        def _pick(week_pool: list[int], weights: list[int]) -> dict | None:
            """
            Attempt up to 30 times to find a unique (week, day_idx) slot.
            Returns a quiz dict or None if every attempt collides.
            """
            for _ in range(30):
                week = random.choices(week_pool, weights=weights[:len(week_pool)], k=1)[0]
                day_idx, slot_idx = random.choice(course.weekly_slots)
                key = (week, day_idx)
                if key not in used:
                    used.add(key)
                    return {
                        "week":     week,
                        "day_idx":  day_idx,
                        "slot_idx": slot_idx,
                        "taken":    False,
                        "missed":   False,
                        "mark":     None,   # filled later when grade-entry is added
                    }
            return None  # extremely unlikely

        # 2 quizzes before mid (weeks 1-7)
        pre_weeks = list(range(1, 8))
        for _ in range(2):
            q = _pick(pre_weeks, self._PRE_MID_WEIGHTS)
            if q:
                course.scheduled_quizzes.append(q)

        # 2 quizzes after mid (weeks 8-15)
        post_weeks = list(range(8, 16))
        for _ in range(2):
            q = _pick(post_weeks, self._POST_MID_WEIGHTS)
            if q:
                course.scheduled_quizzes.append(q)

        # Sort chronologically for the dashboard
        course.scheduled_quizzes.sort(key=lambda q: (q["week"], q["day_idx"]))
```

> **When to call it:** In `main.py`, immediately after `course_manager.apply_schedule(schedule)` inside the wizard-complete block. Also call it after `load_game()` only if `scheduled_quizzes` is empty on every theory course (i.e. the save pre-dates this feature).

---

## 2. `ui.py`

Paste both classes anywhere after `AlertBox` (or at the end of the file).

---

### 2a. `QuizResultBox` — the interrupt popup

```python
class QuizResultBox:
    """
    Shown immediately when a scheduled quiz fires.
    Displays course name, the auto-generated mark, and a grade band label.
    The player dismisses it with Enter or by clicking the card.
    """

    # ── Theme colours (match existing ui.py palette) ──
    _CARD_BG      = (30, 30, 50, 230)
    _BORDER       = (120, 100, 200)
    _TEXT_WHITE   = (236, 240, 241)
    _TEXT_SUBTEXT = (180, 180, 220)
    _GRADE_COLORS = {          # keyed by letter grade
        "A":  (100, 255, 140),
        "B":  (120, 210, 255),
        "C":  (255, 220, 80),
        "D":  (255, 150, 60),
        "F":  (231, 76, 60),
    }

    def __init__(self, screen_w: int, screen_h: int):
        self.screen_w  = screen_w
        self.screen_h  = screen_h
        self.active    = False
        self._course   = None
        self._mark     = 0.0
        self._missed   = False  # True when the quiz fired but player was sick
        # Fonts are loaded lazily on first open (avoids pygame init order issues)
        self._title_font  = None
        self._body_font   = None
        self._hint_font   = None

    # ── public API ────────────────────────────────────────────────────────

    def open(self, course, mark: float, missed: bool = False):
        self._course = course
        self._mark   = mark
        self._missed = missed
        self.active  = True
        self._load_fonts()

    def close(self):
        self.active = False

    def handle_event(self, event) -> bool:
        """Return True if the box consumed the event."""
        if not self.active:
            return False
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE,
                                                           pygame.K_ESCAPE):
            self.close()
            return True
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.close()
            return True
        return False

    def draw(self, screen):
        if not self.active:
            return

        # ── dim the background ──
        overlay = pygame.Surface((self.screen_w, self.screen_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # ── card ──
        card_w, card_h = 460, 220
        card_x = (self.screen_w - card_w) // 2
        card_y = (self.screen_h - card_h) // 2

        card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        card_surf.fill(self._CARD_BG)
        screen.blit(card_surf, (card_x, card_y))
        pygame.draw.rect(screen, self._BORDER, (card_x, card_y, card_w, card_h), 2, border_radius=10)

        # ── accent bar at top ──
        accent = self._grade_color() if not self._missed else (255, 80, 80)
        pygame.draw.rect(screen, accent, (card_x, card_y, card_w, 5), border_radius=10)

        y = card_y + 18

        # ── title ──
        if self._missed:
            title_text = f"QUIZ MISSED  —  {self._course.name}"
        else:
            title_text = f"QUIZ RESULT  —  {self._course.name}"
        title_surf = self._title_font.render(title_text, True, self._TEXT_WHITE)
        screen.blit(title_surf, (card_x + card_w // 2 - title_surf.get_width() // 2, y))
        y += title_surf.get_height() + 10

        # ── divider ──
        pygame.draw.line(screen, (80, 80, 140),
                         (card_x + 30, y), (card_x + card_w - 30, y), 1)
        y += 14

        if self._missed:
            # Sick message
            sick_surf = self._body_font.render(
                "You were sick and could not sit the quiz.", True, (255, 130, 130))
            screen.blit(sick_surf,
                        (card_x + card_w // 2 - sick_surf.get_width() // 2, y))
            y += sick_surf.get_height() + 6
            note_surf = self._hint_font.render(
                "A mark of 0 has been recorded for this attempt.",
                True, (200, 160, 160))
            screen.blit(note_surf,
                        (card_x + card_w // 2 - note_surf.get_width() // 2, y))
        else:
            # Mark + grade band
            grade_letter = self._grade_letter()
            grade_color  = self._grade_color()

            mark_surf = self._title_font.render(
                f"{self._mark:.1f} / 100", True, grade_color)
            screen.blit(mark_surf,
                        (card_x + card_w // 2 - mark_surf.get_width() // 2, y))
            y += mark_surf.get_height() + 6

            band_surf = self._body_font.render(
                f"Grade Band: {grade_letter}  —  {self._band_label()}",
                True, grade_color)
            screen.blit(band_surf,
                        (card_x + card_w // 2 - band_surf.get_width() // 2, y))

        # ── dismiss hint ──
        hint_surf = self._hint_font.render(
            "Press Enter or click anywhere to continue.", True, (130, 130, 170))
        screen.blit(hint_surf,
                    (card_x + card_w // 2 - hint_surf.get_width() // 2,
                     card_y + card_h - hint_surf.get_height() - 12))

    # ── private helpers ───────────────────────────────────────────────────

    def _load_fonts(self):
        if self._title_font is None:
            self._title_font = pygame.font.Font("assets/fonts/Papernotes.otf", 26)
            self._body_font  = pygame.font.Font("assets/fonts/Papernotes.otf", 20)
            self._hint_font  = pygame.font.Font("assets/fonts/Papernotes.otf", 16)

    def _grade_letter(self) -> str:
        m = self._mark
        if m >= 80: return "A"
        if m >= 70: return "B"
        if m >= 60: return "C"
        if m >= 50: return "D"
        return "F"

    def _grade_color(self):
        return self._GRADE_COLORS[self._grade_letter()]

    def _band_label(self) -> str:
        m = self._mark
        if m >= 80: return "Excellent"
        if m >= 70: return "Good"
        if m >= 60: return "Average"
        if m >= 50: return "Passing"
        return "Failing"
```

---

### 2b. `AcademicDashboard` — attendance + upcoming quizzes panel

This is a toggleable overlay that fits the game's right sidebar.  
It renders inside the same `GAME_SCREEN` draw pass — no new screen state needed.

```python
class AcademicDashboard:
    """
    Toggleable panel shown over the game screen.
    Top half:    Attendance for EVERY course (theory + lab), coloured by %.
    Bottom half: Upcoming (untaken) quizzes for theory courses, sorted
                 chronologically and colour-coded by urgency.

    Usage:
        dashboard = AcademicDashboard(screen_w, screen_h, font, small_font)
        dashboard.toggle()          # from a button click
        dashboard.draw(screen, course_manager, week_count)
        dashboard.handle_event(event)   # closes on Escape / backdrop click
    """

    # ── Theme ──────────────────────────────────────────────────────────────
    _BG           = (20, 20, 40, 235)
    _BORDER       = (120, 100, 200)
    _HEADER_BG    = (40, 30, 70, 255)
    _ROW_ALT      = (30, 30, 55, 200)
    _TEXT_WHITE   = (236, 240, 241)
    _TEXT_DIM     = (160, 160, 200)
    _DIVIDER      = (70, 60, 120)

    # Attendance colour thresholds
    _ATT_GOOD    = (46, 204, 113)    # ≥ 75 %
    _ATT_WARN    = (255, 200, 60)    # 50-74 %
    _ATT_BAD     = (231, 76, 60)     # < 50 %

    # Quiz urgency colours
    _QUIZ_THIS   = (231, 76, 60)     # this week
    _QUIZ_NEXT   = (255, 200, 60)    # next week
    _QUIZ_FUTURE = (100, 200, 255)   # later

    def __init__(self, screen_w: int, screen_h: int, font, small_font):
        self.screen_w   = screen_w
        self.screen_h   = screen_h
        self.font       = font        # your existing message_font-sized font
        self.small_font = small_font  # smaller font for dense rows
        self.visible    = False
        self._title_font = None       # loaded lazily

        # Panel geometry
        self._pw = 340          # panel width
        self._ph = screen_h - 80
        self._px = screen_w - self._pw - 10   # flush to right side
        self._py = 40

    # ── public API ────────────────────────────────────────────────────────

    def toggle(self):
        self.visible = not self.visible

    def show(self):
        self.visible = True

    def hide(self):
        self.visible = False

    def handle_event(self, event) -> bool:
        """Return True if the dashboard consumed the event."""
        if not self.visible:
            return False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.hide()
            return True
        # Click outside the panel → close
        if event.type == pygame.MOUSEBUTTONDOWN:
            panel_rect = pygame.Rect(self._px, self._py, self._pw, self._ph)
            if not panel_rect.collidepoint(event.pos):
                self.hide()
                return True
        return False

    def draw(self, screen, course_manager, week_count: int):
        if not self.visible:
            return
        self._load_fonts()

        # ── backdrop panel ──
        surf = pygame.Surface((self._pw, self._ph), pygame.SRCALPHA)
        surf.fill(self._BG)
        screen.blit(surf, (self._px, self._py))
        pygame.draw.rect(screen, self._BORDER,
                         (self._px, self._py, self._pw, self._ph), 2, border_radius=8)

        y = self._py + 8
        x = self._px

        # ════════════════════════════════════
        #  SECTION 1 — ATTENDANCE
        # ════════════════════════════════════
        y = self._draw_section_header(screen, "  📋  Attendance", x, y)

        courses = course_manager.courses
        if not courses:
            y = self._draw_dim(screen, "  No courses enrolled.", x, y)
        else:
            for i, course in enumerate(courses):
                pct = course.get_attendance_percentage()
                att_color = (
                    self._ATT_GOOD if pct >= 75 else
                    self._ATT_WARN if pct >= 50 else
                    self._ATT_BAD
                )

                # Alternating row tint
                if i % 2 == 0:
                    row_surf = pygame.Surface((self._pw - 4, 28), pygame.SRCALPHA)
                    row_surf.fill(self._ROW_ALT)
                    screen.blit(row_surf, (x + 2, y))

                # Course name (truncated to fit)
                name = self._truncate(course.name, 18)
                name_surf = self.small_font.render(name, True, self._TEXT_WHITE)
                screen.blit(name_surf, (x + 8, y + 4))

                # Attendance % right-aligned
                pct_text = f"{pct:.0f}%  ({course.attended_classes}/{course.total_classes})"
                pct_surf  = self.small_font.render(pct_text, True, att_color)
                screen.blit(pct_surf,
                            (x + self._pw - pct_surf.get_width() - 10, y + 4))

                # Thin mini-bar below the row
                bar_y = y + 24
                bar_w = self._pw - 20
                pygame.draw.rect(screen, (44, 62, 80),
                                 (x + 10, bar_y, bar_w, 3), border_radius=2)
                fill = int(bar_w * min(pct, 100) / 100)
                if fill > 0:
                    pygame.draw.rect(screen, att_color,
                                     (x + 10, bar_y, fill, 3), border_radius=2)

                y += 30

        y += 6
        pygame.draw.line(screen, self._DIVIDER,
                         (x + 10, y), (x + self._pw - 10, y), 1)
        y += 8

        # ════════════════════════════════════
        #  SECTION 2 — UPCOMING QUIZZES
        # ════════════════════════════════════
        y = self._draw_section_header(screen, "  📝  Upcoming Quizzes", x, y)

        # Collect all untaken quizzes across theory courses
        upcoming = []
        for course in courses:
            if course.course_type != "Theory":
                continue
            for quiz in course.scheduled_quizzes:
                if not quiz["taken"]:
                    upcoming.append((quiz["week"], quiz["day_idx"],
                                     quiz["slot_idx"], course.name))
        upcoming.sort()  # chronological

        if not upcoming:
            y = self._draw_dim(screen, "  No upcoming quizzes.", x, y)
        else:
            from environment import SLOT_TIMES, DAYS_OF_WEEK, format_time
            for i, (wk, d_idx, s_idx, cname) in enumerate(upcoming):
                # Stop drawing if we're about to overflow the panel
                if y + 40 > self._py + self._ph - 20:
                    remaining = len(upcoming) - i
                    y = self._draw_dim(screen, f"  … +{remaining} more", x, y)
                    break

                weeks_away = wk - week_count
                quiz_color = (
                    self._QUIZ_THIS   if weeks_away <= 0 else
                    self._QUIZ_NEXT   if weeks_away == 1 else
                    self._QUIZ_FUTURE
                )
                urgency_label = (
                    "THIS WEEK" if weeks_away <= 0 else
                    "NEXT WEEK" if weeks_away == 1 else
                    f"Week {wk}"
                )

                # Row background
                if i % 2 == 0:
                    row_surf = pygame.Surface((self._pw - 4, 36), pygame.SRCALPHA)
                    row_surf.fill(self._ROW_ALT)
                    screen.blit(row_surf, (x + 2, y))

                # Left: urgency badge + weekday
                day_name_short = DAYS_OF_WEEK[d_idx][:3]
                start_h, _ = SLOT_TIMES[s_idx]
                time_str = format_time(start_h)
                badge_surf = self.small_font.render(
                    f"[{urgency_label}]", True, quiz_color)
                screen.blit(badge_surf, (x + 8, y + 2))

                day_surf = self.small_font.render(
                    f"{day_name_short}  {time_str}", True, self._TEXT_DIM)
                screen.blit(day_surf, (x + 8, y + 20))

                # Right: course name
                cname_short = self._truncate(cname, 14)
                cname_surf = self.small_font.render(cname_short, True, self._TEXT_WHITE)
                screen.blit(cname_surf,
                            (x + self._pw - cname_surf.get_width() - 10, y + 10))

                y += 40

        # ── close hint ──
        hint = self.small_font.render("Press Esc or click outside to close",
                                      True, (100, 100, 140))
        screen.blit(hint, (x + self._pw // 2 - hint.get_width() // 2,
                            self._py + self._ph - 20))

    # ── private helpers ───────────────────────────────────────────────────

    def _load_fonts(self):
        if self._title_font is None:
            self._title_font = pygame.font.Font("assets/fonts/Papernotes.otf", 20)

    def _draw_section_header(self, screen, text: str, x: int, y: int) -> int:
        """Draw a tinted section header. Returns new y."""
        hdr_surf = pygame.Surface((self._pw, 28), pygame.SRCALPHA)
        hdr_surf.fill(self._HEADER_BG)
        screen.blit(hdr_surf, (x, y))
        label = self._title_font.render(text, True, (200, 180, 255))
        screen.blit(label, (x + 4, y + 4))
        return y + 32

    def _draw_dim(self, screen, text: str, x: int, y: int) -> int:
        """Draw a dimmed single line. Returns new y."""
        surf = self.small_font.render(text, True, self._TEXT_DIM)
        screen.blit(surf, (x + 8, y))
        return y + 24

    @staticmethod
    def _truncate(s: str, max_chars: int) -> str:
        return s if len(s) <= max_chars else s[:max_chars - 1] + "…"
```

---

## 3. `main.py`

### 3a. Import — no changes needed

`QuizResultBox` and `AcademicDashboard` just go into `ui.py`; your existing import line handles them:

```python
from ui import (StatusBar, Button, InputBox, NumberBox, AlertBox,
                SetupWizard, ScheduleBuilder, ClassInterruptBox,
                QuizResultBox, AcademicDashboard)   # ← add these two
```

---

### 3b. State variables — add near the top with your other init vars

```python
# ── Quiz interrupt state ───────────────────────────────────────────────────
_quizzes_resolved_today: set = set()
# Each element is a tuple: (course_name, week, day_idx)
# Reset every time day_count increments, the same way _classes_resolved is reset.
```

---

### 3c. Instantiate UI components — in your UI setup section

Find where you create `class_interrupt_box` and add right below:

```python
quiz_result_box = QuizResultBox(WIDTH, HEIGHT)
academic_dashboard = AcademicDashboard(
    WIDTH, HEIGHT,
    message_font,   # use your existing message_font
    date_font,      # use your existing date_font as the small font
)
```

Add a toggle button to your game buttons list (position to taste):

```python
dashboard_btn = Button(
    x=bar_space + 10,   # left side, below Knowledge bar — adjust as needed
    y=580,
    w=130, h=30,
    text="📋 Courses",
    font=date_font,
)
# Append to game_buttons so it draws automatically via game_screen():
game_buttons.append(dashboard_btn)
```

---

### 3d. Call `schedule_all_quizzes()` after wizard completes

Find the block in your wizard-complete handler that calls `apply_schedule`:

```python
# EXISTING:
course_manager.apply_schedule(schedule)

# ADD directly after:
course_manager.schedule_all_quizzes()
```

Also add a guard in your `load_game` block so old saves without quizzes get them generated:

```python
# After load_game() succeeds:
for c in course_manager.courses:
    if c.course_type == "Theory" and not c.scheduled_quizzes:
        # Old save — generate quizzes now
        course_manager.schedule_all_quizzes()
        break
```

---

### 3e. Reset quiz resolved set when the day changes

Find the block where you reset `_classes_resolved` at day rollover and add:

```python
# Existing (something like):
_classes_resolved.clear()

# Add alongside it:
_quizzes_resolved_today.clear()
```

---

### 3f. Quiz interrupt trigger loop

Add this block in the main game loop, **after** the existing class interrupt block and **before** the draw section. Mirror the structure of the class interrupt block exactly:

```python
# ── Quiz interrupt trigger (GAME_SCREEN, weekdays only) ─────────────────
if (current_screen_state == GAME_SCREEN
        and not day_over
        and not class_interrupt_box.active   # don't stack interrupts
        and not quiz_result_box.active
        and not alert_box.active
        and not input_box.active
        and day_in_week <= 5):               # no quizzes on weekends

    for course in course_manager.courses:
        if course.course_type != "Theory":
            continue
        for quiz in course.scheduled_quizzes:
            if quiz["taken"]:
                continue

            key = (course.name, quiz["week"], quiz["day_idx"])
            if key in _quizzes_resolved_today:
                continue

            # Does this quiz match today?
            if quiz["week"] != week_count:
                continue
            if quiz["day_idx"] != (day_in_week - 1):   # day_idx is 0-based
                continue

            # Has the clock reached the quiz slot?
            from environment import SLOT_TIMES
            start_h, end_h = SLOT_TIMES[quiz["slot_idx"]]

            if time_of_day < start_h:
                continue    # slot hasn't started yet

            # ── Quiz fires ──
            _quizzes_resolved_today.add(key)
            quiz["taken"] = True

            if student.is_sick:
                # Sick → automatic miss, mark 0
                quiz["missed"] = True
                quiz["mark"]   = 0.0
                course.quiz_marks.append(0.0)
                messages.append(f"[QUIZ] {course.name} — MISSED (sick). Mark: 0.")
                quiz_result_box.open(course, 0.0, missed=True)
            else:
                # Generate mark via existing Course method
                course.generate_quiz_mark(
                    stress=student.stress,
                    sleep=student.sleep / 100.0,
                    health=student.health,
                )
                mark = course.quiz_marks[-1] if course.quiz_marks else 0.0
                quiz["mark"] = mark
                messages.append(f"[QUIZ] {course.name}: {mark:.1f}/100!")
                quiz_result_box.open(course, mark, missed=False)

            messages = messages[-5:]   # keep message list tidy
            break   # only one quiz popup at a time
```

---

### 3g. Handle `QuizResultBox` events

In your event loop, inside `for event in pygame.event.get()`, add **before** the class_interrupt_box handler:

```python
# Quiz result box dismissal
if quiz_result_box.handle_event(event):
    continue    # event consumed; don't pass to buttons below

# Dashboard toggle
if dashboard_btn.clicked(event):
    academic_dashboard.toggle()

# Dashboard backdrop / Escape
if academic_dashboard.handle_event(event):
    continue
```

---

### 3h. Draw `QuizResultBox` and `AcademicDashboard`

Inside the `elif current_screen_state == GAME_SCREEN:` draw block, add at the very end (so they render on top of everything):

```python
# Draw academic dashboard (behind quiz popup)
academic_dashboard.draw(screen, course_manager, week_count)

# Draw quiz result popup (topmost)
quiz_result_box.draw(screen)
```

---

### 3i. Replay runners — quiz handling

Inside `ReplayRunner.tick()` and `WeekReplayRunner.tick()`, when an `attend_class` action fires you need to also check quizzes. Add this helper call after the action runs:

```python
# After processing each action in tick():
# Auto-resolve any quiz that falls within this action's time window
# (During replay, quizzes just auto-fire with no popup)
for c in self.course_manager.courses:
    if c.course_type != "Theory":
        continue
    for quiz in c.scheduled_quizzes:
        if quiz["taken"]:
            continue
        # Match week + day — use replay runner's own counters
        if quiz["week"] != self.current_week:
            continue
        if quiz["day_idx"] != (self.current_day_in_week - 1):
            continue
        start_h, _ = SLOT_TIMES[quiz["slot_idx"]]
        if self.time_cursor >= start_h:
            quiz["taken"] = True
            if self.student.is_sick:
                quiz["missed"] = True
                quiz["mark"]   = 0.0
                c.quiz_marks.append(0.0)
            else:
                c.generate_quiz_mark(
                    stress=self.student.stress,
                    sleep=self.student.sleep / 100.0,
                    health=self.student.health,
                )
                if c.quiz_marks:
                    quiz["mark"] = c.quiz_marks[-1]
```

> `SLOT_TIMES` needs to be imported at the top of `main.py` — it already is via `from environment import ...`.

---

## 4. `savegame.py`

### 4a. `_course_to_dict` — add one line

```python
def _course_to_dict(course) -> dict:
    return {
        # ... all existing keys ...
        "weekly_slots": [list(s) for s in course.weekly_slots],
        "scheduled_quizzes": course.scheduled_quizzes,   # ← ADD THIS
        # already JSON-safe: list of dicts with only int/bool/None values
    }
```

### 4b. `_courses_from_dict` — restore quizzes

After `c.weekly_slots = [tuple(s) for s in d.get("weekly_slots", [])]`, add:

```python
c.scheduled_quizzes = d.get("scheduled_quizzes", [])
```

### 4c. `save_game` — persist resolved-today set

Add `quizzes_resolved_today` as a parameter and persist it:

```python
def save_game(student, course_manager,
              time_of_day, day_count, week_count, day_in_week,
              burnout_active, day_over,
              day_actions: list, week_actions: list,
              classes_resolved: set = None,
              attend_all_today: bool = False,
              quizzes_resolved_today: set = None) -> bool:   # ← ADD param

    payload = {
        # ... existing keys ...
        "quizzes_resolved_today": [
            list(k) for k in quizzes_resolved_today
        ] if quizzes_resolved_today else [],                 # ← ADD
    }
```

### 4d. `load_game` — restore resolved-today set

In the `return` dict:

```python
return {
    # ... existing keys ...
    "quizzes_resolved_today": set(
        tuple(k) for k in data.get("quizzes_resolved_today", [])
    ),   # ← ADD
}
```

In `main.py` where you unpack `load_game`'s return dict:

```python
_quizzes_resolved_today = saved.get("quizzes_resolved_today", set())
```

---

## 5. Adding grade entry later

When you're ready to let the player manually enter quiz marks (e.g. after results are announced), you only need to:

1. Add a `GradeEntryBox` (similar style to `InputBox`) that iterates `course.scheduled_quizzes` and presents each `quiz["mark"]` as an editable field.
2. Replace `quiz["mark"]` with the entered value.
3. Call `course.quiz_marks[i] = new_mark` for the corresponding index.

The `"mark": None` placeholder in every quiz dict is the hook — `None` means "auto-generated", any `float` means "overridden". You can use this distinction in `calculate_total_marks()` if you want manually-entered marks to take precedence.

---

## 6. Quick integration checklist

```
[ ] courses.py — add scheduled_quizzes list to Course.__init__
[ ] courses.py — add schedule_all_quizzes() to CourseManager
[ ] ui.py      — paste QuizResultBox class
[ ] ui.py      — paste AcademicDashboard class
[ ] main.py    — update import line
[ ] main.py    — add _quizzes_resolved_today state variable
[ ] main.py    — instantiate quiz_result_box and academic_dashboard
[ ] main.py    — add dashboard_btn to game_buttons
[ ] main.py    — call schedule_all_quizzes() after apply_schedule()
[ ] main.py    — add old-save guard after load_game()
[ ] main.py    — clear _quizzes_resolved_today at day rollover
[ ] main.py    — add quiz trigger loop (after class interrupt block)
[ ] main.py    — handle quiz_result_box events in event loop
[ ] main.py    — handle dashboard_btn clicks + dashboard events
[ ] main.py    — draw dashboard + quiz_result_box in GAME_SCREEN draw block
[ ] main.py    — add quiz auto-fire inside ReplayRunner.tick()
[ ] savegame.py — add scheduled_quizzes to _course_to_dict
[ ] savegame.py — restore scheduled_quizzes in _courses_from_dict
[ ] savegame.py — add quizzes_resolved_today to save_game / load_game
[ ] main.py    — pass _quizzes_resolved_today to save_game call
```
