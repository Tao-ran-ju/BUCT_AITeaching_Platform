"""视频/音频处理工具：基于 ffmpeg / ffprobe 完成转码、关键帧抽取、字幕抽取与时长探测。

设计约定：
- 所有函数在 ffmpeg / ffprobe 未安装或处理失败时返回 None（优雅降级），
  不抛异常，保证上传主流程不受影响；
- 入参 path 采用与 Resource.file_path 一致的「相对路径」（相对 backend/ 工作目录），
  输出同样返回 posix 风格相对路径，可直接入库并通过 /uploads 静态目录访问。
"""
import logging
import re
import shutil
import subprocess
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

VIDEO_EXT = {
    ".mp4", ".mov", ".avi", ".mkv", ".flv", ".wmv", ".webm",
    ".m4v", ".ts", ".mpeg", ".mpg",
}
AUDIO_EXT = {".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg", ".wma"}


def _which(binary: str) -> str | None:
    """定位可执行文件；binary 可能已是绝对路径。"""
    if not binary:
        return None
    return shutil.which(binary) if not Path(binary).is_absolute() else (
        binary if Path(binary).exists() else None
    )


def _run(args: list[str], timeout: int = 120) -> subprocess.CompletedProcess | None:
    """执行外部命令，统一捕获异常；失败返回 None。"""
    try:
        return subprocess.run(args, capture_output=True, timeout=timeout, check=False)
    except (OSError, subprocess.SubprocessError) as exc:
        logger.warning("ffmpeg 调用失败: %s", exc)
        return None


def ffmpeg_available() -> bool:
    return _which(settings.FFMPEG_PATH) is not None


def ffprobe_available() -> bool:
    return _which(settings.FFPROBE_PATH) is not None


def probe_duration(path: str) -> float | None:
    """探测音视频时长（秒）；失败返回 None。"""
    src = Path(path)
    if not src.exists() or not ffprobe_available():
        return None
    proc = _run([
        settings.FFPROBE_PATH, "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(src),
    ])
    if not proc or proc.returncode != 0:
        return None
    raw = proc.stdout.decode("utf-8", errors="ignore").strip()
    try:
        return round(float(raw), 2)
    except ValueError:
        return None


def extract_keyframes(path: str, out_dir: str, count: int = 1) -> list[str]:
    """从视频中抽取关键帧（缩略图），返回相对路径列表；失败返回空列表。

    采用「等间隔采样」方式：在 [10% 时长, 90% 时长] 区间内均匀取 count 帧，
    保证抽取到的是内容画面而非片头黑帧。单帧时落在 10% 时长处。
    """
    src = Path(path)
    if not src.exists() or not ffmpeg_available():
        return []
    duration = probe_duration(path)
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    if not duration or duration <= 0:
        # 无法探测时长时退化为抽取第 1 秒
        points = [1.0]
    else:
        start, end = duration * 0.1, duration * 0.9
        if count <= 1:
            points = [max(1.0, start)]
        else:
            step = (end - start) / max(count - 1, 1)
            points = [round(start + step * i, 2) for i in range(count)]

    results: list[str] = []
    for idx, t in enumerate(points):
        out_path = out / f"{src.stem}_frame{idx + 1}.jpg"
        proc = _run([
            settings.FFMPEG_PATH, "-y", "-ss", f"{t:.2f}",
            "-i", str(src), "-frames:v", "1", "-q:v", "2", str(out_path),
        ])
        if proc and proc.returncode == 0 and out_path.exists():
            results.append(out_path.as_posix())
    return results


def extract_subtitle_text(path: str) -> str | None:
    """抽取内嵌字幕流（.srt/.ass/.vtt 等）并转为纯文本；无字幕时返回 None。"""
    src = Path(path)
    if not src.exists() or not ffmpeg_available():
        return None
    tmp = src.with_name(f"{src.stem}.srt")
    proc = _run([
        settings.FFMPEG_PATH, "-y", "-i", str(src),
        "-map", "0:s:0", "-c:s", "srt", str(tmp),
    ])
    if not proc or proc.returncode != 0 or not tmp.exists() or tmp.stat().st_size == 0:
        return None
    return _srt_to_text(tmp)


def _srt_to_text(path: Path) -> str | None:
    """将 .srt 字幕文件转成连续纯文本（去掉序号、时间轴与内联标签）。"""
    try:
        data = path.read_bytes()
    except OSError:
        return None
    text = None
    for enc in ("utf-8-sig", "utf-8", "gb18030", "gbk"):
        try:
            text = data.decode(enc)
            break
        except (UnicodeDecodeError, ValueError):
            continue
    if text is None:
        text = data.decode("utf-8", errors="ignore")

    parts: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.upper().startswith("WEBVTT") or line.upper().startswith("NOTE"):
            continue
        if re.fullmatch(r"\d+", line):
            continue
        if "-->" in line:
            continue
        line = re.sub(r"<[^>]+>", "", line)
        line = line.replace("\\N", " ").replace("\\n", " ").strip()
        if line:
            parts.append(line)
    return " ".join(parts) or None


def transcode_mp4(path: str, out_dir: str) -> str | None:
    """转码为 Web 友好 MP4（H.264 + AAC + faststart），返回相对路径；失败返回 None。

    超过 MAX_VIDEO_TRANSCODE_MB 的大文件跳过转码，避免同步上传请求阻塞过久。
    """
    src = Path(path)
    if not src.exists() or not ffmpeg_available():
        return None
    size_mb = src.stat().st_size / (1024 * 1024)
    if size_mb > settings.MAX_VIDEO_TRANSCODE_MB:
        logger.info("视频 %.1fMB 超过转码阈值 %dMB，跳过转码", size_mb, settings.MAX_VIDEO_TRANSCODE_MB)
        return None
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    out_path = out / f"{src.stem}_web.mp4"
    proc = _run([
        settings.FFMPEG_PATH, "-y", "-i", str(src),
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart",
        str(out_path),
    ], timeout=600)
    if not proc or proc.returncode != 0 or not out_path.exists():
        return None
    return out_path.as_posix()
