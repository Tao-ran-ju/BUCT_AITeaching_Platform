"""安全工具：密码哈希（标准库 PBKDF2）、JWT 签发与校验。

选择标准库 hashlib + PyJWT 实现，避免 bcrypt 等需要编译的
依赖在 Windows / Python 3.13 环境下的安装问题。
"""
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import jwt

from app.config import settings

_PBKDF2_ITERATIONS = 100_000


def hash_password(password: str) -> str:
    """使用 PBKDF2-HMAC-SHA256 生成带随机盐的密码哈希。

    返回格式: pbkdf2$iterations$salt_hex$hash_hex
    """
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS
    )
    return (
        f"pbkdf2${_PBKDF2_ITERATIONS}$"
        f"{salt.hex()}${digest.hex()}"
    )


def verify_password(password: str, hashed: str) -> bool:
    """校验明文密码与哈希是否匹配（使用 hmac.compare_digest 防时序攻击）。"""
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
