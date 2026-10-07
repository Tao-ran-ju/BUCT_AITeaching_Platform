"""用户服务：登录鉴权、SSO 建档、用户 CRUD、个人资料。"""
import secrets
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import (
    AuthError,
    ConflictError,
    NotFoundError,
    ValidateError,
)
from app.models.user import ROLE_TEACHER, TeacherActor, User
from app.schemas.user import UserCreate, UserUpdate
from app.utils.pagination import normalize_page, paginate
from app.utils.security import create_token, hash_password, verify_password


class UserService:
    """用户相关的全部业务逻辑。"""

    @staticmethod
    def _now() -> int:
        return int(time.time())

    @staticmethod
    def authenticate(db: Session, username: str, password: str) -> User:
        """校验账号密码（uid + bcrypt），成功返回用户。"""
        user = db.scalar(select(User).where(User.uid == username))
        if not user or not verify_password(password, user.password_hash):
            raise AuthError("用户名或密码错误")
        if user.status != 0:
            raise AuthError("账号已被禁用，请联系管理员")
        return user

    @staticmethod
    def issue_token(user: User) -> str:
        """为用户签发 JWT。"""
        return create_token(user.id)

    @staticmethod
    def create_user(db: Session, data: UserCreate, created_by: int = 0) -> User:
        """创建用户（教师手动建档学生用；密码缺省生成随机密码）。"""
        exists = db.scalar(select(User).where(User.uid == data.uid))
        if exists:
            raise ConflictError("该学号/工号已存在")
        password = data.password or secrets.token_urlsafe(16)
        user = User(
            uid=data.uid,
            password_hash=hash_password(password),
            name=data.name,
            role=data.role,
            gender=data.gender,
            college=data.college,
            grade=data.grade,
            class_name=data.class_name,
            major=data.major,
            status=0,
            created_at=UserService._now(),
            edited_at=UserService._now(),
            created_by=created_by,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def list_users(db: Session, page: int | None, page_size: int | None,
                   role: int | None = None, keyword: str | None = None) -> dict:
        """分页查询用户，支持按角色（0/1）/ 关键字过滤。"""
        page, page_size = normalize_page(page, page_size)
        stmt = select(User)
        if role is not None:
            stmt = stmt.where(User.role == role)
        if keyword:
            like = f"%{keyword}%"
            stmt = stmt.where((User.name.like(like)) | (User.uid.like(like)))
        total = len(db.scalars(stmt).all())
        rows = db.scalars(
            stmt.order_by(User.id.desc()).offset((page - 1) * page_size).limit(page_size)
        ).all()
        return paginate(rows, total, page, page_size)

    @staticmethod
    def update_profile(db: Session, user: User, data: UserUpdate) -> User:
        """更新当前用户个人资料。"""
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        user.edited_at = UserService._now()
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def change_password(db: Session, user: User, old_password: str, new_password: str) -> None:
        """修改密码：需校验旧密码。"""
        if not verify_password(old_password, user.password_hash):
            raise ValidateError("旧密码不正确")
        user.password_hash = hash_password(new_password)
        user.edited_at = UserService._now()
        db.commit()

    @staticmethod
    def get_or_raise(db: Session, user_id: int) -> User:
        user = db.get(User, user_id)
        if not user:
            raise NotFoundError("用户不存在")
        return user

    @staticmethod
    def get_or_create_sso_user(db: Session, uid: str, name: str | None, role: int) -> User:
        """统一 SSO 建档：按 uid 查找，不存在则创建（教师同时写入 teacher_actors）。

        密码写入随机不可知值，禁用密码登录——SSO 用户只能通过共享密钥换 token。
        """
        user = db.scalar(select(User).where(User.uid == uid))
        if user:
            changed = False
            if user.role != role:
                user.role = role
                changed = True
            if name and user.name != name:
                user.name = name
                changed = True
            if changed:
                user.edited_at = UserService._now()
                db.commit()
                db.refresh(user)
            if role == ROLE_TEACHER:
                UserService._ensure_teacher_actor(db, uid, name or user.name)
            return user

        user = User(
            uid=uid,
            password_hash=hash_password(secrets.token_urlsafe(24)),
            name=name or uid,
            role=role,
            gender=0,
            college="",
            status=0,
            created_at=UserService._now(),
            edited_at=UserService._now(),
            created_by=0,
        )
        db.add(user)
        db.flush()
        if role == ROLE_TEACHER:
            UserService._ensure_teacher_actor(db, uid, name or uid)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def _ensure_teacher_actor(db: Session, uid: str, name: str) -> None:
        """确保教师账号在 teacher_actors 表有对应记录（幂等）。"""
        actor = db.scalar(select(TeacherActor).where(TeacherActor.uid == uid))
        if not actor:
            db.add(TeacherActor(
                uid=uid, name=name, status=0, created_at=UserService._now()
            ))
            db.flush()
