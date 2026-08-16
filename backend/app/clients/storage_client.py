"""存储客户端：文件存储抽象。

初期使用本地磁盘，后续可无缝切换为 OSS / COS 等对象存储，
只需替换本类内部实现，业务层调用不变。
"""
import logging
import shutil
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)


class StorageClient:
    """统一文件存储接口。"""

    def __init__(self) -> None:
        self.base_dir = Path(settings.UPLOAD_DIR)

    def save_bytes(self, rel_path: str, data: bytes) -> str:
        """写入字节数据，返回相对路径。"""
        dest = self.base_dir / rel_path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return rel_path.replace("\\", "/")

    def delete(self, rel_path: str) -> None:
        """删除文件（不存在时静默）。"""
        target = self.base_dir / rel_path
        try:
            if target.is_file():
                target.unlink()
            elif target.is_dir():
                shutil.rmtree(target)
        except OSError as exc:
            logger.warning("删除存储文件失败 %s: %s", rel_path, exc)

    def absolute_path(self, rel_path: str) -> Path:
        """相对路径转本地绝对路径（用于 StaticFiles 或下载响应）。"""
        return (self.base_dir / rel_path).resolve()


# 全局单例
storage_client = StorageClient()
