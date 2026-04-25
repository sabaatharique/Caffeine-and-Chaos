import json
import os

SAVE_FILE = "save_data.json"


def _default_stats() -> dict:
    """Return a zeroed lifetime-stats dict (used when loading old saves)."""
    return {
        "hours_studied": 0.0, "hours_slept": 0.0, "hours_relaxed": 0.0,
        "hours_in_class": 0.0, "hours_wifi_outage": 0.0,
        "coffees_drunk": 0, "meals_eaten": 0,
        "classes_attended": 0, "classes_skipped": 0,
        "burnout_occurrences": 0, "days_burnt_out": 0,
        "times_sick": 0, "total_sick_days": 0,
        "longest_sick_streak": 0, "_current_sick_streak": 0,
        "peak_stress": 0, "lowest_health": 100, "peak_motivation": 0,
    }


def _student_to_dict(student) -> dict:
    return {
        "type_mult": student.type_mult,
        "target_cgpa": student.target_cgpa,
        "sleep": student.sleep,
        "health": student.health,
        "stress": student.stress,
        "motivation": student.motivation,
        "hunger": student.hunger,
        "hours_since_last_meal": student.hours_since_last_meal,
        "attendance": student.attendance,
        "consecutive_stress_days": student.consecutive_stress_days,
        "burnout_days_remaining": student.burnout_days_remaining,
        "is_sick": student.is_sick,
        "sick_days_remaining": student.sick_days_remaining,
        "stress_history": student._stress_history,
        "health_history": student._health_history,
        "week_stress_snapshots":     student._week_stress_snapshots,
        "week_health_snapshots":     student._week_health_snapshots,
        "week_motivation_snapshots": student._week_motivation_snapshots,
        "week_study_hours":          student._week_study_hours,
        "week_sleep_hours":          student._week_sleep_hours,
        "week_relax_hours":          student._week_relax_hours,
        "week_class_hours":          student._week_class_hours,
        "today_study_hours":         student._today_study_hours,
        "today_sleep_hours":         student._today_sleep_hours,
        "today_relax_hours":         student._today_relax_hours,
        "today_class_hours":         student._today_class_hours,
        "snapshot_week":             student._snapshot_week,
        "stats": student.stats,
    }


def _student_from_dict(data: dict, student):
    """Restore student attributes from a dict (in-place)."""
    student.type_mult = data.get("type_mult", 1.0)
    student.target_cgpa = data.get("target_cgpa", 0.0)
    student.sleep = data.get("sleep", 90)
    student.health = data.get("health", 80)
    student.stress = data.get("stress", 30)
    student.motivation = data.get("motivation", 60)
    student.hunger = data.get("hunger", 50)
    student.hours_since_last_meal = data.get("hours_since_last_meal", 0.0)
    student.attendance = data.get("attendance", 0)
    student.consecutive_stress_days = data.get("consecutive_stress_days", 0)
    student.burnout_days_remaining = data.get("burnout_days_remaining", 5)
    student.is_sick = data.get("is_sick", False)
    student.sick_days_remaining = data.get("sick_days_remaining", 0)
    student._stress_history     = data.get("stress_history", [])
    student._health_history     = data.get("health_history", [])
    student._week_stress_snapshots     = data.get("week_stress_snapshots", [])
    student._week_health_snapshots     = data.get("week_health_snapshots", [])
    student._week_motivation_snapshots = data.get("week_motivation_snapshots", [])
    student._week_study_hours          = data.get("week_study_hours", [])
    student._week_sleep_hours          = data.get("week_sleep_hours", [])
    student._week_relax_hours          = data.get("week_relax_hours", [])
    student._week_class_hours          = data.get("week_class_hours", [])
    student._today_study_hours         = data.get("today_study_hours", 0.0)
    student._today_sleep_hours         = data.get("today_sleep_hours", 0.0)
    student._today_relax_hours         = data.get("today_relax_hours", 0.0)
    student._today_class_hours         = data.get("today_class_hours", 0.0)
    student._snapshot_week             = data.get("snapshot_week", 0)
    # Merge saved stats with defaults so old saves load without KeyError
    saved_stats = data.get("stats", {})
    student.stats = {**_default_stats(), **saved_stats}
    student.update_action_status()


def _course_to_dict(course) -> dict:
    return {
        "name": course.name,
        "credits": course.credits,
        "course_type": course.course_type,
        "schedule": course.schedule,
        "knowledge": course.knowledge,
        "total_classes": course.total_classes,
        "attended_classes": course.attended_classes,
        "max_lab_evaluations": course.max_lab_evaluations,
        "mid_mark": course.mid_mark,
        "final_mark": course.final_mark,
        "lab_evaluations": course.lab_evaluations,
        "lab_mid": course.lab_mid,
        "lab_final": course.lab_final,
        "grade_point": course.grade_point,
        "scheduled_quizzes": course.scheduled_quizzes,
        "scheduled_lab_assessments": getattr(course, "scheduled_lab_assessments", []),
        "occurred_classes": course.occurred_classes,
        "weekly_slots": getattr(course, "weekly_slots", []),
    }


def _courses_from_dict(data_list: list, course_manager):
    """Rebuild course_manager.courses from saved list."""
    from courses import Course
    course_manager.courses = []
    for d in data_list:
        c = Course(
            name=d["name"],
            credits=d["credits"],
            course_type=d["course_type"],
            max_lab_evaluations=d.get("max_lab_evaluations", 0),
            total_classes=d.get("total_classes", 0),
            schedule=d.get("schedule", "weekly"),
        )
        c.knowledge = d.get("knowledge", 10)
        c.attended_classes = d.get("attended_classes", 0)
        c.mid_mark = d.get("mid_mark")
        c.final_mark = d.get("final_mark")
        c.lab_evaluations = d.get("lab_evaluations", [])
        c.lab_mid = d.get("lab_mid")
        c.lab_final = d.get("lab_final")
        c.grade_point = d.get("grade_point", 0.0)
        c.weekly_slots = [tuple(s) for s in d.get("weekly_slots", [])]
        c.scheduled_quizzes = d.get("scheduled_quizzes", [])
        c.scheduled_lab_assessments = d.get("scheduled_lab_assessments", [])
        # Migration guard for older saves
        for i, q in enumerate(c.scheduled_quizzes):
            if "quiz_number" not in q:
                q["quiz_number"] = i + 1
            if "attempt" not in q:
                q["attempt"] = 0
            if "mark" not in q:
                q["mark"] = None
        c.occurred_classes = d.get("occurred_classes", 0)
        course_manager.courses.append(c)


def _actions_to_serialisable(day_actions: list) -> list:
    """
    Convert a day_actions list  [(action, hours, data), ...]  to JSON-safe form.
    'data' is either None or a Course object; store only the course name.
    """
    out = []
    for action, hours, data in day_actions:
        out.append({
            "action": action,
            "hours": hours,
            "course_name": data.name if data is not None else None,
        })
    return out


def _actions_from_serialisable(raw: list, course_manager) -> list:
    """Reverse of _actions_to_serialisable; resolve course names back to objects."""
    out = []
    name_map = {c.name: c for c in course_manager.courses}
    for item in raw:
        course = name_map.get(item.get("course_name")) if item.get("course_name") else None
        out.append((item["action"], item["hours"], course))
    return out


def save_game(student, course_manager,
              time_of_day, day_count, week_count, day_in_week,
              burnout_active, day_over,
              day_actions: list, week_actions: list,
              classes_resolved: set = None,
              quizzes_resolved: set = None,
              attend_all_today: bool = False,
              exam_period_type: str = "",
              exam_idx: int = 0,
              exam_copy_to_all: bool = False,
              exam_prep_actions: list = None,
              pre_mid_week_template: list = None) -> bool:
    """
    Write all game state to SAVE_FILE.
    Returns True on success, False on error.
    """
    # Serialise midterm/final schedules
    name_to_str = lambda s: [{"course_name": e["course"].name, "week": e["week"], "day_idx": e["day_idx"]} for e in s]
    payload = {
        "student": _student_to_dict(student),
        "courses": [_course_to_dict(c) for c in course_manager.courses],
        "time_of_day": time_of_day,
        "day_count": day_count,
        "week_count": week_count,
        "day_in_week": day_in_week,
        "burnout_active": burnout_active,
        "day_over": day_over,
        "day_actions": _actions_to_serialisable(day_actions),
        "week_actions": [_actions_to_serialisable(d) for d in week_actions],
        "classes_resolved_today": list(classes_resolved) if classes_resolved else [],
        "quizzes_resolved_today": list(quizzes_resolved) if quizzes_resolved else [],
        "attend_all_today": attend_all_today,
        # Exam period state
        "midterm_schedule": name_to_str(course_manager.midterm_schedule),
        "final_schedule":   name_to_str(course_manager.final_schedule),
        "exam_period_type": exam_period_type,
        "exam_idx":         exam_idx,
        "exam_copy_to_all": exam_copy_to_all,
        "exam_prep_actions": _actions_to_serialisable(exam_prep_actions or []),
        "pre_mid_week_template": [_actions_to_serialisable(day) for day in (pre_mid_week_template or [])],
    }
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        return True
    except Exception as e:
        print(f"[SaveGame] Failed to save: {e}")
        return False


def load_game(student, course_manager) -> dict | None:
    """
    Read SAVE_FILE and populate student + course_manager in-place.
    Returns a dict with the remaining scalar state on success, or None if
    no save file exists / the file is corrupt.

    Returned dict keys:
        time_of_day, day_count, week_count, day_in_week,
        burnout_active, day_over, day_actions, week_actions
    """
    if not os.path.exists(SAVE_FILE):
        return None
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        _student_from_dict(data["student"], student)
        _courses_from_dict(data["courses"], course_manager)

        day_actions  = _actions_from_serialisable(data.get("day_actions", []),  course_manager)
        week_actions = [
            _actions_from_serialisable(d, course_manager)
            for d in data.get("week_actions", [])
        ]

        # Restore exam schedules
        name_map = {c.name: c for c in course_manager.courses}
        course_manager.midterm_schedule = [
            {"course": name_map[s["course_name"]], "week": s["week"], "day_idx": s["day_idx"]}
            for s in data.get("midterm_schedule", []) if s["course_name"] in name_map
        ]
        course_manager.final_schedule = [
            {"course": name_map[s["course_name"]], "week": s["week"], "day_idx": s["day_idx"]}
            for s in data.get("final_schedule", []) if s["course_name"] in name_map
        ]
        exam_prep_actions = _actions_from_serialisable(data.get("exam_prep_actions", []), course_manager)
        pre_mid_week_template = [
            _actions_from_serialisable(day, course_manager)
            for day in data.get("pre_mid_week_template", [])
        ]

        return {
            "time_of_day": data.get("time_of_day", 8.0),
            "day_count": data.get("day_count", 1),
            "week_count": data.get("week_count", 1),
            "day_in_week": data.get("day_in_week", 1),
            "burnout_active": data.get("burnout_active", False),
            "day_over": data.get("day_over", False),
            "day_actions": day_actions,
            "week_actions": week_actions,
            "classes_resolved_today": set(data.get("classes_resolved_today", [])),
            "quizzes_resolved_today": {tuple(x) for x in data.get("quizzes_resolved_today", []) if isinstance(x, (list, tuple))},
            "attend_all_today": data.get("attend_all_today", False),
            "exam_period_type": data.get("exam_period_type", ""),
            "exam_idx": data.get("exam_idx", 0),
            "exam_copy_to_all": data.get("exam_copy_to_all", False),
            "exam_prep_actions": exam_prep_actions,
            "pre_mid_week_template": pre_mid_week_template,
        }
    except Exception as e:
        print(f"[SaveGame] Failed to load: {e}")
        return None


def delete_save() -> None:
    """Remove the save file (used after starting a new game)."""
    if os.path.exists(SAVE_FILE):
        os.remove(SAVE_FILE)


def save_exists() -> bool:
    return os.path.exists(SAVE_FILE)
