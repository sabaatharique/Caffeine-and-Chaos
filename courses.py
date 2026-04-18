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
        self.knowledge += amount
        self.knowledge = max(0, min(100, self.knowledge))

   
    def attend_class(self):
        # To do
        pass


    def get_attendance_percentage(self):
        """Return attendance as a percentage of classes that have actually occurred.
        Falls back to total_classes when no classes have been recorded yet.
        """
        denom = self.occurred_classes if self.occurred_classes > 0 else self.total_classes
        if denom == 0:
            return 0.0
        return min((self.attended_classes / denom) * 100, 100.0)
    
    @property
    def quiz_marks(self) -> list[float]:
        """
        Derive quiz marks from scheduled_quizzes.
        Returns only quizzes where mark is not None (i.e., result system has run).
        Ordered by quiz_number so calculate_total_marks() gets them in the right order.
        Phase 1: always returns [] because mark stays None.
        Phase 2: returns real values once the result system populates quiz["mark"].
        """
        return [
            q["mark"]
            for q in sorted(self.scheduled_quizzes, key=lambda q: q["quiz_number"])
            if q["taken"] and not q["missed"] and q["mark"] is not None
        ]

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
                q["mark"]   = None   # Phase 2 will repopulate this on the new attempt
                q["attempt"] += 1

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
            # Weekly theory: ~3 classes/week × 16 weeks = 48 total
            self.add_course(
                name=c["name"],
                credits=c["credits"],
                course_type="Theory",
                total_classes=48,
                schedule="weekly",
            )

        for lab in result.get("labs", []):
            # Weekly lab: 1/week × 16 = 16; biweekly: 1/2-weeks × 16 = 8
            classes = 16 if lab["schedule"] == "weekly" else 8
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
            multiplier = 16 if c.schedule == "weekly" else 8
            c.total_classes = len(c.weekly_slots) * multiplier
            # Sync lab evaluation targets for lab courses
            if c.course_type == "Lab":
                c.max_lab_evaluations = c.total_classes

    # ── Quiz scheduling 

    # Weighted probability per week for each quiz window.
    # Index 0 = first week of the window.
    _PRE_MID_WEIGHTS  = [1, 1, 2, 4, 5, 5, 4]   # weeks 1-7
    _POST_MID_WEIGHTS = [1, 1, 2, 4, 5, 5, 4, 3] # weeks 8-15

    def schedule_all_quizzes(self):
        """
        Assign 2 pre-midterm + 2 post-midterm quiz dates to every theory course.
        Call this ONCE after apply_schedule() so that weekly_slots are populated.

        Each quiz lands on one of the course's own class slots so it fires
        exactly when the player would normally be in lecture.
        """
        import random

        for course in self.courses:
            if course.course_type != "Theory":
                continue
            if not course.weekly_slots:
                continue  # shouldn't happen, but be safe

            course.scheduled_quizzes = []
            used: set[tuple[int, int]] = set()  # (week, day_idx) → no double-booking
            next_quiz_num = 1

            def _pick(week_pool: list[int], weights: list[int], q_num: int) -> dict | None:
                """
                Attempt up to 30 times to find a unique (week, day_idx) slot.
                Returns a quiz dict or None if every attempt collides.
                """
                for _ in range(30):
                    week = random.choices(week_pool, weights=weights[:len(week_pool)], k=1)[0]
                    day_idx, slot_idx = random.choice(course.weekly_slots)
                    key = (week, day_idx)
                    if key not in used:
                        used.add(key)
                        return {
                            "quiz_number": q_num,
                            "week":     week,
                            "day_idx":  day_idx,
                            "slot_idx": slot_idx,
                            "taken":    False,
                            "missed":   False,
                            "mark":     None,
                            "attempt":  0,
                        }
                return None  # extremely unlikely

            # 2 quizzes before mid (weeks 1-7)
            pre_weeks = list(range(1, 8))
            for _ in range(2):
                q = _pick(pre_weeks, self._PRE_MID_WEIGHTS, next_quiz_num)
                if q:
                    course.scheduled_quizzes.append(q)
                    next_quiz_num += 1

            # 2 quizzes after mid (weeks 8-15)
            post_weeks = list(range(8, 16))
            for _ in range(2):
                q = _pick(post_weeks, self._POST_MID_WEIGHTS, next_quiz_num)
                if q:
                    course.scheduled_quizzes.append(q)
                    next_quiz_num += 1

            # Sort chronologically for the dashboard
            course.scheduled_quizzes.sort(key=lambda q: (q["week"], q["day_idx"]))
