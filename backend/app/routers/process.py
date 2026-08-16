"""教学过程路由：主题讨论区（发帖 / 回复 / 列表 / 精华与置顶）。"""
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.exceptions import NotFoundError
from app.models.discussion import DiscussionPost, DiscussionReply
from app.models.user import User
from app.routers import ok

router = APIRouter(prefix="/discussions", tags=["教学过程"])


class PostCreate(BaseModel):
    course_id: int
    title: str = Field(..., min_length=1, max_length=128)
    content: str = Field("", max_length=5000)


class ReplyCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=5000)


class PostFlagsUpdate(BaseModel):
    """帖子精华 / 置顶标记（均可选，部分更新）。"""

    is_essence: Optional[bool] = None
    is_top: Optional[bool] = None


def _post_out(p: DiscussionPost, author_name: str | None) -> dict:
    return {
        "id": p.id, "course_id": p.course_id, "author_id": p.author_id,
        "author_name": author_name,
        "title": p.title, "content": p.content,
        "is_top": p.is_top, "is_essence": p.is_essence,
        "created_at": p.created_at.isoformat(),
    }


def _author_map(db: Session, author_ids: set[int]) -> dict[int, str]:
    if not author_ids:
        return {}
    return {
        u.id: u.name
        for u in db.scalars(select(User).where(User.id.in_(author_ids))).all()
    }


@router.get("", summary="讨论区帖子列表")
def list_posts(course_id: int, user: User = Depends(get_current_user),
               db: Session = Depends(get_db)):
    posts = db.scalars(
        select(DiscussionPost)
        .where(DiscussionPost.course_id == course_id)
        .order_by(DiscussionPost.is_top.desc(), DiscussionPost.id.desc())
    ).all()
    name_map = _author_map(db, {p.author_id for p in posts})
    return ok([_post_out(p, name_map.get(p.author_id)) for p in posts])


@router.post("", summary="发布帖子")
def create_post(data: PostCreate, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    post = DiscussionPost(
        course_id=data.course_id, author_id=user.id,
        title=data.title, content=data.content,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return ok({"id": post.id})


@router.patch("/{post_id}", summary="设置精华 / 置顶")
def update_post_flags(post_id: int, data: PostFlagsUpdate,
                     user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)):
    post = db.get(DiscussionPost, post_id)
    if not post:
        raise NotFoundError("帖子不存在")
    if data.is_essence is not None:
        post.is_essence = data.is_essence
    if data.is_top is not None:
        post.is_top = data.is_top
    db.commit()
    db.refresh(post)
    return ok(_post_out(post, user.name))


@router.delete("/{post_id}", summary="删除帖子")
def delete_post(post_id: int, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    post = db.get(DiscussionPost, post_id)
    if not post:
        raise NotFoundError("帖子不存在")
    db.execute(delete(DiscussionReply).where(DiscussionReply.post_id == post_id))
    db.delete(post)
    db.commit()
    return ok(message="帖子已删除")


@router.get("/{post_id}/replies", summary="帖子回复列表")
def list_replies(post_id: int, user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    replies = db.scalars(
        select(DiscussionReply)
        .where(DiscussionReply.post_id == post_id)
        .order_by(DiscussionReply.id)
    ).all()
    name_map = _author_map(db, {r.author_id for r in replies})
    return ok([{
        "id": r.id, "post_id": r.post_id, "author_id": r.author_id,
        "author_name": name_map.get(r.author_id),
        "content": r.content, "created_at": r.created_at.isoformat(),
    } for r in replies])


@router.post("/{post_id}/replies", summary="回复帖子")
def create_reply(post_id: int, data: ReplyCreate,
                 user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    post = db.get(DiscussionPost, post_id)
    if not post:
        raise NotFoundError("帖子不存在")
    reply = DiscussionReply(post_id=post_id, author_id=user.id, content=data.content)
    db.add(reply)
    db.commit()
    db.refresh(reply)
    return ok({"id": reply.id})
