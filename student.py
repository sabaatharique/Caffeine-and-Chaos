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
        # Keep values within limits
        self.knowledge = max(0, min(100, self.knowledge))
        self.sleep = max(0, min(100, self.sleep))
        self.health = max(0, min(100, self.health))
        self.stress = max(0, min(100, self.stress))
        self.motivation = max(0, min(100, self.motivation))
        self.attendance = max(0, min(100, self.attendance))

    def end_of_day(self):
        # Daily changes in state
        if self.stress > 70:
            self.consecutive_stress_days += 1
        else:
            self.consecutive_stress_days = 0

        self.clamp()

    def attend_class(self, course_difficulty=1.0):
        self.knowledge += 2 * course_difficulty
        self.stress += 3 * course_difficulty
        self.sleep -= 5
        self.attendance += 1

        self.clamp()

    def study(self, hours=2.0):
        # Study efficiency depends on current state
        efficiency = (self.sleep + self.health + (100 - self.stress) + (100 - self.motivation)) / 400
        self.knowledge += hours * 5 * efficiency
        self.sleep -= hours * 8
        self.stress += hours * 5

        self.clamp()

    def rest(self, hours=1.0):
        self.sleep += hours * 10
        self.stress -= hours * 5
        self.health += hours * 3
        self.knowledge -= hours * 2

        self.clamp()
    
    def eat(self, food_supply):
        self.health += 10
        self.stress -= 5
        food_supply -= 10

        self.clamp()

    def drink_coffee(self):
        self.sleep += 10
        self.health -= 7
        self.stress += 3

        self.clamp()

    def take_break(self, hours=1.0):
        self.stress -= hours * 8
        self.motivation += hours * 5

        self.clamp()

    def burnout_check(self):
        # Return true if burnout occurs
        return self.consecutive_stress_days >= 5
