"""安全工具：密码哈希（bcrypt，兼容旧 PBKDF2）、JWT 签发与校验。"""
import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import bcrypt
import jwt

from app.config import settings


def hash_password(password: str) -> str:
    """使用 bcrypt 生成密码哈希（与学校 buct_cip 库 user_rft 的 $2b$ 格式一致）。"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """校验明文密码与哈希是否匹配。

    兼容两种格式：
    - bcrypt：`$2b$10$...`（学校 user_rft 表使用，$2a/$2b/$2y 均支持）
    - PBKDF2：`pbkdf2$iterations$salt_hex$hash_hex`（旧版自建用户）
    """
    if not hashed:
        return False
    if hashed.startswith(("$2a$", "$2b$", "$2y$")):
        try:
            return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
        except (ValueError, TypeError):
            return False
    if hashed.startswith("pbkdf2$"):
        return _verify_pbkdf2(password, hashed)
    return False


def _verify_pbkdf2(password: str, hashed: str) -> bool:
    """校验旧版 PBKDF2 哈希（hmac.compare_digest 防时序攻击）。"""
    try:
        scheme, iterations, salt_hex, hash_hex = hashed.split("$")
        if scheme != "pbkdf2":
            return False
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, int(iterations)
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def create_token(user_id: int, expires_minutes: Optional[int] = None) -> str:
    """签发 JWT，payload 携带用户主键 uid。"""
    minutes = expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    now = datetime.now(timezone.utc)
    payload = {
        "uid": user_id,
        "iat": now,
        "exp": now + timedelta(minutes=minutes),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict[str, Any]]:
    """校验并解码 JWT；失败返回 None。"""
    try:
        return jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except jwt.PyJWTError:
        return None
