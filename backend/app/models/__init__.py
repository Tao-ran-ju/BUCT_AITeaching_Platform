"""数据模型包：集中导出所有 ORM 模型，便于 alembic / create_all 自动发现。

两类表：
1. 学校 buct_cip 库现有 16 张表（直接映射，不改结构）；
2. 教师端自有 t_ 前缀表（需要持久化但学校表无对应字段时使用，见 scripts/create_teacher_tables.py）。
"""
from app.models.user import ROLE_STUDENT, ROLE_TEACHER, TeacherActor, User
from app.models.class_ import ClassNotice, ClassRecord, ClassRoom, ClassTask, ClassTaskCompletion
from app.models.course import Course, CourseClass, CourseStudent, KnowledgeGraph
from app.models.resource import Resource
from app.models.question import Question
from app.models.assignment import Assignment, AssignmentOj, AssignmentSubmission, SubmissionJudge
from app.models.discussion import DiscussionPost, DiscussionReply
from app.models.team import Team, TeamMember
from app.models.warning import StudentWarning, StudyBehavior
from app.models.message import PersonalMessage
from app.models.qa import QaQuestion

__all__ = [
    "User",
    "TeacherActor",
    "ROLE_TEACHER",
    "ROLE_STUDENT",
    "ClassRoom",
    "ClassRecord",
    "ClassNotice",
    "ClassTask",
    "ClassTaskCompletion",
    "Course",
    "CourseClass",
    "CourseStudent",
    "KnowledgeGraph",
    "Resource",
    "Question",
    "Assignment",
    "AssignmentSubmission",
    "AssignmentOj",
    "SubmissionJudge",
    "DiscussionPost",
    "DiscussionReply",
    "Team",
    "TeamMember",
    "StudentWarning",
    "StudyBehavior",
    "PersonalMessage",
    "QaQuestion",
]
