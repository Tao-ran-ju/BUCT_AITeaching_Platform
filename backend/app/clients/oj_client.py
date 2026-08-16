"""OJ 系统客户端：对接学校 BUCTOJ（HUSTOJ 架构）。

已实证的接口（2026-08-15 对 https://buctcoder.com 实测）：
    - 登录：GET /loginpage.php 取会话 -> MD5(明文密码) -> POST /login.php
      （表单字段 user_id / password；密码为客户端 hex_md5，无盐）
    - 提交：POST /submit.php（字段 id / problem_id / language / source）
      成功后 302 跳转 status.php，新提交的 solution_id 出现在状态页首行
    - 结果：GET /status.php，解析行内 <span result=N> 取 HUSTOJ 结果码
      （0=Pending 2=Compiling 3=Running 4=Accepted 6=WA 7=TLE 10=RE 11=CE ...）
    - 查重：HUSTOJ 的 sim 表记录每题相似度；走 OJ 库只读（需配置 OJ_DB_*），
      未配置或读取失败时降级返回不可用，不阻塞主流程。

所有网络异常统一降级，不阻塞作业提交主流程。
"""
import hashlib
import logging
import re
import time
from urllib.parse import urljoin

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# HUSTOJ 标准结果码 -> 中文语义
HUSTOJ_RESULT = {
    0: "等待评测",
    1: "等待重判",
    2: "编译中",
    3: "运行并评判",
    4: "正确",
    5: "格式错误",
    6: "答案错误",
    7: "超出时间限制",
    8: "超出内存限制",
    9: "超出输出限制",
    10: "运行时错误",
    11: "编译错误",
    12: "编译通过",
    13: "测试运行完成",
    14: "系统错误",
}

# 评测中的中间状态（需继续轮询）
PENDING_CODES = {0, 1, 2, 3, 13}

# 语言别名 -> HUSTOJ language id
LANGUAGE_IDS = {
    "c": 0, "gcc": 0,
    "cpp": 1, "c++": 1, "cc": 1, "g++": 1,
    "java": 3,
    "python": 6, "python3": 6, "py": 6,
    "php": 7,
    "csharp": 9, "c#": 9, "cs": 9,
    "javascript": 16, "js": 16, "node": 16,
    "go": 17, "golang": 17,
    "sql": 18,
}


class OJClient:
    """学校 OJ 系统封装（BUCTOJ / HUSTOJ）。"""

    def __init__(self) -> None:
        self.base = (settings.OJ_API_BASE or "").rstrip("/")
        self.username = settings.OJ_USERNAME
        self.password = settings.OJ_PASSWORD
        self.timeout = 30.0
        self._logged_in = False
        self._client = httpx.Client(
            timeout=self.timeout,
            follow_redirects=False,
            headers={"User-Agent": "BUCT-AI-Teaching-Platform/0.1"},
        )

    def __enter__(self) -> "OJClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        self._client.close()

    @property
    def enabled(self) -> bool:
        """配置了 OJ 地址 + 登录凭据才视为启用。"""
        return bool(self.base and self.username and self.password)

    # ---------- 内部工具 ----------
    def _url(self, path: str) -> str:
        return urljoin(self.base + "/", path.lstrip("/"))

    def _get(self, path: str) -> httpx.Response:
        resp = self._client.get(self._url(path))
        resp.raise_for_status()
        return resp

    @staticmethod
    def _md5(text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    # ---------- 登录 ----------
    def login(self) -> bool:
        """登录 OJ，成功后会话 cookie 保存在 self._client。"""
        if not self.enabled:
            return False
        try:
            self._get("loginpage.php")  # 建立会话（Set-Cookie: PHPSESSID）
            resp = self._client.post(
                self._url("login.php"),
                data={
                    "user_id": self.username,
                    "password": self._md5(self.password),
                },
            )
            ok = "UserName or Password Wrong" not in resp.text
            self._logged_in = ok
            if ok:
                logger.info("OJ 登录成功（%s）", self.username)
            else:
                logger.warning("OJ 登录失败：用户名或密码错误")
            return ok
        except httpx.HTTPError as exc:
            logger.warning("OJ 登录异常: %s", exc)
            self._logged_in = False
            return False

    def _ensure_login(self) -> bool:
        return self._logged_in or self.login()

    # ---------- 提交 ----------
    def submit_code(self, code: str, language: str = "python",
                    problem_id: int | None = None) -> dict:
        """提交代码到 OJ。返回 {solution_id, accepted(占位), message}。

        成功时返回 solution_id，由调用方轮询 get_result 获取最终结果；
        失败时降级返回 accepted=False，不阻塞主流程。
        """
        if not self.enabled:
            return {"accepted": False, "score": 0.0, "message": "OJ 未配置"}
        if not problem_id:
            return {"accepted": False, "score": 0.0, "message": "缺少 OJ 题目 ID"}

        lang_id = LANGUAGE_IDS.get(str(language).lower(), 6)
        try:
            if not self._ensure_login():
                return {"accepted": False, "score": 0.0, "message": "OJ 登录失败"}

            resp = self._client.post(
                self._url("submit.php"),
                data={
                    "id": str(problem_id),
                    "problem_id": str(problem_id),
                    "language": str(lang_id),
                    "source": code,
                },
                headers={"Referer": self._url(f"submitpage.php?id={problem_id}")},
            )
            # 成功会 302 -> status.php?user_id=xxx
            if resp.status_code in (301, 302, 303, 307, 308):
                solution_id = self._latest_solution_id()
                if solution_id:
                    return {
                        "accepted": None,
                        "score": None,
                        "solution_id": solution_id,
                        "message": "已提交，等待判题",
                    }
            return {
                "accepted": False,
                "score": 0.0,
                "message": "OJ 提交失败（未返回跳转，可能处于考试模式或题目不可提交）",
            }
        except httpx.HTTPError as exc:
            logger.warning("OJ 提交失败: %s", exc)
            return {"accepted": False, "score": 0.0, "message": str(exc)}

    def _latest_solution_id(self) -> int | None:
        """从 status.php 首行取本人最新提交的 solution_id。"""
        html = self._get(f"status.php?user_id={self.username}").text
        m = re.search(r"<tr>\s*<td>\s*<b>(\d+)</b>", html)
        return int(m.group(1)) if m else None

    # ---------- 结果查询 ----------
    def get_result(self, solution_id: int) -> dict:
        """按 solution_id 查询判题结果。

        返回 {result_code, label, pass_rate, accepted}；查不到时各字段为 None。
        """
        try:
            html = self._get(f"status.php?user_id={self.username}").text
            pattern = (
                r"<tr><td><b>%d</b>.*?result=(\d+)></span>"
                r"<a[^>]*>([^<]*)</a>" % solution_id
            )
            m = re.search(pattern, html, re.S)
            if not m:
                return {"result_code": None, "label": None,
                        "pass_rate": None, "accepted": None}
            code = int(m.group(1))
            text = m.group(2).strip()
            label = HUSTOJ_RESULT.get(code, text or f"code={code}")
            pass_rate = None
            pm = re.search(r"(\d+(?:\.\d+)?)%", text)
            if pm:
                pass_rate = float(pm.group(1)) / 100.0
            return {
                "result_code": code,
                "label": label,
                "pass_rate": pass_rate,
                "accepted": code == 4,
            }
        except httpx.HTTPError as exc:
            logger.warning("查询 OJ 结果失败: %s", exc)
            return {"result_code": None, "label": None,
                    "pass_rate": None, "accepted": None}

    def judge(self, code: str, language: str = "python",
              problem_id: int | None = None, poll_times: int = 12,
              poll_interval: float = 1.5) -> dict:
        """提交并轮询到最终结果（编排入口）。

        返回 dict：{solution_id, accepted, result_code, label, pass_rate}。
        """
        sub = self.submit_code(code, language, problem_id)
        solution_id = sub.get("solution_id")
        if not solution_id:
            return sub

        for _ in range(poll_times):
            time.sleep(poll_interval)
            r = self.get_result(solution_id)
            if r.get("result_code") not in PENDING_CODES and r.get("result_code") is not None:
                r["solution_id"] = solution_id
                return r
        r = self.get_result(solution_id)
        r["solution_id"] = solution_id
        return r

    # ---------- 查重 ----------
    def get_similarity(self, solution_id: int) -> dict:
        """读取某提交在 OJ 上的查重记录。

        HUSTOJ 将相似度存于 sim 表（s_id / sim_s_id / sim）。优先走 OJ 库
        只读（settings.oj_sqlalchemy_url，需配置 OJ_DB_*）；未配置或失败
        时降级返回 similarity=None，不阻塞主流程。
        """
        url = settings.oj_sqlalchemy_url
        if not url:
            return {"solution_id": solution_id, "similarity": None,
                    "similar_solution_id": None}
        try:
            from sqlalchemy import create_engine, text

            engine = create_engine(url, pool_pre_ping=True)
            with engine.connect() as conn:
                rows = conn.execute(
                    text("SELECT sim, sim_s_id FROM sim WHERE s_id = :sid "
                         "ORDER BY sim DESC LIMIT 1"),
                    {"sid": solution_id},
                ).fetchall()
            engine.dispose()
            if rows:
                return {
                    "solution_id": solution_id,
                    "similarity": round(float(rows[0][0]) / 100.0, 3),
                    "similar_solution_id": rows[0][1],
                }
        except Exception as exc:  # 数据库不可达 / 表不存在等
            logger.warning("读取 OJ 查重记录失败: %s", exc)
        return {"solution_id": solution_id, "similarity": None,
                "similar_solution_id": None}

    # ---------- 题目 ----------
    def fetch_problem(self, problem_id: int) -> dict:
        """按 ID 拉取题目标题（骨架）。"""
        try:
            resp = self._get(f"problem.php?id={problem_id}")
            m = re.search(r"<title>([^<]*)</title>", resp.text)
            return {
                "problem_id": problem_id,
                "title": m.group(1).strip() if m else "",
            }
        except httpx.HTTPError as exc:
            logger.warning("拉取 OJ 题目失败: %s", exc)
            return {}
