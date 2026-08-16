"""AI 备课路由：教案 / 大纲 / PPT / 题库 / 组卷 / 题目评估 / 项目 / 教学报告 / 摘要。"""
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.dependencies import get_current_user
from app.exceptions import ValidateError
from app.models.user import User
from app.routers import ok
from app.services.llm_teaching_service import LLMTeachingService

router = APIRouter(prefix="/teaching", tags=["AI 备课中心"])


class TeachingPlanRequest(BaseModel):
    knowledge_point: str = Field(..., min_length=1, description="知识点")
    goal: Optional[str] = None


class OutlineRequest(BaseModel):
    course_name: str = Field(..., min_length=1, description="课程名称 / 主题")
    goal: Optional[str] = None


class PptRequest(BaseModel):
    topic: str = Field(..., min_length=1, description="授课主题")
    objective: Optional[str] = None
    outline: Optional[str] = None


class QuizRequest(BaseModel):
    knowledge_point: str = Field(..., min_length=1)
    count: int = Field(5, ge=1, le=20)
    difficulty: int = Field(3, ge=1, le=5)


class ExamPaperRequest(BaseModel):
    knowledge_point: str = Field(..., min_length=1, description="考核知识点")
    count: int = Field(10, ge=1, le=30)
    difficulty: int = Field(3, ge=1, le=5)
    question_types: Optional[str] = None


class QuestionReviewRequest(BaseModel):
    question: str = Field(..., min_length=10, description="待评估的题目文本")


class ProjectRequest(BaseModel):
    topic: str = Field(..., min_length=1, description="项目主题")
    difficulty: int = Field(3, ge=1, le=5)
    goal: Optional[str] = None


class ReportRequest(BaseModel):
    course_name: str = Field(..., min_length=1, description="课程名称")
    semester_data: Optional[str] = None


class SummarizeRequest(BaseModel):
    content: str = Field(..., min_length=10)


def _generate(fn, *args):
    try:
        return ok({"content": fn(*args)})
    except RuntimeError as exc:
        raise ValidateError(str(exc))


@router.post("/plan", summary="AI 生成教案")
def generate_plan(data: TeachingPlanRequest, user: User = Depends(get_current_user)):
    return _generate(LLMTeachingService.generate_teaching_plan,
                     data.knowledge_point, data.goal)


@router.post("/outline", summary="AI 生成课程大纲")
def generate_outline(data: OutlineRequest, user: User = Depends(get_current_user)):
    return _generate(LLMTeachingService.generate_outline,
                     data.course_name, data.goal)


@router.post("/ppt", summary="AI 生成 PPT 大纲")
def generate_ppt(data: PptRequest, user: User = Depends(get_current_user)):
    return _generate(LLMTeachingService.generate_ppt,
                     data.topic, data.objective, data.outline)


@router.post("/quiz", summary="AI 生成题库")
def generate_quiz(data: QuizRequest, user: User = Depends(get_current_user)):
    return _generate(LLMTeachingService.generate_quiz,
                     data.knowledge_point, data.count, data.difficulty)


@router.post("/exam-paper", summary="AI 智能组卷")
def generate_exam_paper(data: ExamPaperRequest, user: User = Depends(get_current_user)):
    return _generate(LLMTeachingService.generate_exam_paper,
                     data.knowledge_point, data.count, data.difficulty, data.question_types)


@router.post("/question-review", summary="AI 题目质量评估")
def review_question(data: QuestionReviewRequest, user: User = Depends(get_current_user)):
    return _generate(LLMTeachingService.review_question, data.question)


@router.post("/project", summary="AI 实践项目设计助手")
def design_project(data: ProjectRequest, user: User = Depends(get_current_user)):
    return _generate(LLMTeachingService.design_project,
                     data.topic, data.difficulty, data.goal)


@router.post("/report", summary="AI 教学报告")
def generate_report(data: ReportRequest, user: User = Depends(get_current_user)):
    return _generate(LLMTeachingService.generate_teaching_report,
                     data.course_name, data.semester_data)


@router.post("/summarize", summary="AI 资源摘要")
def summarize(data: SummarizeRequest, user: User = Depends(get_current_user)):
    return _generate(LLMTeachingService.summarize_resource, data.content)
