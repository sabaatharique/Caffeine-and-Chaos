import pygame

# Day timing constants
DAY_START: float = 8.0    # 08:00  (hours)
DAY_END:   float = 32.0   # 08:00 next morning (24 + 8)

# Week constants
DAYS_IN_WEEK = 7
DAYS_OF_WEEK = [ "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" ]

# Midterm exam window: weeks 8–9, days Mon/Wed/Fri only (day_idx 0, 2, 4)
MIDTERM_EXAM_WEEKS = [8, 9]
MIDTERM_EXAM_DAYS = [0, 2, 4]   # Mon, Wed, Fri (0-indexed)

# Final exam window: weeks 18–20, days Tue/Fri only (day_idx 1, 3)
# Raw timeline: 1-7 pre-mid, 8-9 midterms, 10-17 post-mid (display 8-15), 18-20 finals
FINAL_EXAM_WEEKS = [18, 19, 20]
FINAL_EXAM_DAYS = [1, 3]      # Tue, Fri (0-indexed)

# Index 4 is the lunch slot (no classes)
# Each class period is 75 minutes 
SLOT_TIMES: list[tuple[float, float]] = [
    (8.0,   9.25),   # 8:00 – 9:15
    (9.25,  10.5),   # 9:15 – 10:30
    (10.5,  11.75),  # 10:30 – 11:45
    (11.75, 13.0),   # 11:45 – 1:00
    (13.0,  14.5),   # 1:00 – 2:30  ← lunch break (slot 4, no classes)
    (14.5,  15.75),  # 2:30 – 3:45
    (15.75, 17.0),   # 3:45 – 5:00
]
LUNCH_SLOT_IDX = 4   # index of the lunch slot (never has a class)


def get_todays_classes(courses: list, day_in_week: int,
                       week_count: int = 1) -> list[tuple[float, float, object]]:
    """Return a sorted list of (start_hour, end_hour, course) for all classes
    scheduled on *day_in_week* (1=Monday … 5=Friday).
    Saturday (6) and Sunday (7) always return an empty list.
    Biweekly courses appear only on odd-numbered weeks (1, 3, 5 …).
    """
    if day_in_week > 5:
        return []  # no classes on weekends

    day_idx = day_in_week - 1  # 0-indexed (0=Monday … 4=Friday)
    result = []
    for course in courses:
        # Biweekly labs only run on odd weeks; skip on even weeks
        if getattr(course, "schedule", "weekly") == "biweekly" and week_count % 2 == 0:
            continue
        for (d, s) in course.weekly_slots:
            if d == day_idx and s != LUNCH_SLOT_IDX:
                start_h, end_h = SLOT_TIMES[s]
                result.append((start_h, end_h, course))

    result.sort(key=lambda x: x[0])
    return result


def day_name(day_in_week: int) -> str:
    """Return the weekday name for a 1-based day_in_week (1=Monday … 7=Sunday)."""
    return DAYS_OF_WEEK[(day_in_week - 1) % DAYS_IN_WEEK]


def format_time(hour: float) -> str:
    """Convert a fractional 24-hour value into a 12-hour AM/PM string."""
    total_minutes = round(hour * 60)
    h = (total_minutes // 60) % 24
    m = total_minutes % 60
    if h == 0:
        return f"12:{m:02d} AM"
    elif h < 12:
        return f"{h}:{m:02d} AM"
    elif h == 12:
        return f"12:{m:02d} PM"
    else:
        return f"{h - 12}:{m:02d} PM"


def draw_clock(screen, clock_font, date_font, time_of_day: float,
               day_count: int, bar_space: int, week_count: int = 1,
               day_in_week: int = 1, exam_week_label: str = None) -> None:
    """Render the digital clock + day + week counter in the top-right area."""
    WIDTH = screen.get_width()
    clock_color = (255, 255, 0)
    time_str  = format_time(time_of_day)
    time_surf  = clock_font.render(time_str, True, clock_color)
    if exam_week_label:
        week_label_str = f"{exam_week_label}, {day_name(day_in_week)}"
        week_color = (255, 255, 0)
    else:
        week_label_str = f"Week {week_count}, {day_name(day_in_week)}"
        week_color = clock_color
    week_surf  = date_font.render(week_label_str, True, week_color)

    right_edge = WIDTH - 50
    
    y = 120
    screen.blit(time_surf, (right_edge - time_surf.get_width(), y))
    y += time_surf.get_height() - 10
    screen.blit(week_surf, (right_edge - week_surf.get_width(), y))


def outage_overlap(outages: list, t_start: float, t_end: float) -> float:
    """Return the total hours of wifi-outage overlap within [t_start, t_end)."""
    total = 0.0
    for o in outages:
        o_start = o["start"]
        o_end   = o["start"] + o["duration"]
        total  += max(0.0, min(t_end, o_end) - max(t_start, o_start))
    return total
