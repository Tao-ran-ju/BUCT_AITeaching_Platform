"""纯文本提取工具：从上传的教学资源文件中抽取正文文本。

仅依赖标准库，避免引入重型文档解析依赖：
- 纯文本类（.txt/.md/.py/.c/.cpp/.java/.json/.csv 等）直接按编码读取；
- .docx（OOXML，本质是 zip）解包 word/document.xml 后剥离标签取正文；
- .docx（OOXML，本质是 zip）解包 word/document.xml 后剥离标签取正文；
- 音视频（.mp4/.mkv/.mp3 等）借助 ffmpeg 抽取内嵌字幕作为正文（无字幕则返回 None）；
- 其余二进制格式（.pdf/.doc/.ppt/图片）暂无法用标准库可靠提取，返回 None。

返回 None 表示无法提取，调用方据此跳过自动摘要 / 关键词生成。
"""
import re
import zipfile
from pathlib import Path

# 可直接按文本读取的扩展名
PLAIN_TEXT_EXT = {
    ".txt", ".md", ".markdown", ".py", ".c", ".cpp", ".cc", ".h", ".java",
    ".js", ".ts", ".json", ".xml", ".yaml", ".yml", ".csv", ".html", ".css",
    ".sql", ".sh",
}

# 用 OOXML 解包方式提取的扩展名
DOCX_EXT = {".docx"}

# 借助 ffmpeg 抽取内嵌字幕的媒体扩展名（与 video_processor 保持一致）
MEDIA_EXT = {
    ".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".webm",
    ".m4v", ".ts", ".mpeg", ".mpg",
    ".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".wma",
}


def _decode(data: bytes) -> str:
    """依次尝试常见编码，避免中文乱码。"""
    for enc in ("utf-8", "gb18030", "gbk", "utf-16"):
        try:
            return data.decode(enc)
        except (UnicodeDecodeError, ValueError):
            continue
    return data.decode("utf-8", errors="ignore")


def _strip_tags(xml: str) -> str:
    """剥离 XML 标签，压缩空白，返回可读正文。"""
    text = re.sub(r"<w:p[ >]", "\n", xml)          # 段落换行
    text = re.sub(r"<[^>]+>", "", text)            # 去掉其余标签
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = re.sub(r"\n{2,}", "\n", text)
    return re.sub(r"[ \t]+", " ", text).strip()


def _extract_docx(path: Path) -> str | None:
    try:
        with zipfile.ZipFile(path) as z:
            xml = z.read("word/document.xml")
    except (zipfile.BadZipFile, KeyError, OSError):
        return None
    return _strip_tags(_decode(xml))


def _extract_media_subtitle(path: Path) -> str | None:
    """音视频：抽取内嵌字幕作为正文文本（懒加载 video_processor，避免重依赖）。"""
    try:
        from app.utils.video_processor import extract_subtitle_text
    except Exception:
        return None
    try:
        return extract_subtitle_text(str(path))
    except Exception:
        return None


def extract_text(path: str) -> str | None:
    """从资源文件路径提取正文文本；无法提取时返回 None。"""
    file = Path(path)
    if not file.exists():
        return None
    ext = file.suffix.lower()

    if ext in PLAIN_TEXT_EXT:
        try:
            return _decode(file.read_bytes()).strip()
        except OSError:
            return None
    if ext in DOCX_EXT:
        return _extract_docx(file)
    if ext in MEDIA_EXT:
        return _extract_media_subtitle(file)
    return None
