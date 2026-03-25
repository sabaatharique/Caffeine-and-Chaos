import pygame

# Day timing constants
DAY_START: float = 8.0    # 08:00  (hours)
DAY_END:   float = 32.0   # 08:00 next morning (24 + 8)

# Week constants
DAYS_IN_WEEK = 7
DAYS_OF_WEEK = [ "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday" ]


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
               day_in_week: int = 1) -> None:
    """Render the digital clock + day + week counter in the top-right area."""
    WIDTH = screen.get_width()
    clock_color = (255, 255, 0)
    time_str  = format_time(time_of_day)
    time_surf  = clock_font.render(time_str, True, clock_color)
    #day_surf   = date_font.render(f"Day {day_count}", True, clock_color)
    week_surf  = date_font.render(f"Week {week_count},  {day_name(day_in_week)}", True, clock_color)

    box_w = max(time_surf.get_width(),# day_surf.get_width(),
                week_surf.get_width()) + 20
    box_h = (time_surf.get_height() +# day_surf.get_height()
             + week_surf.get_height() + 5)
    box_x = WIDTH - bar_space - box_w
    box_y = 95

    clock_bg = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
    clock_bg.fill((0, 0, 0, 180))
    screen.blit(clock_bg, (box_x, box_y))

    y = 100
    screen.blit(time_surf, (box_x + box_w - time_surf.get_width() - 10, y))
    y += time_surf.get_height() - 10
    #screen.blit(day_surf,  (box_x + box_w - day_surf.get_width()  - 10, y))
    #y += day_surf.get_height() - 4
    screen.blit(week_surf, (box_x + box_w - week_surf.get_width() - 10, y))


def outage_overlap(outages: list, t_start: float, t_end: float) -> float:
    """Return the total hours of wifi-outage overlap within [t_start, t_end)."""
    total = 0.0
    for o in outages:
        o_start = o["start"]
        o_end   = o["start"] + o["duration"]
        total  += max(0.0, min(t_end, o_end) - max(t_start, o_start))
    return total
