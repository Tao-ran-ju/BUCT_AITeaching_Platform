"""全局配置：从 .env 读取环境变量，集中管理所有可配置项。"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用全局配置。

    所有环境变量都从这里读取，业务代码禁止硬编码任何敏感信息。
    """

    # ---------- 应用 ----------
    APP_NAME: str = "BUCT AI 教学平台"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = True
    API_PREFIX: str = "/api/v1"

    # ---------- 数据库 ----------
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "buct_ai_teaching"
    DATABASE_URL: str = ""  # 若显式配置则优先使用（支持远程 MySQL）

    # ---------- JWT ----------
    SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # ---------- 学校 OJ 系统 ----------
    OJ_API_BASE: str = "https://buctcoder.com"
    OJ_USERNAME: str = ""
    OJ_PASSWORD: str = ""
    OJ_DB_HOST: str = ""
    OJ_DB_PORT: int = 3306
    OJ_DB_USER: str = ""
    OJ_DB_PASSWORD: str = ""
    OJ_DB_NAME: str = "jol"

    # ---------- 大模型 API ----------
    LLM_API_KEY: str = ""
    LLM_API_BASE: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    LLM_MODEL: str = "qwen-plus"

    # ---------- 文件存储 ----------
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 100

    # ---------- 视频处理（ffmpeg / ffprobe） ----------
    FFMPEG_PATH: str = "ffmpeg"
    FFPROBE_PATH: str = "ffprobe"
    MAX_VIDEO_TRANSCODE_MB: int = 500

    # ---------- 阿里云 OSS（对象存储 + 文档预览，可选） ----------
    OSS_ENABLED: bool = False
    OSS_ACCESS_KEY_ID: str = ""
    OSS_ACCESS_KEY_SECRET: str = ""
    OSS_BUCKET: str = ""
    OSS_ENDPOINT: str = ""
    OSS_REGION: str = ""
    OSS_URL_EXPIRES: int = 3600

    # ---------- 学情预警阈值 ----------
    WARNING_SUBMIT_DELAY_DAYS: int = 3
    WARNING_ABSENT_DAYS: int = 3
    WARNING_LOW_SCORE: float = 0.3
    WARNING_LOW_LOGIN_SECONDS: int = 600
    WARNING_LOW_RESOURCE_VISITS: int = 2

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    @property
    def sqlalchemy_url(self) -> str:
        """拼接 SQLAlchemy 连接串；配置了 DATABASE_URL 时优先使用。"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )

    @property
    def oj_sqlalchemy_url(self) -> str:
        """学校 OJ 库只读连接串（用于拉取题目 / 评测结果）。"""
        if not self.OJ_DB_USER:
            return ""
        return (
            f"mysql+pymysql://{self.OJ_DB_USER}:{self.OJ_DB_PASSWORD}"
            f"@{self.OJ_DB_HOST}:{self.OJ_DB_PORT}/{self.OJ_DB_NAME}?charset=utf8mb4"
        )


@lru_cache
def get_settings() -> Settings:
    """缓存全局配置实例，避免重复解析 .env。"""
    return Settings()


settings = get_settings()
