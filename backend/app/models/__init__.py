"""数据模型包：集中导出所有 ORM 模型，便于 alembic 自动发现。"""
from app.models.user import User
from app.models.class_ import ClassRoom, ClassStudent
from app.models.course import Course, Chapter, KnowledgePoint
from app.models.resource import Resource
from app.models.question import Question
from app.models.assignment import Assignment, AssignmentSubmission
from app.models.discussion import DiscussionPost, DiscussionReply
from app.models.team import Team, TeamMember
from app.models.warning import StudentWarning, StudyBehavior
from app.models.message import MessageContent, MessageReceiver
from app.models.task import Task, TaskAssignment
from app.models.qa import QaQuestion

__all__ = [
    "User",
    "ClassRoom",
    "ClassStudent",
    "Course",
    "Chapter",
    "KnowledgePoint",
    "Resource",
    "Question",
    "Assignment",
    "AssignmentSubmission",
    "DiscussionPost",
    "DiscussionReply",
    "Team",
    "TeamMember",
    "StudentWarning",
    "StudyBehavior",
    "MessageContent",
    "MessageReceiver",
    "Task",
    "TaskAssignment",
    "QaQuestion",
]
