"""查重服务：基于 simhash 的代码相似度检测（纯标准库，无外部依赖）。

流程：
    1. 归一化文本（小写 + 按标识符/数字切词）
    2. 生成 3-gram shingle
    3. 每个 shingle 计算 64 位指纹，累加得到 simhash
    4. 两两计算海明距离 → 相似度，写入每个提交的 plagiarism_rate
"""
import hashlib
import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.assignment import AssignmentSubmission

_TOKEN_RE = re.compile(r"[a-z_][a-z0-9_]*|\d+")
_SHINGLE_N = 3
_BITS = 64


def _tokenize(text: str) -> list[str]:
    """归一化 + 切词：变量名重命名、大小写、空白差异被部分消除。"""
    return _TOKEN_RE.findall((text or "").lower())


def _shingles(tokens: list[str], n: int = _SHINGLE_N) -> list[tuple]:
    """滑动窗口 n-gram。"""
    if len(tokens) < n:
        return [tuple(tokens)] if tokens else []
    return [tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def _fingerprint(token) -> int:
    """稳定 64 位指纹（md5，跨进程一致，不受 PYTHONHASHSEED 影响）。

    token 既可能是单词（str），也可能是 shingle 元组（tuple），统一字符串化。
    """
    s = token if isinstance(token, str) else "|".join(token)
    return int.from_bytes(hashlib.md5(s.encode("utf-8")).digest()[:8], "little")


def _simhash(tokens: list[str]) -> int:
    """对词集合计算 simhash 指纹。"""
    v = [0] * _BITS
    for t in set(tokens):
        f = _fingerprint(t)
        for i in range(_BITS):
            if (f >> i) & 1:
                v[i] += 1
            else:
                v[i] -= 1
    result = 0
    for i in range(_BITS):
        if v[i] > 0:
            result |= 1 << i
    return result


def _hamming(a: int, b: int) -> int:
    return bin(a ^ b).count("1")


def similarity(a: int, b: int) -> float:
    """simhash 相似度 0-1。"""
    return 1.0 - _hamming(a, b) / _BITS


def fingerprint(text: str) -> int:
    """对外暴露：文本 → simhash 指纹。"""
    return _simhash(_shingles(_tokenize(text)))


class PlagiarismService:
    """作业查重业务逻辑。"""

    @staticmethod
    def check(db: Session, assignment_id: int) -> list[AssignmentSubmission]:
        """对某作业的全部提交两两比对，写入最高相似度，返回提交列表。"""
        submissions = list(
            db.scalars(
                select(AssignmentSubmission)
                .where(AssignmentSubmission.assignment_id == assignment_id)
                .order_by(AssignmentSubmission.id)
            ).all()
        )
        if len(submissions) < 2:
            for s in submissions:
                s.plagiarism_rate = 0.0
            db.commit()
            return submissions

        fps = [fingerprint(s.content or "") for s in submissions]
        for i, s in enumerate(submissions):
            best = 0.0
            for j in range(len(submissions)):
                if i == j:
                    continue
                best = max(best, similarity(fps[i], fps[j]))
            s.plagiarism_rate = round(best, 3)
        db.commit()
        for s in submissions:
            db.refresh(s)
        return submissions
