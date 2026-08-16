"""大模型客户端：统一封装 OpenAI 兼容接口（通义千问 / DeepSeek 等）。

对外暴露三个业务方法：
- text_generate：通用文本生成（教案、题库、摘要）
- code_review：代码质量分析，生成个性化评语
- intervention_suggestion：学情干预建议

内置：超时、重试、错误降级、简单 token 估算。
业务代码只需调用本类，不直接依赖任何具体厂商。
"""
import logging
import time

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """大模型统一客户端。"""

    def __init__(self) -> None:
        self.api_key = settings.LLM_API_KEY
        self.base_url = settings.LLM_API_BASE
        self.model = settings.LLM_MODEL
        self.timeout = 60.0
        self.max_retries = 2

    @property
    def available(self) -> bool:
        """未配置 API Key 时视为不可用，业务层据此降级。"""
        return bool(self.api_key)

    # ---------- 底层调用 ----------
    def _chat(self, messages: list[dict], temperature: float = 0.7) -> str:
        """调用 chat/completions 接口，带超时与重试。"""
        if not self.available:
            raise RuntimeError("LLM_API_KEY 未配置，无法调用大模型")
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
        }
        last_exc: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    resp = client.post(url, json=payload, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()
                return data["choices"][0]["message"]["content"]
            except (httpx.HTTPError, KeyError, IndexError) as exc:
                last_exc = exc
                logger.warning("大模型调用失败(第 %d 次): %s", attempt + 1, exc)
                if attempt < self.max_retries:
                    time.sleep(1 * (attempt + 1))  # 指数退避简化
        raise RuntimeError(f"大模型调用失败: {last_exc}")

    # ---------- 业务方法 ----------
    def text_generate(self, prompt: str) -> str:
        """通用文本生成。"""
        return self._chat(
            [{"role": "system", "content": "你是高校程序设计课程的资深 AI 教研助手。"},
             {"role": "user", "content": prompt}]
        )

    def code_review(self, code: str, language: str = "python") -> str:
        """代码质量分析，生成个性化评语。"""
        prompt = (
            f"请分析以下 {language} 代码的正确性、可读性与优化空间，"
            f"并给出 150 字以内的个性化评语（面向大学生）：\n```{language}\n{code[:3000]}\n```"
        )
        return self._chat(
            [{"role": "system", "content": "你是算法竞赛课程助教，擅长代码评审。"},
             {"role": "user", "content": prompt}]
        )

    def intervention_suggestion(self, reason: str) -> str:
        """根据预警原因生成个性化干预建议。"""
        prompt = (
            f"学生出现以下学情风险：{reason}。"
            f"请给出 3 条具体、可操作的干预建议（含与教师、助教、同伴互动的措施）。"
        )
        return self._chat(
            [{"role": "system", "content": "你是高校学业预警与学习支持专家。"},
             {"role": "user", "content": prompt}]
        )

    def count_tokens(self, text: str) -> int:
        """粗略估算 token 数（中文 1 字约 1 token，英文约 4 字符 1 token）。"""
        if not text:
            return 0
        return len(text) // 1 if any("\u4e00" <= ch <= "\u9fff" for ch in text) else len(text) // 4


# 全局单例，业务层直接 import 使用
llm_client = LLMClient()
