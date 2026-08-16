"""评测服务：对接学校 OJ 判题（BUCTOJ/HUSTOJ）+ 大模型评语。

编排流程：
    1. 提交代码到 OJ（若作业配置了 oj_problem_id），轮询拿到判题结果
    2. 回写 judge_status / score / oj_solution_id
    3. 读取 OJ 查重记录（sim 表）写入 plagiarism_rate（未配置 OJ 库则跳过）
    4. 调用大模型生成个性化评语（失败不阻塞）

未配置 OJ 时降级为占位结果，保证本地联调可跑通。
"""
import logging

from sqlalchemy.orm import Session

from app.clients.llm_client import llm_client
from app.clients.oj_client import OJClient
from app.models.assignment import Assignment, AssignmentSubmission

logger = logging.getLogger(__name__)


class JudgeService:
    """作业 / 代码评测编排。"""

    def __init__(self, oj: OJClient | None = None):
        self.oj = oj or OJClient()

    def judge(self, db: Session, submission: AssignmentSubmission) -> AssignmentSubmission:
        """对单个提交进行评测，返回回写后的提交。"""
        assignment = db.get(Assignment, submission.assignment_id)
        problem_id = assignment.oj_problem_id if assignment else None
        language = (assignment.oj_language if assignment else None) or "python"

        submission.judge_status = "judging"
        db.commit()

        # 第一阶段：OJ 判题
        if self.oj.enabled and problem_id:
            self._judge_via_oj(db, submission, problem_id, language)
        else:
            # 未配置 OJ 或未关联题目，给出占位结果（便于本地联调）
            submission.judge_status = "accepted"
            submission.score = 100.0

        # 第二阶段：大模型个性化评语（失败不阻塞）
        try:
            submission.ai_comment = llm_client.code_review(submission.content, language=language)
        except Exception as exc:
            logger.warning("AI 评语生成失败: %s", exc)

        db.commit()
        db.refresh(submission)
        return submission

    def _judge_via_oj(self, db: Session, submission: AssignmentSubmission,
                      problem_id: int, language: str) -> None:
        """提交到 OJ 并轮询结果，回写判题与查重。"""
        try:
            result = self.oj.judge(submission.content or "", language=language,
                                   problem_id=problem_id)
            solution_id = result.get("solution_id")
            accepted = result.get("accepted")

            if solution_id:
                submission.oj_solution_id = solution_id

            if accepted is True:
                submission.judge_status = "accepted"
                submission.score = 100.0
            elif accepted is False or (accepted is None and result.get("result_code")):
                # 已出最终结果但未通过，按通过率给分
                submission.judge_status = "failed"
                pass_rate = result.get("pass_rate")
                submission.score = round((pass_rate or 0.0) * 100, 1)
            else:
                # 未能拿到确定结果（提交失败 / 轮询超时）
                submission.judge_status = "failed"
                submission.score = 0.0

            # 读取 OJ 查重记录（sim 表），失败不阻塞
            if solution_id:
                sim = self.oj.get_similarity(solution_id)
                if sim.get("similarity") is not None:
                    submission.plagiarism_rate = sim["similarity"]
        except Exception as exc:
            logger.warning("OJ 判题异常，降级为未通过: %s", exc)
            submission.judge_status = "failed"
            submission.score = 0.0

    def close(self) -> None:
        self.oj.close()
