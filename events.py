import random
import math


def poisson_random(lam):
    L = math.exp(-lam)
    k = 0
    p = 1.0

    while p > L:
        k += 1
        p *= random.random()

    return k - 1


def wifi_failure_event(lam=1.25, day_start=8.0, day_end=32.0):
    outages = []

    # Poisson: how many outages?
    num_outages = poisson_random(lam)

    for _ in range(num_outages):
        # Uniform start time within the game day (hours), rounded to nearest minute
        start_min = random.randint(int(day_start * 60), int(day_end * 60) - 5)
        start = start_min / 60.0
        
        # Uniform duration: 5 minutes to 2 hours (in hours), rounded to nearest minute
        duration_min = random.randint(5, 120)
        duration = duration_min / 60.0

        outages.append({
            "start": start,
            "duration": duration,
        })

    # Sort by start time so we can process them in order
    outages.sort(key=lambda o: o["start"])
    return outages


def compute_sickness_prob(stress_history: list, health_history: list, base_prob=0.005, max_prob=0.10) -> float:
    """Return today's Bernoulli probability of falling sick based on history."""
    if not stress_history:
        return base_prob

    avg_stress = sum(stress_history) / len(stress_history)
    avg_health = sum(health_history) / len(health_history)

    stress_factor = 0.02 * (avg_stress / 100)
    health_factor = 0.02 * (1 - avg_health / 100)

    p = base_prob + stress_factor + health_factor
    return min(p, max_prob)


def generate_sick_duration(recovery_prob=0.40) -> int:
    """Sample illness duration from a geometric distribution."""
    days = 0
    while True:
        days += 1
        if random.random() < recovery_prob:
            return days


def generate_quiz_schedule(weekly_slots, used_slots):
    """
    Assign 2 pre-midterm + 2 post-midterm quiz dates.
    Returns a list of quiz dicts.
    """
    pre_mid_weights  = [1, 1, 2, 4, 5, 5, 4]     # weeks 1-7
    post_mid_weights = [1, 1, 2, 4, 5, 5, 4, 3]  # weeks 8-15
    scheduled_quizzes = []
    next_quiz_num = 1

    def _pick(week_pool: list[int], weights: list[int]) -> dict | None:
        """Attempt up to 30 times to find a unique (week, day_idx) slot."""
        for _ in range(30):
            week = random.choices(week_pool, weights=weights[:len(week_pool)], k=1)[0]
            day_idx, slot_idx = random.choice(weekly_slots)
            key = (week, day_idx)
            if key not in used_slots:
                used_slots.add(key)
                return {
                    "quiz_number": 0,  # assigned later
                    "week":     week,
                    "day_idx":  day_idx,
                    "slot_idx": slot_idx,
                    "taken":    False,
                    "missed":   False,
                    "mark":     None,
                    "attempt":  0,
                }
        return None

    # 2 quizzes before mid (weeks 1-7)
    pre_weeks = list(range(1, 8))
    for _ in range(2):
        q = _pick(pre_weeks, pre_mid_weights)
        if q:
            scheduled_quizzes.append(q)

    # 2 quizzes after mid (weeks 8-15)
    post_weeks = list(range(8, 16))
    for _ in range(2):
        q = _pick(post_weeks, post_mid_weights)
        if q:
            scheduled_quizzes.append(q)

    scheduled_quizzes.sort(key=lambda x: (x["week"], x["day_idx"], x["slot_idx"]))
    for i, q in enumerate(scheduled_quizzes, start=1):
        q["quiz_number"] = i

    return scheduled_quizzes


def generate_lab_assessment_schedule(weekly_slots):
    """
    Assign 1 lab-mid (week 6 or 7) + 1 lab-final (week 14 or 15) to a lab course.
    Each assessment lands on one of the course's own lab slots.
    Returns a list of two assessment dicts.
    """
    # Weighted: slightly prefer the later week in each window (harder to be early)
    mid_weeks    = [6, 7]
    mid_weights  = [4, 6]
    final_weeks  = [14, 15]
    final_weights = [4, 6]

    assessments = []
    used: set[tuple[int, int]] = set()

    def _pick(week_pool, weights, assessment_type):
        for _ in range(30):
            week    = random.choices(week_pool, weights=weights, k=1)[0]
            day_idx, slot_idx = random.choice(weekly_slots)
            key = (week, day_idx)
            if key not in used:
                used.add(key)
                return {
                    "assessment_type": assessment_type,   # "lab_mid" or "lab_final"
                    "week":     week,
                    "day_idx":  day_idx,
                    "slot_idx": slot_idx,
                    "taken":    False,
                    "missed":   False,
                    "mark":     None,
                    "attempt":  0,
                }
        return None

    mid = _pick(mid_weeks, mid_weights, "lab_mid")
    if mid:
        assessments.append(mid)

    final = _pick(final_weeks, final_weights, "lab_final")
    if final:
        assessments.append(final)

    return assessments