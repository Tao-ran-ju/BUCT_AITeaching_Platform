"""文件处理工具：安全保存上传文件、路径校验。"""
import os
import uuid
from pathlib import Path

from app.config import settings
from app.exceptions import ValidateError

# 允许的常见教学资源类型
ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx",
    ".txt", ".md", ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ".mp4", ".mp3", ".zip", ".py", ".c", ".cpp", ".java",
}


def ensure_upload_dir(sub_dir: str = "") -> Path:
    """确保上传目录存在，返回目标目录 Path。"""
    base = Path(settings.UPLOAD_DIR)
    target = base / sub_dir if sub_dir else base
    target.mkdir(parents=True, exist_ok=True)
    return target


def save_upload_file(file, sub_dir: str = "") -> str:
    """保存上传文件，返回相对存储路径（入库字段）。

    Args:
        file: FastAPI UploadFile
        sub_dir: 子目录，例如 course/1、resource/2

    Returns:
        相对路径，例如 uploads/course/1/<uuid>.pdf
    """
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidateError(f"不支持的文件类型: {ext or '(无扩展名)'}")

    target_dir = ensure_upload_dir(sub_dir)
    filename = f"{uuid.uuid4().hex}{ext}"
    dest = target_dir / filename

    with dest.open("wb") as f:
        while chunk := file.file.read(1024 * 1024):
            f.write(chunk)

    return str(Path(settings.UPLOAD_DIR) / sub_dir / filename).replace("\\", "/")
