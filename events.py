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