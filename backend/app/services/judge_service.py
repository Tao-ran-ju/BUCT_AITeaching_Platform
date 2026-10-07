"""评测服务：对接学校 OJ 判题 + 大模型评语。

结果写入两处：
1. t_submission_judge —— 教师端自有扩展（judge_status / oj_solution_id / score /
   ai_comment / plagiarism_rate），供教师端作业批阅页展示；
2. assignment_submissions —— 镜像 score / feedback / status=1，供学生端读取分数与评语。
"""
import logging
import time

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clients.llm_client import llm_client
from app.clients.oj_client import OJClient
from app.models.assignment import AssignmentOj, AssignmentSubmission, SubmissionJudge

logger = logging.getLogger(__name__)


def get_or_create_judge(db: Session, submission: AssignmentSubmission) -> SubmissionJudge:
    """取该提交的评测扩展记录，不存在则创建。"""
    sj = db.scalar(select(SubmissionJudge).where(SubmissionJudge.submission_id == submission.id))
    if not sj:
        sj = SubmissionJudge(
            submission_id=submission.id,
            assignment_id=submission.assignment_id,
            student_user_id=submission.student_user_id,
            judge_status="pending",
            created_at=int(time.time()),
            edited_at=int(time.time()),
        )
        db.add(sj)
        db.flush()
    return sj


class JudgeService:
    """作业 / 代码评测编排。"""

    def __init__(self, oj: OJClient | None = None):
        self.oj = oj or OJClient()

    def judge(self, db: Session, submission: AssignmentSubmission) -> AssignmentSubmission:
        """对单个提交进行评测，返回回写后的提交。"""
        oj = db.scalar(
            select(AssignmentOj).where(AssignmentOj.assignment_id == submission.assignment_id)
        )
        problem_id = oj.oj_problem_id if oj else None
        language = (oj.oj_language if oj else None) or "python"

        sj = get_or_create_judge(db, submission)
        sj.judge_status = "judging"
        db.commit()

        # 第一阶段：OJ 判题
        if self.oj.enabled and problem_id:
            self._judge_via_oj(db, sj, submission, problem_id, language)
        else:
            # 未配置 OJ 或未关联题目，给出占位结果（便于本地联调）
            sj.judge_status = "accepted"
            sj.score = 100.0

        # 第二阶段：大模型个性化评语（失败不阻塞）
        try:
            sj.ai_comment = llm_client.code_review(submission.content or "", language=language)
        except Exception as exc:
            logger.warning("AI 评语生成失败: %s", exc)

        # 镜像回学校提交表，供学生端读取
        submission.status = 1
        submission.score = sj.score
        submission.feedback = sj.ai_comment or (
            f"已评测，得分 {sj.score if sj.score is not None else 0}"
        )
        submission.edited_at = int(time.time())
        sj.edited_at = int(time.time())
        db.commit()
        db.refresh(submission)
        return submission

    def _judge_via_oj(self, db: Session, sj: SubmissionJudge, submission: AssignmentSubmission,
                      problem_id: int, language: str) -> None:
        """提交到 OJ 并轮询结果，回写判题与查重。"""
        try:
            result = self.oj.judge(submission.content or "", language=language,
                                   problem_id=problem_id)
            solution_id = result.get("solution_id")
            accepted = result.get("accepted")

            if solution_id:
                sj.oj_solution_id = solution_id
                sj.oj_problem_id = problem_id
                sj.oj_language = language

            if accepted is True:
                sj.judge_status = "accepted"
                sj.score = 100.0
            elif accepted is False or (accepted is None and result.get("result_code")):
                sj.judge_status = "failed"
                pass_rate = result.get("pass_rate")
                sj.score = round((pass_rate or 0.0) * 100, 1)
            else:
                sj.judge_status = "failed"
                sj.score = 0.0

            # 读取 OJ 查重记录（sim 表），失败不阻塞
            if solution_id:
                sim = self.oj.get_similarity(solution_id)
                if sim.get("similarity") is not None:
                    sj.plagiarism_rate = sim["similarity"]
        except Exception as exc:
            logger.warning("OJ 判题异常，降级为未通过: %s", exc)
            sj.judge_status = "failed"
            sj.score = 0.0

    def close(self) -> None:
        self.oj.close()
