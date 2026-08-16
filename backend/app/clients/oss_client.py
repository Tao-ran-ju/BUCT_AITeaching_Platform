"""阿里云 OSS 客户端：文件镜像、签名 URL、Office 文档转 PDF 预览。

设计约定（与全项目「优雅降级」一致）：
- 未配置 OSS（enabled=False）或任一操作失败时返回 None / False，绝不抛异常打断主流程；
- object key 直接复用本地相对路径（如 uploads/course/1/<uuid>.mp4），
  使 Resource.file_path 同时充当 OSS key，缩略图/转码产物同理。
"""
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# Office 扩展名 -> OSS 文档转换（IMM doc/convert）source 参数
OFFICE_EXT_SOURCE = {
    ".doc": "source_doc", ".docx": "source_docx",
    ".ppt": "source_ppt", ".pptx": "source_pptx",
    ".xls": "source_xls", ".xlsx": "source_xlsx",
}

# 常见扩展名 -> Content-Type（确保 PDF/图片/视频能内联预览而非强制下载）
CONTENT_TYPES = {
    ".pdf": "application/pdf",
    ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
    ".gif": "image/gif", ".webp": "image/webp", ".bmp": "image/bmp",
    ".mp4": "video/mp4", ".m4v": "video/mp4", ".mov": "video/quicktime",
    ".mp3": "audio/mpeg", ".wav": "audio/wav", ".m4a": "audio/mp4",
}


def _guess_content_type(key: str) -> str | None:
    ext = "." + key.rsplit(".", 1)[-1].lower() if "." in key else ""
    return CONTENT_TYPES.get(ext)


class OSSClient:
    """OSS 操作封装，所有方法对「未启用」场景安全无副作用。"""

    def __init__(self) -> None:
        self._bucket = None

    @property
    def enabled(self) -> bool:
        return bool(
            settings.OSS_ENABLED
            and settings.OSS_ACCESS_KEY_ID
            and settings.OSS_ACCESS_KEY_SECRET
            and settings.OSS_BUCKET
            and settings.OSS_ENDPOINT
        )

    def _get_bucket(self):
        """懒加载 oss2.Bucket；未启用 / 未安装 oss2 / 初始化失败均返回 None。"""
        if not self.enabled:
            return None
        if self._bucket is not None:
            return self._bucket
        try:
            import oss2
        except ImportError as exc:
            logger.warning("未安装 oss2，跳过 OSS 操作: %s", exc)
            return None
        try:
            auth = oss2.Auth(settings.OSS_ACCESS_KEY_ID, settings.OSS_ACCESS_KEY_SECRET)
            endpoint = settings.OSS_ENDPOINT
            if not endpoint.startswith(("http://", "https://")):
                endpoint = "https://" + endpoint
            self._bucket = oss2.Bucket(
                auth, endpoint, settings.OSS_BUCKET,
                region=settings.OSS_REGION or None,
            )
        except Exception as exc:
            logger.warning("OSS 初始化失败: %s", exc)
            return None
        return self._bucket

    # ---------- 基础操作 ----------
    def upload_file(self, local_path: str, key: str, content_type: str | None = None) -> bool:
        """上传本地文件到 OSS（key 为本地相对路径）。成功返回 True。"""
        bucket = self._get_bucket()
        if bucket is None:
            return False
        try:
            headers = {"Content-Type": content_type or _guess_content_type(key)} or None
            bucket.put_object_from_file(key, local_path, headers=headers)
            return True
        except Exception as exc:
            logger.warning("OSS 上传失败 %s: %s", key, exc)
            return False

    def delete(self, key: str) -> None:
        """删除对象（不存在或未启用时静默）。"""
        bucket = self._get_bucket()
        if bucket is None or not key:
            return
        try:
            bucket.delete_object(key)
        except Exception as exc:
            logger.warning("OSS 删除失败 %s: %s", key, exc)

    def signed_url(self, key: str, expires: int | None = None) -> str | None:
        """生成 GET 签名 URL（供下载 / 播放 / 缩略图）。失败返回 None。"""
        bucket = self._get_bucket()
        if bucket is None or not key:
            return None
        try:
            return bucket.sign_url("GET", key, expires or settings.OSS_URL_EXPIRES)
        except Exception as exc:
            logger.warning("OSS 签名失败 %s: %s", key, exc)
            return None

    # ---------- 文档预览（IMM doc/convert 异步转 PDF） ----------
    def office_to_pdf(self, key: str) -> str | None:
        """把 Office 对象异步转换为 PDF 并返回其签名 URL；失败返回 None。

        依赖：已开通 IMM 并在 Bucket 绑定同地域 Project，且 oss2 支持异步处理接口。
        任何环节失败（含未开通 IMM）都返回 None，由调用方回退为下载。
        """
        bucket = self._get_bucket()
        if bucket is None or not key:
            return None
        source = OFFICE_EXT_SOURCE.get(
            "." + key.rsplit(".", 1)[-1].lower() if "." in key else ""
        )
        if not source:
            return None
        try:
            import base64
            import time

            target_key = f"{key}.preview.pdf"
            style = f"doc/convert,target_pdf,{source}"
            bucket_enc = base64.urlsafe_b64encode(settings.OSS_BUCKET.encode()).decode().rstrip("=")
            key_enc = base64.urlsafe_b64encode(target_key.encode()).decode().rstrip("=")
            process = f"{style}|sys/saveas,b_{bucket_enc},o_{key_enc}"

            result = bucket.async_process_object(key, process)
            task_id = getattr(result, "task_id", None)
            if not task_id:
                return None

            # 轮询任务状态（有界等待，避免请求挂起）
            deadline = time.time() + 30
            while time.time() < deadline:
                try:
                    info = bucket.get_task(task_id)
                    status = getattr(info, "status", None) or getattr(info, "state", None)
                    if status in ("Success", "Succeed", "Succeeded", "Finished", "Done"):
                        return self.signed_url(target_key)
                    if status in ("Failed", "Fail", "Error"):
                        return None
                except Exception:
                    pass  # 轮询接口差异/网络抖动，继续等待
                time.sleep(2)
            # 超时：转换可能仍在进行，仍返回签名 URL 让前端重试
            return self.signed_url(target_key)
        except Exception as exc:
            logger.warning("OSS 文档转换失败 %s: %s", key, exc)
            return None


# 全局单例
oss_client = OSSClient()
