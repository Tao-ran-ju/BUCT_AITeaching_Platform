"""用户相关请求 / 响应模型。"""
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import Timestamp


class LoginRequest(BaseModel):
    """直接账号密码登录（学号/工号 + 密码，验证 user_rft.bcrypt）。"""

    username: str = Field(..., min_length=1, max_length=255, description="学号/工号（uid）")
    password: str = Field(..., min_length=1, max_length=128)


class SsoRequest(BaseModel):
    """统一 SSO：学生端/教师端后端凭共享密钥换取教师端 JWT。"""

    uid: str = Field(..., min_length=1, max_length=255, description="学号/工号")
    name: Optional[str] = Field(None, max_length=255, description="姓名（首次建档时使用）")
    role: int = Field(..., description="0=教师 1=学生")
    secret: str = Field(..., min_length=1, description="两端约定的共享密钥")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class UserCreate(BaseModel):
    """教师手动创建学生账号（学号建档；密码缺省生成随机密码）。"""

    uid: str = Field(..., min_length=1, max_length=255)
    name: str = Field(..., min_length=1, max_length=255)
    role: int = Field(1, description="0=教师 1=学生")
    password: Optional[str] = Field(None, min_length=6, max_length=128)
    gender: int = 0
    college: str = ""
    grade: Optional[str] = None
    class_name: Optional[str] = None
    major: Optional[str] = None


class UserUpdate(BaseModel):
    """更新个人资料（部分字段可选）。"""

    name: Optional[str] = None
    gender: Optional[int] = None
    college: Optional[str] = None
    grade: Optional[str] = None
    class_name: Optional[str] = None
    major: Optional[str] = None


class PasswordChange(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=6, max_length=128)


class UserOut(BaseModel):
    """用户信息出参（不回传密码哈希）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    uid: str
    name: str
    role: int
    gender: int
    college: str
    grade: Optional[str] = None
    class_name: Optional[str] = None
    major: Optional[str] = None
    status: int
    created_at: Timestamp
