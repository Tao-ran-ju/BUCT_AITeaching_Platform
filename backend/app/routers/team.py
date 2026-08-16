"""学习小组路由：建组 / 列表 / 改删 / 指定组长 / 成员管理。"""
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.routers import ok
from app.schemas.team import MemberAddRequest, TeamCreate, TeamOut, TeamUpdate
from app.services.team_service import TeamService

router = APIRouter(prefix="/teams", tags=["学习小组"])


@router.get("", summary="学习小组列表")
def list_teams(
    course_id: Optional[int] = Query(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    teams = TeamService.list_teams(db, course_id)
    return ok([TeamOut.model_validate(t) for t in teams])


@router.post("", summary="创建学习小组")
def create_team(data: TeamCreate, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    team = TeamService.create_team(db, data)
    return ok(TeamOut.model_validate(team))


@router.put("/{team_id}", summary="更新学习小组")
def update_team(team_id: int, data: TeamUpdate,
                user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    team = TeamService.update_team(db, team_id, data)
    return ok(TeamOut.model_validate(team))


@router.delete("/{team_id}", summary="删除学习小组")
def delete_team(team_id: int, user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    TeamService.delete_team(db, team_id)
    return ok(message="学习小组已删除")


@router.post("/{team_id}/members", summary="批量添加成员")
def add_members(team_id: int, data: MemberAddRequest,
                user: User = Depends(get_current_user),
                db: Session = Depends(get_db)):
    added = TeamService.add_members(db, team_id, data.student_ids)
    return ok({"added": added}, message=f"成功添加 {added} 名成员")


@router.delete("/{team_id}/members/{student_id}", summary="移除成员")
def remove_member(team_id: int, student_id: int,
                  user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    TeamService.remove_member(db, team_id, student_id)
    return ok(message="已移除该成员")
