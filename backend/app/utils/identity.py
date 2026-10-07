"""用户身份辅助：统一处理 buct_cip 库「学号/工号 vs user_rft.id」两套 ID 约定。"""


def numeric_uid(user) -> int | None:
    """将 user_rft.uid（学号/工号字符串）转成数值 ID；失败返回 None。

    学校库中 class_record.uid、personal_messages.sender_id / receiver_id 存的是
    数值学号/工号（如 2025060144、1001），而 user_rft.uid 是字符串；本函数统一转换，
    供读写这些「数值 ID」列时使用。
    """
    try:
        return int(user.uid)
    except (ValueError, TypeError):
        return None


def class_member_users(db, class_id: int) -> list:
    """返回班级学生（user_rft 用户对象列表）。

    班级成员关系在 class_record（uid 存数值学号），需经 `str(uid)` 反查 user_rft.uid，
    最终得到 user_rft 用户对象。延迟导入避免模块加载期循环依赖。
    """
    from sqlalchemy import select

    from app.models.class_ import ClassRecord
    from app.models.user import User

    numeric_uids = list(
        db.scalars(
            select(ClassRecord.uid).where(
                ClassRecord.class_id == class_id, ClassRecord.role == 1
            )
        ).all()
    )
    if not numeric_uids:
        return []
    str_uids = [str(u) for u in numeric_uids]
    return list(db.scalars(select(User).where(User.uid.in_(str_uids))).all())
