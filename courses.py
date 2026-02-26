import random

class Course:
   def __init__(self, name, credits, course_type="Theory", max_lab_evaluations=0):
    self.name = name
    self.credits = credits
    self.course_type = course_type

    self.knowledge = 0.0

    # Attendance
    self.total_classes = total_classes
    self.attended_classes = 0

    # Theory
    self.quiz_marks = []
    self.mid_mark = None
    self.final_mark = None

    # Lab
    self.lab_evaluations = []
    self.lab_mid = None
    self.lab_final = None
    self.max_lab_evaluations = max_lab_evaluations

    self.grade_point = 0.0


    def add_knowledge(self, amount):
        self.knowledge += amount
        self.knowledge = max(0, min(100, self.knowledge))

   
    def attend_class(self):
        # To do
        pass


    def get_attendance_percentage(self):
        if self.total_classes == 0:
            return 0
        return (self.attended_classes / self.total_classes) * 100  
    
    # THEORY SECTION 
    def generate_quiz_mark(self, stress=0, sleep=1.0, health=100):
        if self.course_type != "Theory":
            return

        if len(self.quiz_marks) >= 4:
            return

        randomness = random.uniform(-10, 10)

        base = (
            0.65 * self.knowledge +
            0.15 * (sleep * 100) +
            0.15 * health -
            0.25 * stress
        )

        mark = max(0, min(100, base + randomness))
        self.quiz_marks.append(mark)


    def generate_mid_mark(self, stress=0, sleep=1.0, health=100):
        if self.course_type != "Theory":
            return

        randomness = random.uniform(-8, 8)

        base = (
            0.7 * self.knowledge +
            0.15 * (sleep * 100) +
            0.15 * health -
            0.2 * stress
        )

        self.mid_mark = max(0, min(100, base + randomness))


    def generate_final_mark(self, stress=0, sleep=1.0, health=100):
        if self.course_type != "Theory":
            return

        randomness = random.uniform(-5, 5)

        base = (
            0.75 * self.knowledge +
            0.1 * (sleep * 100) +
            0.15 * health -
            0.2 * stress
        )

        self.final_mark = max(0, min(100, base + randomness))

    # LAB SECTION
    def generate_lab_evaluation(self, stress=0, health=100):

        if self.course_type != "Lab":
            return

        if len(self.lab_evaluations) >= self.max_lab_evaluations:
            return

        randomness = random.uniform(-5, 5)

        base = (
            0.6 * self.knowledge +
            0.2 * health -
            0.3 * stress
        )

        mark = max(0, min(100, base + randomness))
        self.lab_evaluations.append(mark)

    def generate_lab_mid(self, stress=0, health=100):
        if self.course_type != "Lab":
            return

        randomness = random.uniform(-5, 5)

        base = (
            0.7 * self.knowledge +
            0.2 * health -
            0.2 * stress
        )

        self.lab_mid = max(0, min(100, base + randomness))

    def generate_lab_final(self, stress=0, health=100):
        if self.course_type != "Lab":
            return

        randomness = random.uniform(-5, 5)

        base = (
            0.75 * self.knowledge +
            0.2 * health -
            0.2 * stress
        )

        self.lab_final = max(0, min(100, base + randomness))

    def calculate_total_marks(self):

        # THEORY 
        if self.course_type == "Theory":
            if len(self.quiz_marks) < 4 or \
               self.mid_mark is None or \
               self.final_mark is None:
                return None

            best_quizzes = sorted(self.quiz_marks, reverse=True)[:3]
            quiz_avg = sum(best_quizzes) / 3

            total = (
                quiz_avg * 0.2 +
                self.mid_mark * 0.3 +
                self.final_mark * 0.5
            )

            return total

        #  LAB 
        elif self.course_type == "Lab":
            if len(self.lab_evaluations) == 0 or \
               self.lab_mid is None or \
               self.lab_final is None:
                return None

            evaluation_avg = sum(self.lab_evaluations) / len(self.lab_evaluations)

            total = (
                evaluation_avg * 0.4 +
                self.lab_mid * 0.25 +
                self.lab_final * 0.35
            )

            return total

    def calculate_grade(self):
        total = self.calculate_total_marks()

        if total is None:
            return None

        if total >= 80:
            self.grade_point = 4.0
        elif total >= 70:
            self.grade_point = 3.7
        elif total >= 60:
            self.grade_point = 3.0
        elif total >= 50:
            self.grade_point = 2.0
        elif total >= 40:
            self.grade_point = 1.0
        else:
            self.grade_point = 0.0

        return self.grade_point


    def display_info(self):
        print(f"\nCourse: {self.name}")
        print(f"Type: {self.course_type}")
        print(f"Credits: {self.credits}")
        print(f"Knowledge: {self.knowledge:.2f}")
        print(f"Total Marks: {self.calculate_total_marks()}")
        print(f"Grade Point: {self.grade_point}")


class CourseManager:
    def __init__(self):
        self.courses = []

    def add_course(self, name, credits, course_type="Theory", max_lab_evaluations=0):
        self.courses.append(
        Course(name, credits, course_type, max_lab_evaluations)
    )

    def calculate_cgpa(self):
        total_points = 0
        total_credits = 0

        for course in self.courses:
            gp = course.calculate_grade()
            if gp is not None:
                total_points += gp * course.credits
                total_credits += course.credits

        if total_credits == 0:
            return 0

        return total_points / total_credits