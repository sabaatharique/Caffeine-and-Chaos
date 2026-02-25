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


def wifi_failure_event(p=0.3, lam=2, day_start=8.0, day_end=32.0):
    outages = []

    # Bernoulli: does wifi fail at all today?
    if random.random() < p:

        # Poisson: how many outages?
        num_outages = poisson_random(lam)

        for _ in range(num_outages):
            # Uniform start time within the game day (hours)
            start = random.uniform(day_start, day_end - (5 / 60))
            # Uniform duration: 5 minutes to 3 hours (in hours)
            duration = random.uniform(5 / 60, 3.0)

            outages.append({
                "start": start,
                "duration": duration,
            })

    # Sort by start time so we can process them in order
    outages.sort(key=lambda o: o["start"])
    return outages