"""日志配置：控制台输出，生产环境可扩展为文件 / 集中式日志。"""
import logging
import sys


def setup_logging(level: int = logging.INFO) -> None:
    """初始化根日志器，避免重复注册 handler。"""
    root = logging.getLogger()
    if root.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    root.addHandler(handler)
    root.setLevel(level)
