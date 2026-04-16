# Sickness System — Implementation Plan
### Project: Caffeine & Chaos

---

## Overview

This document is a self-contained guide for implementing a **random sickness system** into the existing simulation. Read it fully before touching any file. Every change is described precisely — what file, what location, what code to add or modify.

---

## Codebase Quick-Reference

| File | Role |
|---|---|
| `student.py` | `Student` class — all stat logic, burnout, actions live here |
| `main.py` | Game loop, `burnout_active` flag, replay runners, event handling |
| `events.py` | Standalone random event generators (e.g. `wifi_failure_event`) |
| `screens.py` | Pure drawing functions — `day_end_screen`, `game_screen`, etc. |
| `courses.py` | `Course` and `CourseManager` — knowledge, grades |
| `environment.py` | Constants, time helpers, clock drawing |

---

## Design Summary

| Component | Approach |
|---|---|
| Occurrence | Bernoulli trial each day, dynamic probability from rolling history |
| Duration | Geometric distribution — each day has a fixed recovery chance |
| State | Two fields on `Student`: `is_sick`, `sick_days_remaining` |
| Effects | Study efficiency ↓50%, class attendance forced-miss or penalised, health slow-drains, stress ↑ |
| Integration | Hooks into `end_of_day()` (same pattern as burnout), plus `study()` and `attend_class()` |
| UI | `alert_box` popup on onset (same mechanism as WiFi outage alerts), status message on recovery |

---

## Part 1 — `student.py` changes

### 1.1 — Add sickness state fields to `__init__`

Find the block that initialises burnout tracking:

```python
# Internal tracking
self.consecutive_stress_days = 0
self.burnout_days_remaining = 5
```

Add the sickness fields directly after it:

```python
# Sickness tracking
self.is_sick = False
self.sick_days_remaining = 0

# Rolling history (last 5 days) for computing sickness probability
self._stress_history: list[float] = []
self._health_history: list[float] = []
self._HISTORY_WINDOW = 5          # days to look back
self._SICKNESS_BASE_PROB = 0.005  # 0.5% daily baseline
self._SICKNESS_MAX_PROB  = 0.10   # hard cap at 10%
self._RECOVERY_PROB      = 0.40   # 40% chance to recover each sick day → ~2.5 day expected illness
```

---

### 1.2 — Add three private helper methods

Place these anywhere before `end_of_day`. A clean spot is right above `burnout_check`.

```python
# ── Sickness helpers ────────────────────────────────────────────────────────

def _record_daily_history(self):
    """Snapshot today's stress & health into rolling history."""
    self._stress_history.append(self.stress)
    self._health_history.append(self.health)
    # Keep only the last N days
    if len(self._stress_history) > self._HISTORY_WINDOW:
        self._stress_history.pop(0)
    if len(self._health_history) > self._HISTORY_WINDOW:
        self._health_history.pop(0)

def _compute_sickness_prob(self) -> float:
    """Return today's Bernoulli probability of falling sick."""
    if not self._stress_history:          # no history yet → baseline only
        return self._SICKNESS_BASE_PROB

    avg_stress = sum(self._stress_history) / len(self._stress_history)
    avg_health = sum(self._health_history) / len(self._health_history)

    stress_factor = 0.02 * (avg_stress / 100)
    health_factor = 0.02 * (1 - avg_health / 100)

    p = self._SICKNESS_BASE_PROB + stress_factor + health_factor
    return min(p, self._SICKNESS_MAX_PROB)

def _generate_sick_duration(self) -> int:
    """Sample illness duration from a geometric distribution."""
    import random
    days = 0
    while True:
        days += 1
        if random.random() < self._RECOVERY_PROB:
            return days
```

> **Note:** `import random` is already at the top of `student.py` (it isn't yet — add `import random` at the very top of the file alongside `import math`).

---

### 1.3 — Modify `end_of_day`

The existing `end_of_day` handles burnout. Add sickness logic inside the **same method**, following the same pattern. The full updated method looks like this (new lines are marked):

```python
def end_of_day(self):
    messages = []

    # Daily changes in state
    if self.stress > 70:
        self.consecutive_stress_days += 1
    else:
        self.consecutive_stress_days = 0

    if self.burnout_days_remaining > 0:
        self.burnout_days_remaining -= 1
        if self.burnout_days_remaining == 0:
            messages.append("You have recovered from burnout!")

    if self.burnout_check():
        self.trigger_burnout()
        messages.append("Burnout! Your stats have taken a hit.")

    # ── NEW: Sickness logic ───────────────────────────────────────────────
    # Always record today before checking onset so history is up-to-date
    self._record_daily_history()

    if self.is_sick:
        # Tick down remaining sick days; check geometric recovery
        import random
        if random.random() < self._RECOVERY_PROB:
            self.is_sick = False
            self.sick_days_remaining = 0
            messages.append("You've recovered from your illness. Feel better!")
        else:
            self.sick_days_remaining = max(0, self.sick_days_remaining - 1)
            # Daily passive effect while sick: health drains a little
            self.health -= 5
            self.stress += 5
            messages.append(f"Still sick — {self.sick_days_remaining} day(s) estimated remaining.")
    else:
        # Bernoulli trial for new sickness
        import random
        p = self._compute_sickness_prob()
        if random.random() < p:
            self.is_sick = True
            self.sick_days_remaining = self._generate_sick_duration()
            # Immediate onset penalty
            self.health -= 10
            self.stress += 10
            messages.append("SICK! You've come down with an illness.")
    # ── END new block ─────────────────────────────────────────────────────

    messages.extend(self.clamp())
    return messages
```

> **Important:** Keep the `import random` at the top of the file (step 1.2 note). Remove the two inline `import random` lines once the top-level import is confirmed — they are written inline above only for clarity.

---

### 1.4 — Modify `study` to apply sickness penalty

Find the `study` method. Locate this line:

```python
knowledge_mult = self.wifi_knowledge_penalty if wifi_penalty else 1.0
```

Replace it with:

```python
knowledge_mult = self.wifi_knowledge_penalty if wifi_penalty else 1.0
if self.is_sick:
    knowledge_mult *= 0.5   # sickness halves effective learning
```

No other changes to `study` are needed.

---

### 1.5 — Modify `attend_class` to block or penalise attendance while sick

Find `attend_class`. At the very top of the method body, right after the existing "too tired" check, add:

```python
if self.is_sick:
    messages.append(f"You're too sick to attend {course.name}. Class missed.")
    # Still counts against attendance — you really weren't there
    return messages
```

This mirrors the burnout design (stat-penalty → can't attend). It makes attendance a meaningful consequence of falling sick.

---

### 1.6 — Add a `sick_check` convenience property

Optionally (used in `main.py` for clarity), add a read-only property below `burnout_check`:

```python
@property
def sick_active(self) -> bool:
    """True while the student is sick (mirrors burnout_active pattern)."""
    return self.is_sick
```

---

## Part 2 — `main.py` changes

### 2.1 — Add `sick_active` game-state variable

Find the block near the top of the game-state section:

```python
day_over      = False
burnout_active = False   # True while student is recovering from burnout
```

Add one line after it:

```python
sick_active = False      # True while student is sick
```

---

### 2.2 — Add a sick background image (optional but recommended)

In the `bg_map` dict:

```python
bg_map  = {
    'study':        pygame.image.load("assets/images/study.jpg"),
    ...
    'burnout':      pygame.image.load("assets/images/burnout.jpg"),
    'default':      pygame.image.load("assets/images/study.jpg"),
}
```

Add:

```python
    'sick':         pygame.image.load("assets/images/sick.jpg"),
```

> If you don't have a `sick.jpg`, reuse `burnout.jpg` or `sleep.jpg` as a placeholder — just map `'sick'` to one of them. The image switch is cosmetic only.

---

### 2.3 — Hook sickness into the day-end logic

Search `main.py` for the block that handles `end_of_day` results and sets `burnout_active`. It looks like this (inside the day-end button handler, around line 600–650 in the original):

```python
end_msgs = student.end_of_day()
messages.extend(end_msgs)
if any("Burnout!" in m for m in end_msgs):
    burnout_active = True
    current_game_bg = bg_map['burnout']
```

Extend it to also detect sickness:

```python
end_msgs = student.end_of_day()
messages.extend(end_msgs)

if any("Burnout!" in m for m in end_msgs):
    burnout_active = True
    current_game_bg = bg_map['burnout']

# ── NEW: sickness detection ───────────────────────────────────────────────
sick_active = student.is_sick
if any("SICK!" in m for m in end_msgs):
    current_game_bg = bg_map.get('sick', bg_map['sleep'])
    alert_box.open(
        "You're Sick!",
        "You've come down with an illness.\n"
        "Study efficiency is halved and you cannot attend classes until you recover.",
        "red"
    )
elif any("recovered from your illness" in m for m in end_msgs):
    sick_active = False
    current_game_bg = bg_map['default']
# ── END new block ─────────────────────────────────────────────────────────
```

> **Note:** `alert_box.open(title, body, colour)` is already used for WiFi outage alerts — this is an identical call. Check the `AlertBox` constructor signature in `ui.py` to confirm argument order if needed.

---

### 2.4 — Sync `sick_active` from replay runners

Both `ReplayRunner.tick()` and `WeekReplayRunner.tick()` call `student.end_of_day()` and already check for burnout like this:

```python
if any("Burnout!" in m for m in day_msgs):
    self.burnout_occurred = True
    ...
```

Add a symmetric sickness check directly after each burnout check in both runners:

```python
# Inside ReplayRunner.tick() — after the burnout check block:
if any("SICK!" in m for m in day_msgs):
    # Alert will be shown when main loop reads runner messages
    pass  # sick_active is read directly from student.is_sick in main loop

# After the runner finishes (in the main loop section that processes runner.done):
sick_active = student.is_sick
```

The simplest approach: after each replay runner's `.done` check in the main loop, add:

```python
sick_active = student.is_sick
```

This keeps `sick_active` always in sync without touching the runners themselves.

---

### 2.5 — Pass `sick_active` to `day_end_screen` (optional)

The `day_end_screen` function already shows a burnout notice. You can similarly show a sick notice. This is optional but improves feedback.

In the `day_end_screen` call(s) inside `main.py`, add `sick_active=sick_active` as a keyword argument — but only **after** updating `screens.py` (see Part 3 below).

---

## Part 3 — `screens.py` changes (optional UI polish)

### 3.1 — Show sickness notice on the day-end screen

Open `screens.py` and find `day_end_screen`. Locate the burnout notice block:

```python
if burnout_active:
    burnout_surf = message_font.render(
        f"You're burned out ...",
        True, (255, 90, 90)
    )
    screen.blit(burnout_surf, ...)
else:
    ...  # continue prompt
```

Add a sickness notice right before this block:

```python
# NEW: sickness notice (show even alongside burnout — they can co-exist)
if sick_active:
    sick_surf = message_font.render(
        "🤒 You're sick — study efficiency halved, classes missed.",
        True, (255, 150, 50)
    )
    screen.blit(sick_surf,
                (WIDTH // 2 - sick_surf.get_width() // 2, HEIGHT // 2 - 30))
```

Update the function signature to accept the new parameter:

```python
def day_end_screen(screen, background_image, student, bars, game_buttons,
                   messages, message_font, bar_space,
                   draw_clock_fn, clock_font, date_font,
                   time_of_day, day_count,
                   avg_knowledge, burnout_active,
                   continue_btn, repeat_btn, quit_btn,
                   repeat_box, alert_box,
                   week_count=1, day_in_week=1,
                   repeat_week_btn=None, week_repeat_box=None,
                   sick_active=False):          # ← add this
```

---

## Part 4 — Save/Load compatibility

If the project uses `savegame.py` (it does — `save_game` / `load_game` are imported in `main.py`), the new sickness fields must be included in the save dict.

### What to add to `save_game`

Find where `student` fields are serialised (look for `student.sleep`, `student.health`, etc. in `savegame.py`). Add:

```python
"is_sick":             student.is_sick,
"sick_days_remaining": student.sick_days_remaining,
"stress_history":      student._stress_history,
"health_history":      student._health_history,
```

### What to add to `load_game`

When the student is reconstructed from the save dict, restore these fields:

```python
student.is_sick             = data.get("is_sick", False)
student.sick_days_remaining = data.get("sick_days_remaining", 0)
student._stress_history     = data.get("stress_history", [])
student._health_history     = data.get("health_history", [])
```

Using `.get(..., default)` ensures old save files without the new keys load cleanly.

---

## Part 5 — Checklist (implement in this order)

```
[ ] 1. Add `import random` at the top of student.py (if not already there)
[ ] 2. Add sickness fields to Student.__init__  (Part 1.1)
[ ] 3. Add three helper methods to Student       (Part 1.2)
[ ] 4. Modify Student.end_of_day                (Part 1.3)
[ ] 5. Modify Student.study                     (Part 1.4)
[ ] 6. Modify Student.attend_class              (Part 1.5)
[ ] 7. Add sick_active variable to main.py      (Part 2.1)
[ ] 8. Add 'sick' entry to bg_map in main.py    (Part 2.2)
[ ] 9. Hook sickness into day-end logic         (Part 2.3)
[ ]10. Sync sick_active after replay runners    (Part 2.4)
[ ]11. Update screens.py day_end_screen         (Part 3.1)  ← optional but nice
[ ]12. Update savegame.py save/load             (Part 4)
```

---

## Design Parameters Summary

| Parameter | Value | Effect |
|---|---|---|
| `_SICKNESS_BASE_PROB` | 0.005 | 0.5% baseline daily chance |
| `_HISTORY_WINDOW` | 5 days | Rolling average window |
| `stress_factor` | 0.02 × (avg_stress / 100) | Max +2% at full stress |
| `health_factor` | 0.02 × (1 − avg_health/100) | Max +2% at zero health |
| `_SICKNESS_MAX_PROB` | 0.10 | Hard cap: never above 10% per day |
| `_RECOVERY_PROB` | 0.40 | ~2.5 day expected illness |
| Study knowledge mult | × 0.5 | Halved learning while sick |
| Daily sick drain | health −5, stress +5 | Passive deterioration |
| Onset penalty | health −10, stress +10 | Immediate hit on day 1 |

---

## Notes for the Implementer

- **Do not** change `courses.py` or `environment.py` — sickness has no hooks there.
- The `sick_active` flag in `main.py` is a local variable (not on `Student`) solely for UI rendering — identical to how `burnout_active` works. `student.is_sick` is the authoritative truth.
- The `alert_box.open()` call for sickness onset is the same pattern used for WiFi outage alerts — check `ui.py → AlertBox.open()` for exact signature before calling.
- Emoji in `message_font.render()` may not render depending on the font (`Papernotes.otf`). Replace `"🤒"` with `"[SICK]"` if it shows as a box.
- If you want sickness to block the day-end Continue button (like burnout does), follow the same pattern: add `or sick_active` to the condition that disables `continue_btn`.
