"""教师端自有表建表脚本（幂等）。

学校 buct_cip 库的 16 张表已存在、不得改动；教师端额外需要持久化的功能
（OJ 评测/AI 评语/查重、讨论区、学习小组、AI 问答、题库、学情预警、学习行为）
没有对应字段，故新增 t_ 前缀的教师端自有表。

用法（在 backend/ 目录下）：
    python scripts/create_teacher_tables.py

幂等：全部使用 CREATE TABLE IF NOT EXISTS，可重复执行。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import text  # noqa: E402

from app.database import engine  # noqa: E402

# 建表 DDL（与 app/models/*.py 中的 ORM 定义一一对应，字段名/类型/索引保持一致）
DDL_STATEMENTS = [
    # 1. 作业评测 / AI 评语 / 查重 扩展（对应 assignment_submissions 的补充信息）
    """
    CREATE TABLE IF NOT EXISTS t_submission_judge (
        id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        submission_id   BIGINT UNSIGNED NOT NULL COMMENT 'assignment_submissions.id',
        assignment_id   BIGINT UNSIGNED NOT NULL COMMENT '作业 ID（冗余）',
        student_user_id INT             NOT NULL COMMENT '学生 user_rft.id',
        judge_status    VARCHAR(20)     NOT NULL DEFAULT 'pending' COMMENT 'pending/judging/accepted/failed',
        oj_solution_id  INT             NULL COMMENT 'OJ 提交编号 solution_id',
        oj_problem_id   INT             NULL COMMENT 'OJ 题目 ID',
        oj_language     VARCHAR(20)     NULL COMMENT 'OJ 判题语言',
        score           DECIMAL(5,2)    NULL COMMENT '评测得分',
        ai_comment      TEXT            NULL COMMENT 'AI 个性化评语',
        plagiarism_rate DECIMAL(5,2)    NULL COMMENT '查重率 0-1',
        created_at      BIGINT          NOT NULL COMMENT '创建时间（UNIX 时间戳）',
        edited_at       BIGINT          NOT NULL COMMENT '最后编辑时间',
        PRIMARY KEY (id),
        UNIQUE KEY uq_t_submission_judge_submission (submission_id),
        KEY idx_t_submission_judge_assignment (assignment_id),
        KEY idx_t_submission_judge_student (student_user_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='教师端自有：作业评测/AI评语/查重扩展'
    """,
    # 1.5. 作业与 OJ 题目/语言绑定配置（assignments 表无 OJ 字段）
    """
    CREATE TABLE IF NOT EXISTS t_assignment_oj (
        id            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        assignment_id BIGINT UNSIGNED NOT NULL COMMENT '作业 ID（唯一）',
        oj_problem_id INT             NULL COMMENT 'OJ 题目 ID',
        oj_language   VARCHAR(20)     NULL COMMENT 'OJ 判题语言',
        created_at    BIGINT          NOT NULL COMMENT '创建时间（UNIX 时间戳）',
        edited_at     BIGINT          NOT NULL COMMENT '最后编辑时间',
        PRIMARY KEY (id),
        UNIQUE KEY uq_t_assignment_oj_assignment (assignment_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='教师端自有：作业-OJ 绑定配置'
    """,
    # 2. 主题讨论区 —— 帖子
    """
    CREATE TABLE IF NOT EXISTS t_discussion_post (
        id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        course_id      BIGINT UNSIGNED NOT NULL COMMENT '课程 ID',
        author_user_id INT             NOT NULL COMMENT '作者 user_rft.id',
        title          VARCHAR(200)    NOT NULL COMMENT '帖子标题',
        content        TEXT            NOT NULL COMMENT '帖子正文',
        is_pinned      INT             NOT NULL DEFAULT 0 COMMENT '0=否 1=置顶',
        is_locked      INT             NOT NULL DEFAULT 0 COMMENT '0=否 1=锁定',
        is_essence     INT             NOT NULL DEFAULT 0 COMMENT '0=否 1=精华',
        status         INT             NOT NULL DEFAULT 0 COMMENT '0=正常',
        created_at     BIGINT          NOT NULL COMMENT '创建时间',
        edited_at      BIGINT          NOT NULL COMMENT '最后编辑时间',
        PRIMARY KEY (id),
        KEY idx_t_discussion_post_course (course_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='教师端自有：讨论区帖子'
    """,
    # 3. 主题讨论区 —— 回复
    """
    CREATE TABLE IF NOT EXISTS t_discussion_reply (
        id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        post_id        BIGINT UNSIGNED NOT NULL COMMENT '帖子 ID',
        author_user_id INT             NOT NULL COMMENT '作者 user_rft.id',
        content        TEXT            NOT NULL COMMENT '回复内容',
        status         INT             NOT NULL DEFAULT 0 COMMENT '0=正常',
        created_at     BIGINT          NOT NULL COMMENT '创建时间',
        edited_at      BIGINT          NOT NULL COMMENT '最后编辑时间',
        PRIMARY KEY (id),
        KEY idx_t_discussion_reply_post (post_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='教师端自有：讨论区回复'
    """,
    # 4. 学习小组
    """
    CREATE TABLE IF NOT EXISTS t_team (
        id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        course_id      BIGINT UNSIGNED NOT NULL COMMENT '课程 ID',
        name           VARCHAR(200)    NOT NULL COMMENT '小组名称',
        description    VARCHAR(500)    NULL COMMENT '小组描述',
        leader_user_id INT             NULL COMMENT '组长 user_rft.id',
        created_at     BIGINT          NOT NULL COMMENT '创建时间',
        edited_at      BIGINT          NOT NULL COMMENT '最后编辑时间',
        PRIMARY KEY (id),
        KEY idx_t_team_course (course_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='教师端自有：学习小组'
    """,
    # 5. 学习小组 —— 成员
    """
    CREATE TABLE IF NOT EXISTS t_team_member (
        id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        team_id         BIGINT UNSIGNED NOT NULL COMMENT '小组 ID',
        student_user_id INT             NOT NULL COMMENT '学生 user_rft.id',
        created_at      BIGINT          NOT NULL COMMENT '加入时间',
        PRIMARY KEY (id),
        KEY idx_t_team_member_team (team_id),
        KEY idx_t_team_member_student (student_user_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='教师端自有：小组-成员关系'
    """,
    # 6. AI 问答助手
    """
    CREATE TABLE IF NOT EXISTS t_qa_question (
        id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        course_id       BIGINT UNSIGNED NULL COMMENT '关联课程 ID（可选）',
        student_user_id INT             NOT NULL COMMENT '提问学生 user_rft.id',
        question        TEXT            NOT NULL COMMENT '问题内容',
        answer          TEXT            NULL COMMENT '回复内容（AI 或教师）',
        answered_by     INT             NULL COMMENT '回答教师 user_rft.id',
        answered_at     BIGINT          NULL COMMENT '回答时间（UNIX 时间戳）',
        status          INT             NOT NULL DEFAULT 0 COMMENT '0=待回答 1=已回答',
        created_at      BIGINT          NOT NULL COMMENT '提问时间',
        PRIMARY KEY (id),
        KEY idx_t_qa_question_course (course_id),
        KEY idx_t_qa_question_student (student_user_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='教师端自有：AI 问答记录'
    """,
    # 7. 题库
    """
    CREATE TABLE IF NOT EXISTS t_question (
        id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        course_id  BIGINT UNSIGNED NULL COMMENT '关联课程 ID（可选）',
        type       VARCHAR(20)     NOT NULL COMMENT 'choice/judge/short',
        content    TEXT            NOT NULL COMMENT '题干内容',
        options    TEXT            NULL COMMENT '选项 JSON 字符串',
        answer     TEXT            NULL COMMENT '标准答案',
        analysis   TEXT            NULL COMMENT '解析',
        difficulty INT             NOT NULL DEFAULT 1 COMMENT '难度 1-5',
        created_by INT             NOT NULL COMMENT '创建者 user_rft.id',
        created_at BIGINT          NOT NULL COMMENT '创建时间',
        edited_at  BIGINT          NOT NULL COMMENT '最后编辑时间',
        PRIMARY KEY (id),
        KEY idx_t_question_course (course_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='教师端自有：题库'
    """,
    # 8. 学情预警
    """
    CREATE TABLE IF NOT EXISTS t_student_warning (
        id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        course_id       BIGINT UNSIGNED NULL COMMENT '关联课程 ID',
        student_user_id INT             NOT NULL COMMENT '学生 user_rft.id',
        warning_type    VARCHAR(50)     NOT NULL COMMENT 'submit_delay/absent/low_score',
        level           VARCHAR(20)     NOT NULL DEFAULT 'normal' COMMENT 'normal/warning/danger',
        detail          TEXT            NULL COMMENT '预警详情',
        suggestion      TEXT            NULL COMMENT 'AI 干预建议',
        intervention    TEXT            NULL COMMENT '教师干预措施记录',
        status          VARCHAR(20)     NOT NULL DEFAULT 'open' COMMENT 'open/resolved',
        created_at      BIGINT          NOT NULL COMMENT '创建时间',
        resolved_at     BIGINT          NULL COMMENT '处理时间',
        PRIMARY KEY (id),
        KEY idx_t_student_warning_course (course_id),
        KEY idx_t_student_warning_student (student_user_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='教师端自有：学情预警'
    """,
    # 9. 学习行为日志
    """
    CREATE TABLE IF NOT EXISTS t_study_behavior (
        id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        student_user_id INT             NOT NULL COMMENT '学生 user_rft.id',
        course_id       BIGINT UNSIGNED NULL COMMENT '课程 ID',
        behavior_type   VARCHAR(50)     NOT NULL COMMENT 'login/resource_view/submit',
        value           TEXT            NULL COMMENT '行为附加数据（JSON）',
        created_at      BIGINT          NOT NULL COMMENT '发生时间（UNIX 时间戳）',
        PRIMARY KEY (id),
        KEY idx_t_study_behavior_student (student_user_id),
        KEY idx_t_study_behavior_course (course_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='教师端自有：学习行为日志'
    """,
]


def main() -> None:
    print(f"连接数据库: {engine.url.render_as_string(hide_password=True)}")
    with engine.begin() as conn:
        for ddl in DDL_STATEMENTS:
            conn.execute(text(ddl))
    print(f"教师端自有表创建/校验完成，共 {len(DDL_STATEMENTS)} 张。")


if __name__ == "__main__":
    main()
