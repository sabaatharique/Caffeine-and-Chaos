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
        if self.sleep < 10:
            messages.append("Warning: Sleep is critically low!")
        if self.health < 10:
            messages.append("Warning: Health is critically low!")
        if self.motivation < 10:
            messages.append("Warning: Motivation is critically low!")
        if self.stress > 90:
            messages.append("Warning: Stress is critically high!")
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
        if self.sleep == 0:
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
        if self.sleep == 0:
            messages.append("You are too tired to study.")
            return messages
        # Study efficiency depends on current state
        efficiency = (self.sleep + self.health + (100 - self.stress) + (100 - self.motivation)) / 400
        self.knowledge += hours * 3 * efficiency
        self.sleep -= hours * 8
        self.stress += hours * 5
        self.health -= hours * 2

        messages.extend(self.clamp())
        return messages

    def rest(self, hours=1.0):
        messages = []
        if self.sleep >= 100:
            messages.append("You are fully rested.")
            return messages
        self.sleep += hours * 10
        self.stress -= hours * 5
        self.health += hours * 3
        self.knowledge -= hours * 2

        messages.extend(self.clamp())
        return messages
    
    def eat(self):
        messages = []
        if self.health >= 100:
            messages.append("You are already at full health.")
            return messages
        self.health += 10
        self.stress -= 5

        messages.extend(self.clamp())
        return messages

    def drink_coffee(self):
        messages = []
        if self.health < 10:
            messages.append("Your health is too low to drink coffee.")
            return messages
        if self.sleep >= 100:
            messages.append("You are already wide awake.")
            return messages
        self.sleep += 10
        self.health -= 7
        self.stress += 3

        messages.extend(self.clamp())
        return messages

    def take_break(self, hours=1.0):
        messages = []
        if self.stress == 0 and self.motivation == 100:
            messages.append("You are perfectly relaxed and motivated.")
            return messages
        self.stress -= hours * 8
        self.motivation += hours * 5

        messages.extend(self.clamp())
        return messages

    def burnout_check(self):
        # Return true if burnout occurs
        return self.consecutive_stress_days >= 5
