class Student:
    def __init__(self):
        # Status bars
        self.knowledge = 50
        self.sleep = 70
        self.health = 80
        self.stress = 30
        self.motivation = 60

        # Academic tracking
        self.attendance = 0   

        # Internal tracking
        self.consecutive_stress_days = 0

        # Action enabled
        self.action_status = {
            'study': True,
            'sleep': True,
            'relax': True,
            'eat': True,
            'coffee': True,
            'attend_class': True,
        }
        self.update_action_status() # Initial update

    def update_action_status(self):
        self.action_status['study'] = self.sleep > 0
        self.action_status['sleep'] = self.sleep < 100
        self.action_status['relax'] = self.stress > 0 or self.motivation < 100
        self.action_status['eat'] = self.health < 100
        self.action_status['coffee'] = self.sleep < 100 and self.health > 0
        # self.action_status['attend_class'] = self.sleep > 0

    def clamp(self):
        messages = []
        # Keep values within limits
        self.knowledge = max(0, min(100, self.knowledge))
        self.sleep = max(0, min(100, self.sleep))
        self.health = max(0, min(100, self.health))
        self.stress = max(0, min(100, self.stress))
        self.motivation = max(0, min(100, self.motivation))
        self.attendance = max(0, min(100, self.attendance))


        if self.knowledge < 10:
            messages.append("Warning: Knowledge is critically low!")
        if self.knowledge == 100:
            messages.append("Knowledge maxxed out!")

        if self.sleep < 10:
            messages.append("Warning: Sleep is critically low!")
        if self.sleep == 100:
            messages.append("Sleep maxxed out!")

        if self.health < 10:
            messages.append("Warning: Health is critically low!")
        if self.health == 100:
            messages.append("Health maxxed out!")
        
        if self.motivation < 10:
            messages.append("Warning: Motivation is critically low!")

        if self.stress > 90:
            messages.append("Warning: Stress is critically high!")
        
        self.update_action_status()
        return messages

    def end_of_day(self):
        # Daily changes in state
        if self.stress > 70:
            self.consecutive_stress_days += 1
        else:
            self.consecutive_stress_days = 0

        return self.clamp()

    def attend_class(self, course_difficulty=1.0):
        messages = []
        if not self.action_status['attend_class']:
            messages.append("You are too tired to attend class.")
            return messages
        self.knowledge += 2 * course_difficulty
        self.stress += 3 * course_difficulty
        self.sleep -= 5
        self.attendance += 1

        messages.extend(self.clamp())
        return messages

    def study(self, hours=2.0):
        messages = []
        if not self.action_status['study']:
            messages.append("You are too tired to study.")
            return messages
        # Study efficiency depends on current state
        efficiency = (self.sleep + self.health + (100 - self.stress) + (100 - self.motivation)) / 400
        self.knowledge += hours * 3 * efficiency
        self.sleep -= hours * 8
        self.stress += hours * 10
        self.health -= hours * 5

        messages.extend(self.clamp())
        return messages

    def rest(self, hours=1.0):
        messages = []
        if not self.action_status['sleep']:
            messages.append("You are well rested.")
            return messages
        self.sleep += hours * 10
        self.stress -= hours * 5
        self.health += hours * 3
        self.knowledge -= hours * 2

        messages.extend(self.clamp())
        return messages
    
    def eat(self):
        messages = []
        if not self.action_status['eat']:
            messages.append("You are at nearly full health.")
            return messages
        self.health += 10
        self.stress -= 5

        messages.extend(self.clamp())
        return messages

    def drink_coffee(self):
        messages = []
        if not self.action_status['coffee']:
            if self.health < 10:
                 messages.append("Your health is too low to drink coffee.")
            else:
                 messages.append("You are already wide awake.")
            return messages
        self.sleep += 10
        self.health -= 7
        self.stress += 3

        messages.extend(self.clamp())
        return messages

    def take_break(self, hours=1.0):
        messages = []
        if not self.action_status['relax']:
            messages.append("You are perfectly relaxed and motivated.")
            return messages
        self.stress -= hours * 8
        self.motivation += hours * 5

        messages.extend(self.clamp())
        return messages

    def max_hours(self, action):
        """Return the max whole hours the player can perform *action*
        before any stat would be clamped (hit 0 or 100)."""
        import math
        limits = []

        if action == 'study':
            # sleep  -= hours * 4  →  max before 0
            if self.sleep > 0:
                limits.append(self.sleep / 8)
            # health -= hours * 2  →  max before 0
            if self.health > 0:
                limits.append(self.health / 5)
            # stress += hours * 3  →  max before 100
            if self.stress < 100:
                limits.append((100 - self.stress) / 10)

        elif action == 'sleep':
            # sleep  += hours * 10 →  max before 100
            if self.sleep < 100:
                limits.append((100 - self.sleep) / 10)
            # knowledge -= hours * 2 → max before 0
            if self.knowledge > 0:
                limits.append(self.knowledge / 2)

        elif action == 'relax':
            # stress -= hours * 8  →  max before 0
            if self.stress > 0:
                limits.append(self.stress / 8)
            # motivation += hours * 5 → max before 100
            if self.motivation < 100:
                limits.append((100 - self.motivation) / 5)

        if not limits:
            return 0
        return max(1, math.floor(min(limits)))

    def burnout_check(self):
        # Return true if burnout occurs
        return self.consecutive_stress_days >= 5
