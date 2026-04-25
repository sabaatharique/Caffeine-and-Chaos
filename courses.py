import random

class Course:
    def __init__(self, name, credits, course_type="Theory", max_lab_evaluations=0,
                 total_classes=0, schedule="weekly"):
        self.name = name
        self.credits = credits
        self.course_type = course_type
        self.schedule = schedule           # "weekly" or "biweekly"

        self.knowledge = 10

        # Attendance
        self.total_classes = total_classes
        self.attended_classes = 0
        self.occurred_classes = 0   # classes that have actually fired (attended OR missed)

        # Weekly timetable: list of (day_idx, slot_idx) tuples (0=Monday … 4=Friday)
        self.weekly_slots: list[tuple[int, int]] = []

        # Quizzes
        self.scheduled_quizzes: list[dict] = []

        # Lab assessments (lab_mid / lab_final scheduled slots)
        self.scheduled_lab_assessments: list[dict] = []

        # Theory
        self.mid_mark = None
        self.final_mark = None

        # Lab
        self.lab_evaluations = []
        self.lab_mid = None
        self.lab_final = None
        self.max_lab_evaluations = max_lab_evaluations

        self.grade_point = 0.0


    def add_knowledge(self, amount):
        max_knowledge = 100.0
        if self.total_classes > 0:
            max_knowledge = min(100.0, 10.0 + (self.occurred_classes / self.total_classes) * 90.0)
        
        self.knowledge += amount
        self.knowledge = max(0, min(max_knowledge, self.knowledge))

   
    def attend_class(self):
        # To do
        pass


    def get_attendance_percentage(self):
        """Return attendance as a percentage of total semester classes completed."""
        if self.total_classes == 0:
            return 0.0
        return min((self.attended_classes / self.total_classes) * 100, 100.0)
    
    @property
    def quiz_marks(self) -> list[float]:
        """
        Derive quiz marks from scheduled_quizzes.
        Returns marks for taken quizzes and 0.0 for missed quizzes.
        Ordered by quiz_number so calculate_total_marks() gets them in the right order.
        """
        marks = []
        for q in sorted(self.scheduled_quizzes, key=lambda q: q["quiz_number"]):
            if q["missed"]:
                marks.append(0.0)
            elif q["taken"] and q["mark"] is not None:
                marks.append(q["mark"])
        return marks

    def reset_for_week_repeat(self, week: int) -> None:
        """
        Rewind quiz state for all quizzes scheduled in `week`.
        Called before a week is replayed so the player can re-encounter the quiz prompts.
        Mark is also cleared so Phase 2 can regenerate it cleanly on re-attempt.
        """
        for q in self.scheduled_quizzes:
            if q["week"] == week:
                q["taken"]  = False
                q["missed"] = False
                q["mark"]   = None  
                q["attempt"] += 1

        for la in self.scheduled_lab_assessments:
            if la["week"] == week:
                la["taken"]  = False
                la["missed"] = False
                la["mark"]   = None
                la["attempt"] += 1

    def reset_for_day_repeat(self, week: int, day_idx: int):
        for q in self.scheduled_quizzes:
            if q["week"] == week and q["day_idx"] == day_idx:
                q["taken"]  = False
                q["missed"] = False
                q["mark"]   = None
                q["attempt"] += 1

        for la in self.scheduled_lab_assessments:
            if la["week"] == week and la["day_idx"] == day_idx:
                la["taken"]  = False
                la["missed"] = False
                la["mark"]   = None
                la["attempt"] += 1

    # THEORY SECTION 
    def generate_quiz_mark(self, week, stress=0, sleep=100, health=100):
        if self.course_type != "Theory":
            return None

        if len(self.quiz_marks) >= 4:
            return None

        randomness = random.uniform(-10, 10)
        expected_knowledge = 10.0 + (self.occurred_classes / max(1, self.total_classes)) * 90.0
        progress = self.knowledge / max(1.0, expected_knowledge)
        progress = min(1.0, progress)

        base = (
            0.65 * (progress * 100) +
            0.15 * sleep +
            0.15 * health -
            0.25 * stress
        )

        mark = max(0, min(100, base + randomness))
        self.quiz_marks.append(mark)
        return mark


    def generate_mid_mark(self, week, stress=0, sleep=100, health=100, is_sick=False):
        if self.course_type != "Theory":
            return None
            
        if is_sick:
            self.mid_mark = 0
            return 0

        randomness = random.uniform(-8, 8)
        expected_knowledge = 10.0 + (self.occurred_classes / max(1, self.total_classes)) * 90.0
        progress = self.knowledge / max(1.0, expected_knowledge)
        progress = min(1.0, progress)

        base = (
            0.7 * (progress * 100) +
            0.15 * sleep +
            0.15 * health -
            0.2 * stress
        )

        self.mid_mark = max(0, min(100, base + randomness))
        return self.mid_mark


    def generate_final_mark(self, week, stress=0, sleep=100, health=100, is_sick=False):
        if self.course_type != "Theory":
            return None
            
        if is_sick:
            self.final_mark = 0
            return 0

        randomness = random.uniform(-5, 5)
        expected_knowledge = 10.0 + (self.occurred_classes / max(1, self.total_classes)) * 90.0
        progress = self.knowledge / max(1.0, expected_knowledge)
        progress = min(1.0, progress)

        base = (
            0.75 * (progress * 100) +
            0.1 * sleep +
            0.15 * health -
            0.2 * stress
        )

        self.final_mark = max(0, min(100, base + randomness))
        return self.final_mark

    # LAB SECTION
    def generate_lab_evaluation(self, week, stress=0, health=100):

        if self.course_type != "Lab":
            return None

        if len(self.lab_evaluations) >= self.max_lab_evaluations:
            return None

        randomness = random.uniform(-5, 5)
        expected_knowledge = 10.0 + (self.occurred_classes / max(1, self.total_classes)) * 90.0
        progress = self.knowledge / max(1.0, expected_knowledge)
        progress = min(1.0, progress)

        base = (
            0.6 * (progress * 100) +
            0.2 * health -
            0.3 * stress
        )

        mark = max(0, min(100, base + randomness))
        self.lab_evaluations.append(mark)
        return mark

    def generate_lab_mid(self, week, stress=0, health=100, is_sick=False):
        if self.course_type != "Lab":
            return None

        for la in self.scheduled_lab_assessments:
            if la["assessment_type"] == "lab_mid" and la["missed"]:
                self.lab_mid = 0
                return 0
            
        if is_sick:
            self.lab_mid = 0
            return 0

        randomness = random.uniform(-5, 5)
        expected_knowledge = 10.0 + (self.occurred_classes / max(1, self.total_classes)) * 90.0
        progress = self.knowledge / max(1.0, expected_knowledge)
        progress = min(1.0, progress)

        base = (
            0.7 * (progress * 100) +
            0.2 * health -
            0.2 * stress
        )

        self.lab_mid = max(0, min(100, base + randomness))
        return self.lab_mid

    def generate_lab_final(self, week, stress=0, health=100, is_sick=False):
        if self.course_type != "Lab":
            return None
            
        for la in self.scheduled_lab_assessments:
            if la["assessment_type"] == "lab_final" and la["missed"]:
                self.lab_final = 0
                return 0

        if is_sick:
            self.lab_final = 0
            return 0

        randomness = random.uniform(-5, 5)
        expected_knowledge = 10.0 + (self.occurred_classes / max(1, self.total_classes)) * 90.0
        progress = self.knowledge / max(1.0, expected_knowledge)
        progress = min(1.0, progress)

        base = (
            0.75 * (progress * 100) +
            0.2 * health -
            0.2 * stress
        )

        self.lab_final = max(0, min(100, base + randomness))
        return self.lab_final

    def calculate_total_marks(self):
        """
        Returns the final percentage (0–100) for this course.
        Returns None if not all assessments are in yet.
        """
        # THEORY 
        if self.course_type == "Theory":
            if len(self.quiz_marks) < 4 or \
               self.mid_mark is None or \
               self.final_mark is None:
                return None

            best_quizzes = sorted(self.quiz_marks, reverse=True)[:3]
            quiz_avg = sum(best_quizzes) / len(best_quizzes) if best_quizzes else 0

            total_percentage = (
                quiz_avg * 0.15 +
                self.mid_mark * 0.25 +
                self.final_mark * 0.50 +
                self.get_attendance_percentage() * 0.10
            )
            return max(0.0, min(100.0, total_percentage))

        #  LAB 
        elif self.course_type == "Lab":
            if (self.max_lab_evaluations > 0 and len(self.lab_evaluations) == 0) or \
               self.lab_mid is None or \
               self.lab_final is None:
                return None

            evaluation_avg = sum(self.lab_evaluations) / len(self.lab_evaluations) if self.lab_evaluations else 0

            total_percentage = (
                evaluation_avg * 0.15 +
                self.lab_mid * 0.25 +
                self.lab_final * 0.50 +
                self.get_attendance_percentage() * 0.10
            )
            return max(0.0, min(100.0, total_percentage))

    def calculate_midterm_percentage(self):
        """Return the weighted mark through the midterm only (quizzes + mid exam, attendance).
        Returns None if midterm has not been taken yet.
        """
        if self.course_type == "Theory":
            if self.mid_mark is None:
                return None
            best_quizzes = sorted(self.quiz_marks, reverse=True)[:3]
            quiz_avg = sum(best_quizzes) / len(best_quizzes) if best_quizzes else 0
            # Scale so quiz+mid+attendance = 50% total weight → normalise to 100
            total = (
                quiz_avg * 0.15 +
                self.mid_mark * 0.25 +
                self.get_attendance_percentage() * 0.10
            ) / 0.50 * 100  # rescale to 100
            return max(0.0, min(100.0, total))
        elif self.course_type == "Lab":
            if self.lab_mid is None:
                return None
            evaluation_avg = sum(self.lab_evaluations) / len(self.lab_evaluations) if self.lab_evaluations else 0
            total = (
                evaluation_avg * 0.15 +
                self.lab_mid * 0.25 +
                self.get_attendance_percentage() * 0.10
            ) / 0.50 * 100
            return max(0.0, min(100.0, total))
        return None

    def is_attendance_eligible(self):
        """Return True if the student meets the 85% attendance requirement.
        Uses occurred_classes (classes actually held so far) as the denominator,
        so a student who attended every class to date is never wrongly flagged.
        At the end of the semester occurred_classes ≈ total_classes.
        """
        if self.occurred_classes == 0:
            return True
        pct = (self.attended_classes / self.occurred_classes) * 100
        return pct >= 85.0

    def get_occurred_attendance_percentage(self) -> float:
        """Attendance % out of occurred (held) classes — used for real-time display."""
        if self.occurred_classes == 0:
            return 0.0
        return min((self.attended_classes / self.occurred_classes) * 100, 100.0)

    @staticmethod
    def _percentage_to_grade_point(pct: float) -> float:
        """Map a percentage mark to a GPA grade point using the official table."""
        if pct >= 80:  return 4.00  # A+
        if pct >= 75:  return 3.75  # A
        if pct >= 70:  return 3.50  # A-
        if pct >= 65:  return 3.25  # B+
        if pct >= 60:  return 3.00  # B
        if pct >= 55:  return 2.75  # B-
        if pct >= 50:  return 2.50  # C+
        if pct >= 45:  return 2.25  # C
        if pct >= 40:  return 2.00  # D
        return 0.00                 # F

    @staticmethod
    def _percentage_to_letter(pct: float) -> str:
        """Map a percentage mark to a letter grade string."""
        if pct >= 80:  return "A+"
        if pct >= 75:  return "A"
        if pct >= 70:  return "A-"
        if pct >= 65:  return "B+"
        if pct >= 60:  return "B"
        if pct >= 55:  return "B-"
        if pct >= 50:  return "C+"
        if pct >= 45:  return "C"
        if pct >= 40:  return "D"
        return "F"

    @staticmethod
    def required_knowledge_for_pct(target_pct, sleep, health, stress, expected_knowledge, course_type="Theory"):
        """
        Calculate the raw knowledge required to hit a specific final percentage,
        assuming 100% attendance and average stat efficiency.
        """
        # If target is lower than what attendance alone provides (10%)
        # cap at the minimum to prevent negative knowledge targets
        needed_from_assessments = max(0.0, target_pct - 10.0)

        # Let x = progress * 100
        # For Theory:
        # quiz_avg  = 0.65*x + 0.15*sleep + 0.15*health - 0.25*stress
        # mid_mark  = 0.70*x + 0.15*sleep + 0.15*health - 0.20*stress
        # fin_mark  = 0.75*x + 0.10*sleep + 0.15*health - 0.20*stress
        # total_from_assessments = 0.15*quiz_avg + 0.25*mid_mark + 0.50*fin_mark
        #
        # For Lab:
        # eval_avg  = 0.60*x + 0.2*health - 0.3*stress
        # mid_mark  = 0.70*x + 0.2*health - 0.2*stress
        # fin_mark  = 0.75*x + 0.2*health - 0.2*stress
        
        if course_type == "Theory":
            weight_x = 0.15 * 0.65 + 0.25 * 0.70 + 0.50 * 0.75
            weight_sleep = 0.15 * 0.15 + 0.25 * 0.15 + 0.50 * 0.10
            weight_health = 0.15 * 0.15 + 0.25 * 0.15 + 0.50 * 0.15
            weight_stress = 0.15 * (-0.25) + 0.25 * (-0.20) + 0.50 * (-0.20)
            
            const_term = weight_sleep * sleep + weight_health * health + weight_stress * stress
        else: # Lab
            weight_x = 0.15 * 0.60 + 0.25 * 0.70 + 0.50 * 0.75
            weight_health = 0.15 * 0.20 + 0.25 * 0.20 + 0.50 * 0.20
            weight_stress = 0.15 * (-0.30) + 0.25 * (-0.20) + 0.50 * (-0.20)
            
            const_term = weight_health * health + weight_stress * stress

        # We know: needed_from_assessments = weight_x * x + const_term
        # Solving for x:
        x = (needed_from_assessments - const_term) / weight_x
        
        # We need to map x back from percentage (x = progress * 100) back to actual knowledge
        progress = x / 100.0
        
        # Don't return negative knowledge
        return max(0.0, progress * expected_knowledge)

    def calculate_grade(self):
        """Compute grade point from final percentage. Returns None if incomplete."""
        pct = self.calculate_total_marks()
        if pct is None:
            return None
        self.grade_point = self._percentage_to_grade_point(pct)
        return self.grade_point

    def get_letter_grade(self) -> str:
        """Return letter grade (A+, A, …, F) or '—' if not ready."""
        pct = self.calculate_total_marks()
        if pct is None:
            return "—"
        return self._percentage_to_letter(pct)


    def display_info(self):
        print(f"\nCourse: {self.name}")
        print(f"Type: {self.course_type}")
        print(f"Credits: {self.credits}")
        print(f"Knowledge: {self.knowledge:.2f}")
        pct = self.calculate_total_marks()
        print(f"Total Marks: {pct:.1f}%" if pct is not None else "Total Marks: N/A")
        print(f"Letter Grade: {self.get_letter_grade()}")
        print(f"Grade Point: {self.grade_point}")


class CourseManager:
    def __init__(self):
        self.courses = []
        self.midterm_schedule: list[dict] = []   # [{"course", "week", "day_idx"}, ...]
        self.final_schedule: list[dict] = []

    def generate_midterm_schedule(self):
        from events import generate_exam_schedule
        from environment import MIDTERM_EXAM_WEEKS, MIDTERM_EXAM_DAYS
        theory = [c for c in self.courses if c.course_type == "Theory"]
        self.midterm_schedule = generate_exam_schedule(theory, MIDTERM_EXAM_WEEKS, MIDTERM_EXAM_DAYS)

    def generate_final_schedule(self):
        from events import generate_exam_schedule
        from environment import FINAL_EXAM_WEEKS, FINAL_EXAM_DAYS
        theory = [c for c in self.courses if c.course_type == "Theory"]
        self.final_schedule = generate_exam_schedule(theory, FINAL_EXAM_WEEKS, FINAL_EXAM_DAYS)


    def add_course(self, name, credits, course_type="Theory", max_lab_evaluations=0,
                   total_classes=0, schedule="weekly"):
        self.courses.append(
            Course(name, credits, course_type, max_lab_evaluations,
                   total_classes=total_classes, schedule=schedule)
        )

    def setup_from_wizard(self, result: dict):
        """Populate courses from the wizard result dict."""
        self.courses = []

        for c in result.get("courses", []):
            # Weekly theory: ~3 classes/week × 15 weeks = 45 total
            self.add_course(
                name=c["name"],
                credits=c["credits"],
                course_type="Theory",
                total_classes=45,
                schedule="weekly",
            )

        for lab in result.get("labs", []):
            # Weekly lab: 1/week × 15 = 15; biweekly: 1/2-weeks × 15 = 8
            classes = 15 if lab["schedule"] == "weekly" else 8
            self.add_course(
                name=lab["name"],
                credits=lab["credits"],
                course_type="Lab",
                max_lab_evaluations=classes,
                total_classes=classes,
                schedule=lab["schedule"],
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

    def get_average_knowledge(self):
        if not self.courses:
            return 0.0
        return sum(c.knowledge * c.credits for c in self.courses) / sum(c.credits for c in self.courses)

    def reset_quizzes_for_week(self, week: int) -> None:
        """Rewind quiz state across all courses for the given week."""
        for course in self.courses:
            course.reset_for_week_repeat(week)

    def reset_quizzes_for_day(self, day_count: int) -> None:
        """Rewind quiz state across all courses for a specific day."""
        week = ((day_count - 1) // 7) + 1
        day_idx = (day_count - 1) % 7
        for course in self.courses:
            course.reset_for_day_repeat(week, day_idx)

    def apply_schedule(self, schedule: dict):
        """Apply a schedule dict {(day_idx, slot_idx): Course} onto course objects."""
        # Clear existing slots
        for c in self.courses:
            c.weekly_slots = []
        # Assign new slots and recalculate targets
        for (day_idx, slot_idx), course in schedule.items():
            if course in self.courses:
                course.weekly_slots.append((day_idx, slot_idx))
        
        # Recalculate total_classes based on assigned slots
        for c in self.courses:
            c.weekly_slots.sort()
            multiplier = 15 if c.schedule == "weekly" else 8
            c.total_classes = len(c.weekly_slots) * multiplier
            # Sync lab evaluation targets for lab courses
            if c.course_type == "Lab":
                c.max_lab_evaluations = c.total_classes

    # Quiz scheduling 

    # Weighted probability per week for each quiz window.
    # Index 0 = first week of the window.

    def schedule_all_quizzes(self):
        """
        Assign 2 pre-midterm + 2 post-midterm quiz dates to every theory course.
        Call this ONCE after apply_schedule() so that weekly_slots are populated.

        Each quiz lands on one of the course's own class slots so it fires
        exactly when the player would normally be in lecture.
        """
        import events

        for course in self.courses:
            if course.course_type != "Theory":
                continue
            if not course.weekly_slots:
                continue  # shouldn't happen, but be safe

            used: set[tuple[int, int]] = set()  # (week, day_idx) → no double-booking
            course.scheduled_quizzes = events.generate_quiz_schedule(course.weekly_slots, used)

            # Sort chronologically for the dashboard
            course.scheduled_quizzes.sort(key=lambda q: (q["week"], q["day_idx"]))

    # Lab assessment scheduling

    def schedule_all_lab_assessments(self):
        """
        Assign 1 lab-mid (week 6 or 7) + 1 lab-final (week 14 or 15) to every
        lab course.  Call this ONCE after apply_schedule().
        """
        import events

        for course in self.courses:
            if course.course_type != "Lab":
                continue
            if not course.weekly_slots:
                continue

            course.scheduled_lab_assessments = events.generate_lab_assessment_schedule(
                course.weekly_slots
            )
            course.scheduled_lab_assessments.sort(key=lambda a: (a["week"], a["day_idx"]))
