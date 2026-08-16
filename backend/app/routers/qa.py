"""AI 问答助手路由：接收学生提问，自动分流，教师人工回复。"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.routers import ok
from app.schemas.qa import QaAnswerIn, QaAskIn, QaOut
from app.services.qa_service import QaService

router = APIRouter(prefix="/qa", tags=["AI 问答助手"])


@router.post("/ask", summary="学生提问（学生端网关调用）")
def ask_question(data: QaAskIn, db: Session = Depends(get_db)):
    q = QaService.ask(db, data.student_id, data.student_name, data.course_id, data.content)
    return ok({
        "id": q.id,
        "status": q.status,
        "classification": q.classification,
        "auto_answer": q.auto_answer,
        "auto_replied": q.status == "auto_answered",
    }, message="问题已接收")


@router.get("/questions", summary="教师查看待处理问题与统计")
def list_questions(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    result = QaService.list_questions(db)
    return ok({
        "pending": [QaOut.model_validate(q) for q in result["pending"]],
        "stats": result["stats"],
    })


@router.post("/{question_id}/answer", summary="教师人工回复问题")
def answer_question(question_id: int, data: QaAnswerIn,
                    user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    q = QaService.answer(db, question_id, user, data.answer)
    return ok(QaOut.model_validate(q), message="已回复并通知学生")
