import json
import os

SAVE_FILE = "save_data.json"


def _student_to_dict(student) -> dict:
    return {
        "type_mult": student.type_mult,
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
    }


def _student_from_dict(data: dict, student):
    """Restore student attributes from a dict (in-place)."""
    student.type_mult = data.get("type_mult", 1.0)
    student.sleep = data.get("sleep", 90)
    student.health = data.get("health", 80)
    student.stress = data.get("stress", 30)
    student.motivation = data.get("motivation", 60)
    student.hunger = data.get("hunger", 50)
    student.hours_since_last_meal = data.get("hours_since_last_meal", 0.0)
    student.attendance = data.get("attendance", 0)
    student.consecutive_stress_days = data.get("consecutive_stress_days", 0)
    student.burnout_days_remaining = data.get("burnout_days_remaining", 5)
    student.is_sick             = data.get("is_sick", False)
    student.sick_days_remaining = data.get("sick_days_remaining", 0)
    student._stress_history     = data.get("stress_history", [])
    student._health_history     = data.get("health_history", [])
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
        "quiz_marks": course.quiz_marks,
        "mid_mark": course.mid_mark,
        "final_mark": course.final_mark,
        "lab_evaluations": course.lab_evaluations,
        "lab_mid": course.lab_mid,
        "lab_final": course.lab_final,
        "grade_point": course.grade_point,
        "weekly_slots": [list(s) for s in course.weekly_slots],
        "scheduled_quizzes": course.scheduled_quizzes,
        "occurred_classes": course.occurred_classes,
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
        c.quiz_marks = d.get("quiz_marks", [])
        c.mid_mark = d.get("mid_mark")
        c.final_mark = d.get("final_mark")
        c.lab_evaluations = d.get("lab_evaluations", [])
        c.lab_mid = d.get("lab_mid")
        c.lab_final = d.get("lab_final")
        c.grade_point = d.get("grade_point", 0.0)
        c.weekly_slots = [tuple(s) for s in d.get("weekly_slots", [])]
        c.scheduled_quizzes = d.get("scheduled_quizzes", [])
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
              attend_all_today: bool = False) -> bool:
    """
    Write all game state to SAVE_FILE.
    Returns True on success, False on error.
    """
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
            "quizzes_resolved_today": set(data.get("quizzes_resolved_today", [])),
            "attend_all_today": data.get("attend_all_today", False),
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
