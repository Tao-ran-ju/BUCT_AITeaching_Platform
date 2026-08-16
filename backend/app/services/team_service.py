"""学习小组服务：建组 / 列表 / 改删 / 指定组长 / 成员管理。"""
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.exceptions import NotFoundError, ValidateError
from app.models.team import Team, TeamMember
from app.models.user import User
from app.schemas.team import TeamCreate, TeamUpdate


class TeamService:
    """学习小组 / 竞赛队伍业务逻辑。"""

    @staticmethod
    def _member_rows(db: Session, team_id: int) -> list[TeamMember]:
        return list(
            db.scalars(
                select(TeamMember).where(TeamMember.team_id == team_id)
            ).all()
        )

    @staticmethod
    def _to_out(db: Session, team: Team) -> dict:
        rows = TeamService._member_rows(db, team.id)
        student_ids = [r.student_id for r in rows]
        users = (
            db.scalars(select(User).where(User.id.in_(student_ids))).all()
            if student_ids else []
        )
        user_map = {u.id: u for u in users}
        members = [
            {"student_id": sid, "name": user_map[sid].name, "username": user_map[sid].username}
            for sid in student_ids if sid in user_map
        ]
        return {
            "id": team.id,
            "name": team.name,
            "course_id": team.course_id,
            "leader_id": team.leader_id,
            "description": team.description,
            "created_at": team.created_at,
            "member_count": len(rows),
            "members": members,
        }

    @staticmethod
    def list_teams(db: Session, course_id: int | None = None) -> list[dict]:
        stmt = select(Team)
        if course_id is not None:
            stmt = stmt.where(Team.course_id == course_id)
        teams = db.scalars(stmt.order_by(Team.id.desc())).all()
        return [TeamService._to_out(db, t) for t in teams]

    @staticmethod
    def get_team(db: Session, team_id: int) -> Team:
        team = db.get(Team, team_id)
        if not team:
            raise NotFoundError("学习小组不存在")
        return team

    @staticmethod
    def create_team(db: Session, data: TeamCreate) -> dict:
        # 校验组长存在且为学生
        leader = db.get(User, data.leader_id)
        if not leader:
            raise ValidateError("组长不存在")
        team = Team(
            name=data.name,
            course_id=data.course_id,
            leader_id=data.leader_id,
            description=data.description,
        )
        db.add(team)
        db.flush()
        # 组长自动纳入成员
        db.add(TeamMember(team_id=team.id, student_id=data.leader_id))
        db.commit()
        db.refresh(team)
        return TeamService._to_out(db, team)

    @staticmethod
    def update_team(db: Session, team_id: int, data: TeamUpdate) -> dict:
        team = TeamService.get_team(db, team_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(team, field, value)
        db.commit()
        db.refresh(team)
        return TeamService._to_out(db, team)

    @staticmethod
    def delete_team(db: Session, team_id: int) -> None:
        team = TeamService.get_team(db, team_id)
        db.execute(delete(TeamMember).where(TeamMember.team_id == team_id))
        db.delete(team)
        db.commit()

    @staticmethod
    def add_members(db: Session, team_id: int, student_ids: list[int]) -> int:
        TeamService.get_team(db, team_id)
        added = 0
        for sid in set(student_ids):
            exists = db.scalar(
                select(TeamMember).where(
                    TeamMember.team_id == team_id,
                    TeamMember.student_id == sid,
                )
            )
            if not exists:
                db.add(TeamMember(team_id=team_id, student_id=sid))
                added += 1
        db.commit()
        return added

    @staticmethod
    def remove_member(db: Session, team_id: int, student_id: int) -> None:
        TeamService.get_team(db, team_id)
        db.execute(
            delete(TeamMember).where(
                TeamMember.team_id == team_id,
                TeamMember.student_id == student_id,
            )
        )
        db.commit()
