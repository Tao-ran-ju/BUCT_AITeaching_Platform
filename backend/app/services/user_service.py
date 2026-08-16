"""用户服务：登录鉴权、用户 CRUD、个人资料。"""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.exceptions import AuthError, ConflictError, NotFoundError, ValidateError
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.utils.pagination import normalize_page, paginate
from app.utils.security import create_token, hash_password, verify_password


class UserService:
    """用户相关的全部业务逻辑。"""

    @staticmethod
    def authenticate(db: Session, username: str, password: str) -> User:
        """校验账号密码，成功返回用户。"""
        user = db.scalar(select(User).where(User.username == username))
        if not user or not verify_password(password, user.password_hash):
            raise AuthError("用户名或密码错误")
        if user.status != "active":
            raise AuthError("账号已被禁用，请联系管理员")
        return user

    @staticmethod
    def issue_token(user: User) -> str:
        """为用户签发 JWT。"""
        return create_token(user.id)

    @staticmethod
    def create_user(db: Session, data: UserCreate) -> User:
        """创建用户（管理员用）。"""
        exists = db.scalar(select(User).where(User.username == data.username))
        if exists:
            raise ConflictError("该工号/学号已存在")
        user = User(
            username=data.username,
            password_hash=hash_password(data.password),
            name=data.name,
            role=data.role,
            email=data.email,
            phone=data.phone,
            department=data.department,
            position=data.position,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def list_users(db: Session, page: int | None, page_size: int | None,
                   role: str | None = None, keyword: str | None = None) -> dict:
        """分页查询用户，支持按角色 / 关键字过滤。"""
        page, page_size = normalize_page(page, page_size)
        stmt = select(User)
        if role:
            stmt = stmt.where(User.role == role)
        if keyword:
            like = f"%{keyword}%"
            stmt = stmt.where(
                (User.name.like(like)) | (User.username.like(like))
            )
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
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def set_avatar(db: Session, user: User, avatar_url: str) -> User:
        """更新当前用户头像路径。"""
        user.avatar = avatar_url
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def change_password(db: Session, user: User, old_password: str, new_password: str) -> None:
        """修改密码：需校验旧密码。"""
        if not verify_password(old_password, user.password_hash):
            raise ValidateError("旧密码不正确")
        user.password_hash = hash_password(new_password)
        db.commit()

    @staticmethod
    def get_or_raise(db: Session, user_id: int) -> User:
        user = db.get(User, user_id)
        if not user:
            raise NotFoundError("用户不存在")
        return user
