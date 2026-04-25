# Implementation Plan: Post-Mid Lifestyle Repeat + Stats Bar Trends

---

## Table of Contents

1. [Feature 1 — Post-Midterm Pre-Mid Lifestyle Repeat](#feature-1)
   - [Overview & Design](#f1-overview)
   - [Phase A — Save the Pre-Mid Week Template](#phase-a)
   - [Phase B — New Screen State & UI Buttons](#phase-b)
   - [Phase C — New `post_mid_choice_screen()` in `screens.py`](#phase-c)
   - [Phase D — Wire Everything in `main.py`](#phase-d)
   - [Phase E — Save/Load Support in `savegame.py`](#phase-e)
2. [Feature 2 — Stats Bar Trends Section](#feature-2)
   - [Overview & Design](#f2-overview)
   - [Phase A — Add Weekly Snapshot Tracking to `student.py`](#f2-phase-a)
   - [Phase B — Update `savegame.py` for New Fields](#f2-phase-b)
   - [Phase C — Update `week_count` Tracking in `main.py`](#f2-phase-c)
   - [Phase D — Add `_draw_trends_section()` to `StatsDashboard` in `ui.py`](#f2-phase-d)
   - [Phase E — Update `StatsDashboard.draw()` Signature](#f2-phase-e)
   - [Phase F — Update All `stats_dashboard.draw()` Call Sites in `main.py`](#f2-phase-f)
3. [Complete Code Blocks](#complete-code-blocks)

---

## Feature 1 — Post-Midterm Pre-Mid Lifestyle Repeat {#feature-1}

### Overview & Design {#f1-overview}

**Goal:** After the midterm results screen, ask the player: "Repeat your pre-mid lifestyle for the remaining post-mid weeks, or play manually?"

- If **Repeat** → automatically create a `WeekReplayRunner` using the saved pre-mid week template and replay it for weeks 8–15 (8 weeks). This works exactly the same as "Repeat Week" — same runner, same quiz/lab interrupts, same burnout detection — but it's triggered automatically post-midterm.
- If **Manual** → current behavior (go directly to `GAME_SCREEN` at day 50).

**How the existing replay already works (recap):**

`WeekReplayRunner` receives:
- `week_actions`: list of up to 7 day-action-lists (one per day Mon–Sun)
- `n_weeks`: how many weeks to replay
- `start_day`: the day_count at the moment replay begins
- `start_week`: the week_count at the moment replay begins (runner starts on `start_week + 1`)

It replays the same daily action patterns for `n_weeks` additional weeks, firing quiz/lab interrupts, detecting burnout, and stopping before exam weeks automatically.

**Key insight:** We need to capture `week_actions` (the last full pre-mid week) before the midterm exam period clears it. This is saved as `_pre_mid_week_template`.

---

### Phase A — Save the Pre-Mid Week Template {#phase-a}

**File: `main.py`**

**Step A1:** Add a new module-level variable near the other replay state variables (around line 50):

```python
# Saved at end of pre-mid period; used for post-mid lifestyle repeat
_pre_mid_week_template: list = []
```

**Step A2:** Save the template at the exact moment the pre-mid period ends.

There are **two code paths** that end pre-mid:

**Path 1 — Player used Repeat Week** (the `WeekReplayRunner` finishes at week 7).

Find the block around line 1926–1942 inside:
```python
if week_replay_runner.done and not week_replay_runner.burnout_occurred:
    if week_count == 7 and _exam_period_type == "":
        ...
        current_screen_state = EXAM_SCREEN
```

Right before `current_screen_state = EXAM_SCREEN`, add:

```python
# Save the pre-mid template for post-mid lifestyle repeat
_pre_mid_week_template[:] = [list(d) for d in week_replay_runner.week_actions]
```

**Path 2 — Player played manually** (clicked "Continue" on day-end each day, then on week 7 Friday the `repeat_week_btn` wasn't used).

The week-7-Friday → EXAM_SCREEN transition happens in the `GAME_SCREEN` event handling. Find around line 1610–1670 the block that detects `week_count == 7` and the end of Friday (day 49), just before it fires `EXAM_SCREEN`. It looks like:

```python
if week_count == 7 and day_in_week == 5 and ...:
    course_manager.generate_midterm_schedule()
    ...
    current_screen_state = EXAM_SCREEN
```

Immediately **before** `current_screen_state = EXAM_SCREEN` in this manual path, add:

```python
# Save pre-mid template (week 7 pattern, padded to 7 days)
_full_week = list(week_actions) + [list(day_actions)]
while len(_full_week) < 7:
    _full_week.append([])
_pre_mid_week_template[:] = [list(d) for d in _full_week]
```

> **Note:** `week_actions` accumulates previous days of the current week; `day_actions` is today's (Friday's) completed actions. Together they form the full week template.

---

### Phase B — New Screen State & UI Buttons {#phase-b}

**File: `main.py`**

**Step B1:** Add the new screen state constant near the other states (around line 620):

```python
POST_MID_CHOICE_SCREEN = "post_mid_choice_screen"
```

**Step B2:** Add two new buttons near the other button declarations (around line 750). Place them so they are centred on screen:

```python
# Post-mid lifestyle choice buttons
_pm_btn_y  = HEIGHT // 2 + 80
_pm_btn_w  = 180
_pm_gap    = 40
post_mid_repeat_btn = Button(
    WIDTH // 2 - _pm_btn_w - _pm_gap // 2, _pm_btn_y,
    _pm_btn_w, 44, "Repeat Pre-Mid Style", button_font
)
post_mid_manual_btn = Button(
    WIDTH // 2 + _pm_gap // 2, _pm_btn_y,
    _pm_btn_w, 44, "Play Manually", button_font
)
```

---

### Phase C — New `post_mid_choice_screen()` in `screens.py` {#phase-c}

**File: `screens.py`**

Add this function anywhere after the existing screen functions (e.g., after `midterm_results_screen`):

```python
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
```

---

### Phase D — Wire Everything in `main.py` {#phase-d}

**File: `main.py`**

**Step D1: Import the new screen function.**

At the top where screens are imported (around line 13–14), add `post_mid_choice_screen`:

```python
from screens import (main_menu, game_screen, day_end_screen, save_prompt_screen,
                     exam_screen, midterm_results_screen, semester_end_screen,
                     semester_stats_screen,
                     exam_schedule_screen, exam_prep_screen,
                     exam_taking_screen,
                     post_mid_choice_screen)          # ← add this
```

**Step D2: Change the MIDTERM_RESULTS_SCREEN "Continue" handler.**

Find (around line 1786–1803):

```python
elif current_screen_state == MIDTERM_RESULTS_SCREEN:
    if exam_continue_btn.clicked(event):
        # Return to game for the post-midterm half — resume at Monday morning, Week 8
        day_count = 50       # Day 50 = Week 8 Monday
        ...
        current_screen_state = GAME_SCREEN
```

Replace the entire block with:

```python
elif current_screen_state == MIDTERM_RESULTS_SCREEN:
    if exam_continue_btn.clicked(event):
        # Reset time/state — same as before
        day_count   = 50
        time_of_day = 8.0
        day_over    = False
        current_game_bg = bg_map['default']
        daily_outages = wifi_failure_event()
        todays_classes.clear()
        _classes_resolved.clear()
        _quizzes_resolved_today.clear()
        _lab_assessments_resolved_today.clear()
        class_interrupt_box.attend_all = False
        _exam_period_type = ""
        _exam_idx = 0
        _exam_schedule.clear()
        # Go to choice screen only if we have a template to replay
        if _pre_mid_week_template:
            current_screen_state = POST_MID_CHOICE_SCREEN
        else:
            current_screen_state = GAME_SCREEN

elif current_screen_state == POST_MID_CHOICE_SCREEN:
    if post_mid_repeat_btn.clicked(event):
        # Build a WeekReplayRunner using the saved pre-mid template
        # start_day=49 so the runner increments to day 50 (week 8 Monday)
        # start_week=7 so the runner replays week 8 first
        week_replay_runner = WeekReplayRunner(
            student, course_manager,
            [list(d) for d in _pre_mid_week_template],
            n_weeks=8,           # weeks 8–15 = 8 weeks
            start_day=49,
            start_week=7
        )
        # Reset week_actions to match the template (for Repeat Week button later)
        week_actions.clear()
        week_actions.extend([list(d) for d in _pre_mid_week_template])
        # Start the runner: check for assessments in week 8 first
        assessments = week_replay_runner.get_next_week_assessments()
        if assessments:
            week_replay_runner.quiz_week_pending = True
            week_replay_runner.msgs.append(
                f"Week {week_replay_runner.current_week} begins but has assessments scheduled."
            )
            quiz_week_prompt_box.open(week_replay_runner.current_week, assessments)
        else:
            week_replay_runner._start_new_day()
            week_replay_runner.msgs.append(
                f"Week {week_replay_runner.current_week} begins (pre-mid style replay)."
            )
        messages = [f"Replaying pre-mid lifestyle for weeks 8–15..."]
        current_screen_state = DAY_END_SCREEN

    elif post_mid_manual_btn.clicked(event):
        # Normal manual play
        week_actions.clear()
        day_actions.clear()
        messages = [f"Week 8 — Monday begins!"]
        current_screen_state = GAME_SCREEN
```

**Step D3: Add the render call for `POST_MID_CHOICE_SCREEN`.**

Find the bottom rendering section (around line 2083+) where each screen state has a render block. Add after the `MIDTERM_RESULTS_SCREEN` block:

```python
elif current_screen_state == POST_MID_CHOICE_SCREEN:
    # Render last game background as the backdrop, then overlay the choice card
    avg_k = course_manager.get_average_knowledge()
    game_screen(screen, current_game_bg, student, bars, game_buttons,
                messages, message_font, bar_space)
    bars[0].draw(screen, avg_k)
    post_mid_choice_screen(screen, post_mid_repeat_btn, post_mid_manual_btn, message_font)
```

---

### Phase E — Save/Load Support in `savegame.py` {#phase-e}

**File: `savegame.py`**

**Step E1: Save `_pre_mid_week_template`.**

In `save_game()`, add the key to the `payload` dict (alongside `exam_prep_actions`):

```python
"pre_mid_week_template": [_actions_to_serialisable(d) for d in (pre_mid_week_template or [])],
```

Update the `save_game` signature to accept it:

```python
def save_game(student, course_manager,
              time_of_day, day_count, week_count, day_in_week,
              burnout_active, day_over,
              day_actions: list, week_actions: list,
              classes_resolved: set = None,
              quizzes_resolved: set = None,
              attend_all_today: bool = False,
              exam_period_type: str = "",
              exam_idx: int = 0,
              exam_copy_to_all: bool = False,
              exam_prep_actions: list = None,
              pre_mid_week_template: list = None) -> bool:   # ← new param
```

**Step E2: Load `_pre_mid_week_template`.**

In `load_game()`, after restoring `exam_prep_actions`, add:

```python
pre_mid_week_template = [
    _actions_from_serialisable(d, course_manager)
    for d in data.get("pre_mid_week_template", [])
]
```

And include it in the returned dict:

```python
return {
    ...
    "pre_mid_week_template": pre_mid_week_template,
}
```

**Step E3: Update all `save_game()` call sites in `main.py`.**

Search for every `save_game(` call in `main.py` and add `pre_mid_week_template=_pre_mid_week_template` as a keyword argument.

---

## Feature 2 — Stats Bar Trends Section {#feature-2}

### Overview & Design {#f2-overview}

**Goal:** Add a new **TRENDS** section at the top of the `StatsDashboard` left panel showing:

1. **Stress trend this week** — ↑ or ↓ arrow with numeric delta
2. **Health trend this week** — ↑ or ↓ arrow with numeric delta
3. **Motivation trend** — ↑ or ↓ arrow with numeric delta
4. **Best day this week** — the day label with lowest stress and highest study hours
5. **Mini stacked bar chart** — proportional: Study / Sleep / Relax / Class hours this week

**Data architecture:**

- Add per-day snapshot lists to `Student`: `_week_stress_snapshots`, `_week_health_snapshots`, `_week_motivation_snapshots` — reset each week, one entry appended each `end_of_day()`.
- Add per-day activity hours lists to `Student`: `_week_study_hours`, `_week_sleep_hours`, `_week_relax_hours`, `_week_class_hours` — also reset each week, appended during each day's actions.
- Pass the current `week_count` to `stats_dashboard.draw()` so the panel knows when the week changes and can reset snapshots.

**Trend arrow logic:**
- Compare `snapshot[-1]` vs `snapshot[0]` (last vs earliest reading this week).
- `↑` = increased, `↓` = decreased, `–` = unchanged.
- For Stress: ↑ is bad (red), ↓ is good (green).
- For Health/Motivation: ↑ is good (green), ↓ is bad (red).

**Best day logic:**
Score each recorded day: `score = study_hours[i] * 2 - stress_snapshots[i]`. The day with the highest score is the "best day". Display it as e.g. "Wednesday (Day 3)".

**Stacked bar chart:**
A single horizontal bar (full panel width) divided into colour-coded segments. Segments: Study (cyan), Sleep (green), Relax (purple), Class (amber). Labels appear below each segment if wide enough. Total height: 18 px.

---

### Phase A — Add Weekly Snapshot Tracking to `student.py` {#f2-phase-a}

**File: `student.py`**

**Step A1:** Add new tracking lists to `Student.__init__()` after the existing `_health_history` lines (~line 40):

```python
# Weekly snapshots (reset at start of each week, one entry per day)
self._week_stress_snapshots:     list[float] = []
self._week_health_snapshots:     list[float] = []
self._week_motivation_snapshots: list[float] = []

# Weekly activity hours (reset at start of each week, appended during each action)
self._week_study_hours:  list[float] = []  # per-day total
self._week_sleep_hours:  list[float] = []
self._week_relax_hours:  list[float] = []
self._week_class_hours:  list[float] = []

# Today's accumulators (reset at end_of_day, used to build weekly lists)
self._today_study_hours: float = 0.0
self._today_sleep_hours: float = 0.0
self._today_relax_hours: float = 0.0
self._today_class_hours: float = 0.0

# Track which week's data the snapshots belong to
self._snapshot_week: int = 0
```

**Step A2:** Accumulate today's hours in each action method. Add to the `study()` method (after the existing `self.stats["hours_studied"] += ...` line):

```python
self._today_study_hours += hours
```

Add to the `rest()` method:

```python
self._today_sleep_hours += hours
```

Add to the `take_break()` method:

```python
self._today_relax_hours += hours
```

Add to the `attend_class()` method (the line that logs attendance, after `self.stats["hours_in_class"] += ...`):

```python
self._today_class_hours += 1.25   # each class slot = 75 min = 1.25 h
```

**Step A3:** Append snapshots at end of day in `end_of_day()` (around line 192). Add these lines **before** the existing `self._stress_history.append(self.stress)` block:

```python
# Append to weekly snapshots
self._week_stress_snapshots.append(self.stress)
self._week_health_snapshots.append(self.health)
self._week_motivation_snapshots.append(self.motivation)
self._week_study_hours.append(self._today_study_hours)
self._week_sleep_hours.append(self._today_sleep_hours)
self._week_relax_hours.append(self._today_relax_hours)
self._week_class_hours.append(self._today_class_hours)
# Reset today's accumulators
self._today_study_hours = 0.0
self._today_sleep_hours = 0.0
self._today_relax_hours = 0.0
self._today_class_hours = 0.0
```

**Step A4:** Add a `reset_week_snapshots()` method to `Student` (add it near `end_of_day`):

```python
def reset_week_snapshots(self):
    """Call at the start of each new week to clear per-week trend data."""
    self._week_stress_snapshots.clear()
    self._week_health_snapshots.clear()
    self._week_motivation_snapshots.clear()
    self._week_study_hours.clear()
    self._week_sleep_hours.clear()
    self._week_relax_hours.clear()
    self._week_class_hours.clear()
    self._today_study_hours = 0.0
    self._today_sleep_hours = 0.0
    self._today_relax_hours = 0.0
    self._today_class_hours = 0.0
```

---

### Phase B — Update `savegame.py` for New Fields {#f2-phase-b}

**File: `savegame.py`**

**Step B1:** In `_student_to_dict()`, add the new fields:

```python
"week_stress_snapshots":     student._week_stress_snapshots,
"week_health_snapshots":     student._week_health_snapshots,
"week_motivation_snapshots": student._week_motivation_snapshots,
"week_study_hours":          student._week_study_hours,
"week_sleep_hours":          student._week_sleep_hours,
"week_relax_hours":          student._week_relax_hours,
"week_class_hours":          student._week_class_hours,
"today_study_hours":         student._today_study_hours,
"today_sleep_hours":         student._today_sleep_hours,
"today_relax_hours":         student._today_relax_hours,
"today_class_hours":         student._today_class_hours,
"snapshot_week":             student._snapshot_week,
```

**Step B2:** In `_student_from_dict()`, restore the new fields:

```python
student._week_stress_snapshots     = data.get("week_stress_snapshots", [])
student._week_health_snapshots     = data.get("week_health_snapshots", [])
student._week_motivation_snapshots = data.get("week_motivation_snapshots", [])
student._week_study_hours          = data.get("week_study_hours", [])
student._week_sleep_hours          = data.get("week_sleep_hours", [])
student._week_relax_hours          = data.get("week_relax_hours", [])
student._week_class_hours          = data.get("week_class_hours", [])
student._today_study_hours         = data.get("today_study_hours", 0.0)
student._today_sleep_hours         = data.get("today_sleep_hours", 0.0)
student._today_relax_hours         = data.get("today_relax_hours", 0.0)
student._today_class_hours         = data.get("today_class_hours", 0.0)
student._snapshot_week             = data.get("snapshot_week", 0)
```

---

### Phase C — Update `week_count` Tracking in `main.py` {#f2-phase-c}

**File: `main.py`**

Call `student.reset_week_snapshots()` whenever `week_count` increases. There are several places in `main.py` where a new week starts:

1. **Manual continue (day-end):** Around line 1581–1596, when `day_in_week == 7` (end of week), add:
   ```python
   if day_in_week == 7:
       week_actions.clear()
       student.reset_week_snapshots()   # ← add this line
   ```

2. **After Repeat Day runner completes a day that crosses a week boundary** (around line 1868–1875):
   ```python
   if day_count != prev_day:
       new_diy = ((day_count - 1) % 7) + 1
       if new_diy == 1:
           week_actions.clear()
           student.reset_week_snapshots()   # ← add
   ```

3. **After Week Replay Runner finishes a week** — in `WeekReplayRunner._start_new_week()` we cannot call `student.reset_week_snapshots()` directly since the runner doesn't own the reset. Instead, detect the week boundary in the main loop where `week_count` syncs from the runner:
   ```python
   # In the week runner tick block, after syncing week_count:
   prev_week = week_count
   week_count  = week_replay_runner.current_week
   if week_count != prev_week:
       student.reset_week_snapshots()
   ```
   Make sure to save `prev_week` before updating.

4. **On return from Midterm/Exam period** (around line 1789, after MIDTERM_RESULTS_SCREEN continue):
   ```python
   student.reset_week_snapshots()
   ```

---

### Phase D — Add `_draw_trends_section()` to `StatsDashboard` in `ui.py` {#f2-phase-d}

**File: `ui.py`**

Add the following new method to the `StatsDashboard` class, right after `_draw_time_section()`:

```python
def _draw_trends_section(self, screen, student, week_count,
                         x: int, w: int, y: int, alpha: int) -> int:
    """Draw the TRENDS section: stat arrows, best day, and a mini stacked bar."""
    y = self._draw_section(screen, "THIS WEEK'S TRENDS", x, w, y, alpha)

    stress_snap = student._week_stress_snapshots
    health_snap = student._week_health_snapshots
    motiv_snap  = student._week_motivation_snapshots

    def _trend(snap: list, higher_is_better: bool):
        """Return (arrow_str, delta_str, color) for a snapshot list."""
        if len(snap) < 2:
            return "–", "n/a", self._C_DIM
        delta = snap[-1] - snap[0]
        if abs(delta) < 1.0:
            return "–", f"{delta:+.0f}", self._C_DIM
        if higher_is_better:
            arrow = "↑" if delta > 0 else "↓"
            color = self._C_GOOD if delta > 0 else self._C_BAD
        else:
            arrow = "↑" if delta > 0 else "↓"
            color = self._C_BAD if delta > 0 else self._C_GOOD
        return arrow, f"{delta:+.0f}", color

    # -- Stress / Health / Motivation trends --
    for label, snap, higher_good in [
        ("Stress",     stress_snap, False),
        ("Health",     health_snap, True),
        ("Motivation", motiv_snap,  True),
    ]:
        arrow, delta_str, color = _trend(snap, higher_good)
        lbl_surf = self._f_body.render(
            f"{label}", True, self._alpha_color(self._C_TEXT, alpha))
        val_surf = self._f_body.render(
            f"{arrow} {delta_str}", True, self._alpha_color(color, alpha))
        screen.blit(lbl_surf, (x, y))
        screen.blit(val_surf, (x + w - val_surf.get_width(), y))
        y += lbl_surf.get_height() + 5

    # -- Best day this week --
    y += 4
    best_day_surf = self._f_body.render(
        "Best Day", True, self._alpha_color(self._C_LIFESTYLE, alpha))
    screen.blit(best_day_surf, (x, y))

    study_h = student._week_study_hours
    best_label = "–"
    if study_h and stress_snap:
        from environment import DAYS_OF_WEEK
        scores = [
            study_h[i] * 2 - stress_snap[i]
            for i in range(min(len(study_h), len(stress_snap)))
        ]
        best_idx = scores.index(max(scores))
        best_label = DAYS_OF_WEEK[best_idx % 7][:3]  # e.g. "Mon"

    best_val_surf = self._f_body.render(
        best_label, True, self._alpha_color(self._C_GOOD, alpha))
    screen.blit(best_val_surf, (x + w - best_val_surf.get_width(), y))
    y += best_day_surf.get_height() + 8

    # -- Mini stacked bar chart (Study | Sleep | Relax | Class) --
    study_total = sum(student._week_study_hours)  if student._week_study_hours  else 0.0
    sleep_total = sum(student._week_sleep_hours)  if student._week_sleep_hours  else 0.0
    relax_total = sum(student._week_relax_hours)  if student._week_relax_hours  else 0.0
    class_total = sum(student._week_class_hours)  if student._week_class_hours  else 0.0
    grand_total = study_total + sleep_total + relax_total + class_total

    segments = [
        ("Study", study_total, self._C_TIME),
        ("Sleep", sleep_total, self._C_GOOD),
        ("Relax", relax_total, self._C_RECORDS),
        ("Class", class_total, self._C_WARN),
    ]

    bar_h = 14
    if grand_total > 0:
        bar_surf = pygame.Surface((w, bar_h), pygame.SRCALPHA)
        bar_surf.fill((*self._C_DIVIDER, alpha))
        cursor_x = 0
        for seg_label, seg_h, seg_color in segments:
            seg_w = int(w * seg_h / grand_total)
            if seg_w > 0:
                pygame.draw.rect(bar_surf, (*seg_color, alpha),
                                 (cursor_x, 0, seg_w, bar_h))
                cursor_x += seg_w
        screen.blit(bar_surf, (x, y))
    else:
        empty_surf = pygame.Surface((w, bar_h), pygame.SRCALPHA)
        empty_surf.fill((*self._C_DIVIDER, alpha))
        screen.blit(empty_surf, (x, y))
    y += bar_h + 3

    # Labels below the bar
    lbl_x = x
    lbl_y = y
    for seg_label, seg_h, seg_color in segments:
        seg_txt = f"{seg_label} {seg_h:.1f}h"
        seg_surf = self._f_detail.render(
            seg_txt, True, self._alpha_color(seg_color, alpha))
        # Wrap to next line if overflows
        if lbl_x + seg_surf.get_width() > x + w:
            lbl_x = x
            lbl_y += seg_surf.get_height() + 2
        screen.blit(seg_surf, (lbl_x, lbl_y))
        lbl_x += seg_surf.get_width() + 8
    y = lbl_y + self._f_detail.get_height() + 8

    return y
```

---

### Phase E — Update `StatsDashboard.draw()` Signature {#f2-phase-e}

**File: `ui.py`**

Change the `draw()` method signature from:

```python
def draw(self, screen, student, day_count: int):
```

to:

```python
def draw(self, screen, student, day_count: int, week_count: int = 0):
```

Inside `draw()`, add a call to the new trends section **before** the existing time section. Change the draw sequence in `draw()` from:

```python
y = self._draw_time_section(screen, student, day_count, ...)
y = self._draw_divider(...)
y = self._draw_academic_section(...)
...
```

to:

```python
y = self._draw_trends_section(screen, student, week_count,
                               content_x, content_w, y, content_alpha)
y = self._draw_divider(screen, content_x, content_w, y, content_alpha)
y = self._draw_time_section(screen, student, day_count,
                             content_x, content_w, y, content_alpha)
y = self._draw_divider(screen, content_x, content_w, y, content_alpha)
y = self._draw_academic_section(screen, student, day_count,
                                 content_x, content_w, y, content_alpha)
y = self._draw_divider(screen, content_x, content_w, y, content_alpha)
y = self._draw_wellness_section(screen, student,
                                 content_x, content_w, y, content_alpha)
y = self._draw_divider(screen, content_x, content_w, y, content_alpha)
y = self._draw_lifestyle_section(screen, student, day_count,
                                  content_x, content_w, y, content_alpha)
y = self._draw_divider(screen, content_x, content_w, y, content_alpha)
y = self._draw_records_section(screen, student,
                                content_x, content_w, y, content_alpha)
```

---

### Phase F — Update All `stats_dashboard.draw()` Call Sites in `main.py` {#f2-phase-f}

**File: `main.py`**

Search for every occurrence of `stats_dashboard.draw(screen, student, day_count)` and add `week_count=week_count`:

```python
stats_dashboard.draw(screen, student, day_count, week_count=week_count)
```

There are **4 call sites** total (in `GAME_SCREEN`, `DAY_END_SCREEN`, and the two `_last_game_screen` fallback blocks around line 2056–2080). Update all four.

---

## Complete Code Blocks (Copy-Paste Ready) {#complete-code-blocks}

### `student.py` — `reset_week_snapshots()` method (full, paste after `end_of_day`)

```python
def reset_week_snapshots(self):
    """Call at the start of each new week to clear per-week trend data."""
    self._week_stress_snapshots.clear()
    self._week_health_snapshots.clear()
    self._week_motivation_snapshots.clear()
    self._week_study_hours.clear()
    self._week_sleep_hours.clear()
    self._week_relax_hours.clear()
    self._week_class_hours.clear()
    self._today_study_hours = 0.0
    self._today_sleep_hours = 0.0
    self._today_relax_hours = 0.0
    self._today_class_hours = 0.0
```

### `main.py` — New module-level variables (add near line 50)

```python
_pre_mid_week_template: list = []   # snapshot of week_actions at end of pre-mid period
```

### `main.py` — Post-mid choice screen state constant (add near line 620)

```python
POST_MID_CHOICE_SCREEN = "post_mid_choice_screen"
```

### `main.py` — New buttons (add near line 750)

```python
_pm_btn_y = HEIGHT // 2 + 80
_pm_btn_w = 180
_pm_gap   = 40
post_mid_repeat_btn = Button(
    WIDTH // 2 - _pm_btn_w - _pm_gap // 2, _pm_btn_y,
    _pm_btn_w, 44, "Repeat Pre-Mid Style", button_font
)
post_mid_manual_btn = Button(
    WIDTH // 2 + _pm_gap // 2, _pm_btn_y,
    _pm_btn_w, 44, "Play Manually", button_font
)
```

### `main.py` — Render block for POST_MID_CHOICE_SCREEN (add in bottom render section)

```python
elif current_screen_state == POST_MID_CHOICE_SCREEN:
    avg_k = course_manager.get_average_knowledge()
    game_screen(screen, current_game_bg, student, bars, game_buttons,
                messages, message_font, bar_space)
    bars[0].draw(screen, avg_k)
    post_mid_choice_screen(screen, post_mid_repeat_btn, post_mid_manual_btn, message_font)
```

### `screens.py` — Full `post_mid_choice_screen()` function

```python
def post_mid_choice_screen(screen, repeat_btn, manual_btn, font):
    """After midterm results, ask player to replay pre-mid lifestyle or play manually."""
    WIDTH, HEIGHT = screen.get_width(), screen.get_height()

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 210))
    screen.blit(overlay, (0, 0))

    card_w, card_h = 540, 280
    card_x = (WIDTH  - card_w) // 2
    card_y = (HEIGHT - card_h) // 2 - 20
    card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
    card_surf.fill((20, 20, 45, 235))
    screen.blit(card_surf, (card_x, card_y))
    pygame.draw.rect(screen, (100, 80, 220),
                     (card_x, card_y, card_w, card_h), 2, border_radius=10)

    title_font = pygame.font.Font("assets/fonts/Papernotes.otf", 30)
    title_surf = title_font.render("Post-Midterm Plan", True, (255, 220, 80))
    screen.blit(title_surf,
                (card_x + card_w // 2 - title_surf.get_width() // 2, card_y + 24))

    lines = [
        "Midterms are done. What's your plan for the rest of the semester?",
        "",
        "  Repeat Pre-Mid Style  ->  automatically replays your pre-mid week",
        "  pattern (actions, hours, courses) for all remaining class weeks.",
        "  Quizzes and labs will still interrupt for you to decide.",
        "",
        "  Play Manually  ->  you control every day as usual.",
    ]
    body_font = pygame.font.Font("assets/fonts/Papernotes.otf", 17)
    y = card_y + 74
    for line in lines:
        surf = body_font.render(line, True, (210, 205, 235))
        screen.blit(surf, (card_x + 20, y))
        y += surf.get_height() + 3

    repeat_btn.draw(screen)
    manual_btn.draw(screen)
```

---

## Summary Checklist

### Feature 1 — Post-Mid Repeat

- [ ] `main.py`: Add `_pre_mid_week_template = []` module variable
- [ ] `main.py`: Add `POST_MID_CHOICE_SCREEN` constant
- [ ] `main.py`: Add `post_mid_repeat_btn` and `post_mid_manual_btn` buttons
- [ ] `main.py`: Save template at week 7 end (both week-replay and manual paths)
- [ ] `main.py`: Replace MIDTERM_RESULTS_SCREEN continue handler to go to choice screen
- [ ] `main.py`: Add `POST_MID_CHOICE_SCREEN` event handler (repeat/manual buttons)
- [ ] `main.py`: Add `POST_MID_CHOICE_SCREEN` render block
- [ ] `main.py`: Import `post_mid_choice_screen` from screens
- [ ] `screens.py`: Add `post_mid_choice_screen()` function
- [ ] `savegame.py`: Add `pre_mid_week_template` to save/load
- [ ] `main.py`: Pass `pre_mid_week_template` to all `save_game()` calls
- [ ] `main.py`: Restore `_pre_mid_week_template` when loading a save

### Feature 2 — Stats Bar Trends

- [ ] `student.py`: Add 11 new instance variables in `__init__`
- [ ] `student.py`: Add accumulation lines in `study()`, `rest()`, `take_break()`, `attend_class()`
- [ ] `student.py`: Append weekly snapshots + reset daily accumulators in `end_of_day()`
- [ ] `student.py`: Add `reset_week_snapshots()` method
- [ ] `savegame.py`: Save and load all 11 new student fields
- [ ] `main.py`: Call `student.reset_week_snapshots()` at every week boundary (4 locations)
- [ ] `ui.py`: Add `_draw_trends_section()` method to `StatsDashboard`
- [ ] `ui.py`: Update `draw()` to accept `week_count` and call `_draw_trends_section` first
- [ ] `main.py`: Update all 4 `stats_dashboard.draw()` calls to pass `week_count=week_count`
