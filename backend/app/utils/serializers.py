"""出参序列化辅助：ORM → 前端友好 dict（int UNIX 时间戳 → ISO 字符串）。"""
from datetime import datetime


def iso_ts(ts) -> str | None:
    """把 int UNIX 时间戳或 datetime 转成 ISO 字符串（YYYY-MM-DDTHH:MM:SS）。"""
    if ts is None:
        return None
    if isinstance(ts, datetime):
        return ts.strftime("%Y-%m-%dT%H:%M:%S")
    try:
        return datetime.fromtimestamp(int(ts)).strftime("%Y-%m-%dT%H:%M:%S")
    except (ValueError, OSError, TypeError):
        return None


def user_out(user) -> dict:
    """user_rft 对象 → 教师端前端友好的用户 dict。"""
    return {
        "id": user.id,
        "uid": user.uid,
        "username": user.uid,
        "name": user.name,
        "role": user.role,
        "gender": user.gender,
        "college": user.college,
        "department": user.college,
        "grade": user.grade,
        "class_name": user.class_name,
        "major": user.major,
        "email": None,
        "phone": None,
        "position": None,
        "avatar": None,
        "status": user.status,
        "created_at": iso_ts(user.created_at),
    }


def course_out(course) -> dict:
    """courses 对象 → 前端友好 dict（status int → draft/published/archived）。"""
    status_map = {0: "draft", 1: "published", 100: "archived"}
    return {
        "id": course.id,
        "name": course.name,
        "code": None,
        "description": course.description,
        "status": status_map.get(course.status, "draft"),
        "cover": None,
        "open_time": None,
        "teacher_user_id": course.teacher_user_id,
        "created_by": course.created_by,
        "created_at": iso_ts(course.created_at),
    }
