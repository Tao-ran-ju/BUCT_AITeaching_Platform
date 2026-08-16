-- ============================================
-- BUCT AI 教学平台 数据库初始化脚本（MySQL 8.0）
-- 执行方式：mysql -u root -p < init.sql
-- ============================================

CREATE DATABASE IF NOT EXISTS `buct_ai_teaching`
  DEFAULT CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `buct_ai_teaching`;

-- ---------- 用户表（教师/学生/管理员统一存放） ----------
CREATE TABLE IF NOT EXISTS `user` (
  `id`            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `username`      VARCHAR(64)     NOT NULL COMMENT '工号/学号',
  `password_hash` VARCHAR(255)    NOT NULL COMMENT 'PBKDF2 哈希',
  `name`          VARCHAR(64)     NOT NULL COMMENT '姓名',
  `role`          VARCHAR(16)     NOT NULL DEFAULT 'teacher' COMMENT 'admin/teacher/student',
  `email`         VARCHAR(128)    NULL,
  `phone`         VARCHAR(32)     NULL,
  `department`    VARCHAR(128)    NULL COMMENT '所属部门/学院',
  `position`      VARCHAR(64)     NULL COMMENT '职称（教师）',
  `avatar`        VARCHAR(255)    NULL,
  `status`        VARCHAR(16)     NOT NULL DEFAULT 'active' COMMENT 'active/disabled',
  `created_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_user_username` (`username`)
) ENGINE=InnoDB COMMENT='用户表';

-- ---------- 班级表 ----------
CREATE TABLE IF NOT EXISTS `class` (
  `id`          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name`        VARCHAR(128)    NOT NULL COMMENT '班级名称',
  `grade`       VARCHAR(16)     NULL COMMENT '年级，如2024',
  `major`       VARCHAR(128)    NULL COMMENT '专业',
  `description` VARCHAR(500)    NULL,
  `teacher_id`  BIGINT UNSIGNED NULL COMMENT '班主任',
  `created_at`  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_class_teacher` (`teacher_id`)
) ENGINE=InnoDB COMMENT='班级表';

-- ---------- 班级-学生关联表（一个学生可多班级） ----------
CREATE TABLE IF NOT EXISTS `class_student` (
  `id`         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `class_id`   BIGINT UNSIGNED NOT NULL,
  `student_id` BIGINT UNSIGNED NOT NULL,
  `joined_at`  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_class_student` (`class_id`, `student_id`),
  KEY `idx_cs_student` (`student_id`)
) ENGINE=InnoDB COMMENT='班级学生关联表';

-- ---------- 课程表 ----------
CREATE TABLE IF NOT EXISTS `course` (
  `id`          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `name`        VARCHAR(128)    NOT NULL,
  `code`        VARCHAR(32)     NULL COMMENT '课程编号',
  `cover`       VARCHAR(255)    NULL COMMENT '封面图路径',
  `description` TEXT            NULL,
  `teacher_id`  BIGINT UNSIGNED NOT NULL COMMENT '主讲教师',
  `status`      VARCHAR(16)     NOT NULL DEFAULT 'published' COMMENT 'draft/published/archived',
  `created_at`  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at`  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_course_teacher` (`teacher_id`),
  KEY `idx_course_name` (`name`)
) ENGINE=InnoDB COMMENT='课程表';

-- ---------- 章节表 ----------
CREATE TABLE IF NOT EXISTS `chapter` (
  `id`          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `course_id`   BIGINT UNSIGNED NOT NULL,
  `title`       VARCHAR(128)    NOT NULL,
  `description` TEXT            NULL,
  `sort_order`  INT             NOT NULL DEFAULT 0,
  `created_at`  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_chapter_course` (`course_id`)
) ENGINE=InnoDB COMMENT='章节表';

-- ---------- 知识点表（支持多级） ----------
CREATE TABLE IF NOT EXISTS `knowledge_point` (
  `id`          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `chapter_id`  BIGINT UNSIGNED NOT NULL,
  `parent_id`   BIGINT UNSIGNED NULL COMMENT '父知识点',
  `name`        VARCHAR(128)    NOT NULL,
  `description` TEXT            NULL,
  `ai_summary`  TEXT            NULL COMMENT 'AI 生成的知识点梗概',
  `sort_order`  INT             NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_kp_chapter` (`chapter_id`)
) ENGINE=InnoDB COMMENT='知识点表';

-- ---------- 教学资源表 ----------
CREATE TABLE IF NOT EXISTS `resource` (
  `id`            BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `title`         VARCHAR(128)    NOT NULL,
  `resource_type` VARCHAR(32)     NOT NULL COMMENT 'document/video/audio/image/code/other',
  `file_path`     VARCHAR(255)    NOT NULL COMMENT '存储相对路径',
  `file_size`     BIGINT          NULL COMMENT '字节数',
  `course_id`     BIGINT UNSIGNED NULL,
  `uploader_id`   BIGINT UNSIGNED NOT NULL,
  `visibility`    VARCHAR(16)     NOT NULL DEFAULT 'course' COMMENT 'public/course/private',
  `summary`       TEXT            NULL COMMENT 'AI 自动摘要',
  `keywords`      VARCHAR(255)    NULL COMMENT 'AI 提取关键词',
  `created_at`    DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_res_course` (`course_id`),
  KEY `idx_res_uploader` (`uploader_id`)
) ENGINE=InnoDB COMMENT='教学资源表';

-- ---------- 题库表 ----------
CREATE TABLE IF NOT EXISTS `question` (
  `id`                 BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `title`              VARCHAR(255)    NOT NULL COMMENT '题目标题/题干',
  `question_type`      VARCHAR(32)     NOT NULL DEFAULT 'choice' COMMENT 'choice/fill/true_false/code',
  `content`            TEXT            NULL COMMENT '详细题干',
  `answer`             TEXT            NULL COMMENT '标准答案',
  `analysis`           TEXT            NULL COMMENT '解析',
  `difficulty`         INT             NOT NULL DEFAULT 3 COMMENT '1-5',
  `knowledge_point_id` BIGINT UNSIGNED NULL,
  `course_id`          BIGINT UNSIGNED NULL,
  `created_by`         BIGINT UNSIGNED NOT NULL,
  `created_at`         DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_q_kp` (`knowledge_point_id`),
  KEY `idx_q_course` (`course_id`)
) ENGINE=InnoDB COMMENT='题库表';

-- ---------- 作业表 ----------
CREATE TABLE IF NOT EXISTS `assignment` (
  `id`           BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `course_id`    BIGINT UNSIGNED NOT NULL,
  `class_id`     BIGINT UNSIGNED NULL,
  `title`        VARCHAR(128)    NOT NULL,
  `description`  TEXT            NULL,
  `question_ids` TEXT            NULL COMMENT '关联题目ID，JSON数组',
  `deadline`     DATETIME        NULL,
  `status`       VARCHAR(16)     NOT NULL DEFAULT 'published' COMMENT 'draft/published/closed',
  `created_at`   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_assign_course` (`course_id`)
) ENGINE=InnoDB COMMENT='作业表';

-- ---------- 作业提交表 ----------
CREATE TABLE IF NOT EXISTS `assignment_submission` (
  `id`              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `assignment_id`   BIGINT UNSIGNED NOT NULL,
  `student_id`      BIGINT UNSIGNED NOT NULL,
  `content`         TEXT            NULL COMMENT '提交内容（代码/文本）',
  `submit_time`     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `judge_status`    VARCHAR(16)     NOT NULL DEFAULT 'pending' COMMENT 'pending/judging/accepted/failed',
  `score`           DECIMAL(6,2)    NULL COMMENT '得分',
  `ai_comment`      TEXT            NULL COMMENT 'AI 个性化评语',
  `plagiarism_rate` DECIMAL(5,4)    NULL COMMENT '查重率 0-1',
  PRIMARY KEY (`id`),
  KEY `idx_sub_assign` (`assignment_id`),
  KEY `idx_sub_student` (`student_id`)
) ENGINE=InnoDB COMMENT='作业提交表';

-- ---------- 讨论区帖子表 ----------
CREATE TABLE IF NOT EXISTS `discussion_post` (
  `id`         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `course_id`  BIGINT UNSIGNED NOT NULL,
  `author_id`  BIGINT UNSIGNED NOT NULL,
  `title`      VARCHAR(128)    NOT NULL,
  `content`    TEXT            NULL,
  `is_top`     TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '置顶',
  `is_essence` TINYINT(1)      NOT NULL DEFAULT 0 COMMENT '精华',
  `created_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_post_course` (`course_id`)
) ENGINE=InnoDB COMMENT='讨论区帖子表';

-- ---------- 讨论区回复表 ----------
CREATE TABLE IF NOT EXISTS `discussion_reply` (
  `id`         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `post_id`    BIGINT UNSIGNED NOT NULL,
  `author_id`  BIGINT UNSIGNED NOT NULL,
  `content`    TEXT            NOT NULL,
  `created_at` DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_reply_post` (`post_id`)
) ENGINE=InnoDB COMMENT='讨论区回复表';

-- ---------- 学习社群/竞赛队伍表 ----------
CREATE TABLE IF NOT EXISTS `team` (
  `id`          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `course_id`   BIGINT UNSIGNED NULL,
  `name`        VARCHAR(128)    NOT NULL,
  `leader_id`   BIGINT UNSIGNED NOT NULL COMMENT '组长/队长',
  `description` TEXT            NULL,
  `created_at`  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_team_course` (`course_id`)
) ENGINE=InnoDB COMMENT='学习社群表';

-- ---------- 队伍成员表 ----------
CREATE TABLE IF NOT EXISTS `team_member` (
  `id`         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `team_id`    BIGINT UNSIGNED NOT NULL,
  `student_id` BIGINT UNSIGNED NOT NULL,
  `joined_at`  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_tm_team` (`team_id`),
  KEY `idx_tm_student` (`student_id`)
) ENGINE=InnoDB COMMENT='队伍成员表';

-- ---------- 学情预警表 ----------
CREATE TABLE IF NOT EXISTS `student_warning` (
  `id`          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `student_id`  BIGINT UNSIGNED NOT NULL,
  `course_id`   BIGINT UNSIGNED NULL,
  `risk_level`  VARCHAR(16)     NOT NULL DEFAULT 'medium' COMMENT 'high/medium/low',
  `reason`      TEXT            NULL COMMENT '预警原因',
  `suggestion`  TEXT            NULL COMMENT '干预建议（AI 生成）',
  `is_resolved` TINYINT(1)      NOT NULL DEFAULT 0,
  `created_at`  DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_warn_student` (`student_id`),
  KEY `idx_warn_course` (`course_id`)
) ENGINE=InnoDB COMMENT='学情预警表';

-- ---------- 学习行为表（预警分析数据源） ----------
CREATE TABLE IF NOT EXISTS `study_behavior` (
  `id`                BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  `student_id`        BIGINT UNSIGNED NOT NULL,
  `course_id`         BIGINT UNSIGNED NULL,
  `login_duration`    INT             NOT NULL DEFAULT 0 COMMENT '当日登录时长(秒)',
  `resource_visits`   INT             NOT NULL DEFAULT 0 COMMENT '当日资源访问次数',
  `submit_delay_days` INT             NULL COMMENT '最近一次提交延迟天数',
  `homework_score`    DECIMAL(6,2)    NULL COMMENT '最近一次作业得分',
  `behavior_date`     DATE            NOT NULL COMMENT '行为日期',
  `created_at`        DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_behavior_student` (`student_id`),
  KEY `idx_behavior_date` (`behavior_date`)
) ENGINE=InnoDB COMMENT='学习行为表';
