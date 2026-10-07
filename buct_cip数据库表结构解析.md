# buct_cip 数据库表结构全解析

> **项目背景**：北京化工大学信息科学与技术学院教学平台数据库
> **核心业务**：教师端布置作业/任务 → 学生端完成并提交 → 教师端批阅反馈
> **数据库引擎**：MariaDB 10.11.13（兼容 MySQL 协议）
> **表总数**：16 张

---

## 目录

- [一、整体架构概览](#一整体架构概览)
- [二、用户体系（3 张表）](#二用户体系3-张表)
  - [2.1 user（旧版用户表）](#21-user旧版用户表)
  - [2.2 user_rft（新版用户表）](#22-user_rft新版用户表)
  - [2.3 teacher_actors（教师账号表）](#23-teacher_actors教师账号表)
- [三、课程体系（4 张表）](#三课程体系4-张表)
  - [3.1 courses（课程表）](#31-courses课程表)
  - [3.2 course_classes（课程-班级关联表）](#32-course_classes课程-班级关联表)
  - [3.3 course_students（课程-学生关联表）](#33-course_students课程-学生关联表)
  - [3.4 course_resources（课程资源表）](#34-course_resources课程资源表)
- [四、班级体系（5 张表）](#四班级体系5-张表)
  - [4.1 class（教学班级表）](#41-class教学班级表)
  - [4.2 class_record（班级成员记录表）](#42-class_record班级成员记录表)
  - [4.3 class_notices（班级公告表）](#43-class_notices班级公告表)
  - [4.4 class_tasks（班级任务表）](#44-class_tasks班级任务表)
  - [4.5 class_task_completions（班级任务完成记录表）](#45-class_task_completions班级任务完成记录表)
- [五、作业体系（2 张表）](#五作业体系2-张表)
  - [5.1 assignments（作业表）](#51-assignments作业表)
  - [5.2 assignment_submissions（作业提交表）](#52-assignment_submissions作业提交表)
- [六、消息体系（1 张表）](#六消息体系1-张表)
  - [6.1 personal_messages（个人消息表）](#61-personal_messages个人消息表)
- [七、知识图谱（1 张表）](#七知识图谱1-张表)
  - [7.1 knowledge_graphs（知识图表）](#71-knowledge_graphs知识图表)
- [八、表间关系与业务流转](#八表间关系与业务流转)
- [九、设计特点与注意事项](#九设计特点与注意事项)

---

## 一、整体架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户体系 (User)                            │
│   user（旧）  │  user_rft（新）  │  teacher_actors（教师）       │
└────────┬────────────────┬───────────────────┬───────────────────┘
         │                │                   │
         ▼                ▼                   ▼
┌─────────────────────────────────────────────────────────────────┐
│                      课程体系 (Course)                            │
│   courses → course_classes → course_students → course_resources │
└────────┬────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      班级体系 (Class)                             │
│   class → class_record → class_notices                           │
│         → class_tasks → class_task_completions                   │
└────────┬────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      作业体系 (Assignment)                        │
│   assignments → assignment_submissions                            │
└────────┬────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────────┐    ┌──────────────────────┐
│  消息 personal_messages │    │  知识图谱 knowledge_graphs │
└──────────────────────┘    └──────────────────────┘
```

**业务核心链路**：
1. 教师创建课程（courses）→ 关联教学班级（course_classes）
2. 学生加入班级（class_record）/ 加入课程（course_students）
3. 教师发布作业（assignments）或班级任务（class_tasks）
4. 学生提交作业（assignment_submissions）或完成任务（class_task_completions）
5. 教师批阅打分、写反馈；系统通过 personal_messages 推送通知

---

## 二、用户体系（3 张表）

### 2.1 user（旧版用户表）

**文件**：`user.sql`
**定位**：学生端原始用户表，设计较早期，字段较少，无状态管理、无时间戳。

| 字段名 | 类型 | 约束 | 含义 |
|--------|------|------|------|
| `uid` | int(10) | 主键，自增 | 用户唯一 ID |
| `uname` | varchar(30) | NOT NULL，唯一 | 用户名/学号（登录账号） |
| `password` | varchar(255) | NOT NULL | 登录密码（明文存储，未加密） |
| `class_` | varchar(255) | 可空 | 行政班级（字段名带下划线避免 SQL 关键字冲突） |
| `college` | varchar(255) | 可空 | 学院 |
| `gender` | int | 可空 | 性别（0=男，1=女，未明确注释） |
| `major` | varchar(255) | 可空 | 专业 |
| `name` | varchar(255) | 可空 | 真实姓名 |
| `role` | int | 可空 | 角色（未明确注释，推测 0=教师，1=学生） |

**索引**：`uname` 唯一索引

**特点与问题**：
- 密码明文存储，存在安全隐患
- 无 `created_at` / `edited_at` 时间戳
- 无账号状态字段（无法禁用/冻结账号）
- 字段均允许为空，数据完整性约束较弱
- 属于早期学生端遗留表，后续被 `user_rft` 替代

---

### 2.2 user_rft（新版用户表）

**文件**：`user_rft.sql`
**定位**：重构版（Refactor）用户表，统一管理教师和学生，字段完整、约束严格、有完整注释。

| 字段名 | 类型 | 约束 | 含义 |
|--------|------|------|------|
| `id` | int | 主键，自增 | 记录唯一 ID |
| `uid` | varchar(255) | NOT NULL，唯一 | 用户名/学号/工号（登录账号） |
| `status` | int | NOT NULL | 用户状态（0=正常，其他值待定义） |
| `reason` | varchar(255) | 可空 | 设为当前状态的原因（如禁用原因） |
| `password` | varchar(255) | NOT NULL | 登录密码（bcrypt 加密存储，如 `$2b$10$...`） |
| `name` | varchar(255) | NOT NULL | 用户真实姓名 |
| `role` | int | NOT NULL | 角色（**0=教师，1=学生**） |
| `gender` | int | NOT NULL | 性别（**0=男，1=女**） |
| `college` | varchar(255) | NOT NULL | 学院名称 |
| `grade` | varchar(255) | 可空 | 所属年级（仅学生需要） |
| `class` | varchar(255) | 可空 | 行政班级（仅学生需要） |
| `major` | varchar(255) | 可空 | 专业（仅学生需要） |
| `created_at` | int | NOT NULL | 注册时间（UNIX 时间戳，后端填充） |
| `edited_at` | int | NOT NULL | 最后编辑时间（UNIX 时间戳） |
| `created_by` | int | NOT NULL | 创建者 ID（谁创建了这个账号） |

**索引**：
- `user_uid_uindex`：uid 唯一索引
- `user_rft_created_by_index`：创建者索引
- `user_rft_name_index`：姓名索引
- `user_rft_role_index`：角色索引
- `user_rft_status_index`：状态索引

**与旧版 user 表的核心差异**：
| 对比项 | user（旧） | user_rft（新） |
|--------|-----------|----------------|
| 密码存储 | 明文 | bcrypt 加密 |
| 账号状态 | 无 | 有 status + reason |
| 时间戳 | 无 | created_at / edited_at |
| 创建者追踪 | 无 | created_by |
| 字段非空约束 | 大部分可空 | 核心字段 NOT NULL |
| 角色定义 | 模糊 | 明确 0=教师 1=学生 |

---

### 2.3 teacher_actors（教师账号表）

**文件**：`teacher_actors.sql`
**定位**：教师角色专用表，轻量级，记录教师账号及其状态。

| 字段名 | 类型 | 约束 | 含义 |
|--------|------|------|------|
| `id` | bigint unsigned | 主键，自增 | 记录唯一 ID |
| `uid` | varchar(255) | NOT NULL，唯一 | 教师工号/登录账号 |
| `name` | varchar(100) | NOT NULL | 教师姓名 |
| `status` | tinyint | 默认 0，NOT NULL | 账号状态（0=正常） |
| `created_at` | bigint | NOT NULL | 创建时间（UNIX 时间戳） |

**索引**：`uq_teacher_actors_uid` 唯一索引（uid）

**示例数据**：
- uid=`1001`，name=`张老师`，status=0

**说明**：
- 该表与 `user_rft` 存在功能重叠，可能是不同模块/迭代阶段的产物
- `courses` 表中的 `created_by` 字段引用的就是这里的 `uid`（如 `'1001'`）
- 使用 `bigint unsigned` 主键，与课程/作业等业务表保持一致的 ID 风格

---

## 三、课程体系（4 张表）

### 3.1 courses（课程表）

**文件**：`courses.sql`
**定位**：核心业务表，教师创建的课程，是班级、作业、资源的上层容器。

| 字段名 | 类型 | 约束 | 含义 |
|--------|------|------|------|
| `id` | bigint unsigned | 主键，自增 | 课程唯一 ID |
| `name` | varchar(200) | NOT NULL | 课程名称（如"数据结构"、"计算机组成原理"） |
| `description` | text | 可空 | 课程描述/简介 |
| `teacher_user_id` | int | NOT NULL | 授课教师用户 ID（关联用户表） |
| `status` | tinyint | 默认 0，NOT NULL | 课程状态（0=草稿/未发布，1=已发布，100=已归档/删除） |
| `created_at` | bigint | NOT NULL | 创建时间（UNIX 时间戳） |
| `edited_at` | bigint | NOT NULL | 最后编辑时间 |
| `created_by` | varchar(255) | 可空 | 创建者 uid（对应 teacher_actors.uid，如 '1001'） |
| `legacy_id` | varchar(100) | 可空，唯一 | 旧系统迁移 ID（数据迁移时保留原 ID） |

**索引**：
- `uq_courses_legacy_id`：legacy_id 唯一索引
- `idx_courses_teacher_status`：(teacher_user_id, status) 联合索引

**示例数据**：
| id | name | status | created_by |
|----|------|--------|------------|
| 1 | 数据结构 | 1（已发布） | 1001 |
| 2 | 计算机组成原理 | 0（草稿） | 1001 |
| 3 | 计算机网络 | 0（草稿） | 1001 |
| 4 | 计算机网络 | 100（已归档） | 1001 |

**status 取值推断**：
- `0` = 草稿/未发布
- `1` = 已发布/正常
- `100` = 已归档/软删除

---

### 3.2 course_classes（课程-班级关联表）

**文件**：`course_classes.sql`
**定位**：多对多关联表，一门课程可以面向多个教学班级开课。

| 字段名 | 类型 | 约束 | 含义 |
|--------|------|------|------|
| `id` | bigint unsigned | 主键，自增 | 记录唯一 ID |
| `course_id` | bigint unsigned | NOT NULL，外键 | 关联课程 ID（→ courses.id） |
| `class_id` | int | NOT NULL | 关联教学班级 ID（→ class.id） |
| `created_at` | bigint | NOT NULL | 关联创建时间 |
| `created_by` | varchar(255) | 可空 | 创建者 uid |

**约束**：
- `uq_course_classes`：(course_id, class_id) 联合唯一，防止重复关联
- `fk_course_classes_course`：外键，课程删除时级联删除（on delete cascade）

**索引**：`idx_course_classes_class`（class_id）

**示例数据**：course_id=3（计算机网络）→ class_id=2（计科2403班）

---

### 3.3 course_students（课程-学生关联表）

**文件**：`course_students.sql`
**定位**：多对多关联表，记录学生选修了哪些课程（独立于班级维度的课程选课关系）。

| 字段名 | 类型 | 约束 | 含义 |
|--------|------|------|------|
| `id` | bigint unsigned | 主键，自增 | 记录唯一 ID |
| `course_id` | bigint unsigned | NOT NULL，外键 | 关联课程 ID（→ courses.id） |
| `student_user_id` | int | NOT NULL | 学生用户 ID |
| `status` | tinyint | 默认 0，NOT NULL | 选课状态（0=正常/已选） |
| `created_at` | bigint | NOT NULL | 选课时间 |
| `edited_at` | bigint | NOT NULL | 最后编辑时间 |
| `created_by` | varchar(255) | 可空 | 操作人 uid（通常是教师批量导入） |

**约束**：
- `uq_course_students`：(course_id, student_user_id) 联合唯一，防止重复选课
- `fk_course_students_course`：外键，课程删除时级联删除

**索引**：`idx_course_students_student_status`（student_user_id, status）

**示例数据**：course_id=3 → student_user_id=4

**与 class_record 的区别**：
- `course_students`：学生 ↔ 课程的直接选课关系
- `class_record`：学生 ↔ 教学班级的成员关系
- 学生可以通过加入班级间接获得课程访问权，也可以被直接添加到课程

---

### 3.4 course_resources（课程资源表）

**文件**：`course_resources.sql`
**定位**：课程配套资源文件管理（课件、文档、视频等），支持权限控制和元数据。

| 字段名 | 类型 | 约束 | 含义 |
|--------|------|------|------|
| `id` | bigint unsigned | 主键，自增 | 资源唯一 ID |
| `course_id` | bigint unsigned | 可空 | 所属课程 ID（可空，支持全局资源） |
| `name` | varchar(255) | NOT NULL | 资源名称/文件名 |
| `type` | varchar(50) | NOT NULL | 资源类型（如 pdf、docx、video、link 等） |
| `file_path` | varchar(500) | NOT NULL | 文件存储路径/URL |
| `file_size` | bigint unsigned | 默认 0，NOT NULL | 文件大小（字节） |
| `permission` | varchar(50) | 默认 'teacher_only'，NOT NULL | 访问权限（teacher_only=仅教师，student=学生可见，public=公开） |
| `metadata_json` | longtext (utf8mb4_bin) | 可空，JSON 校验 | 元数据（JSON 格式，如页数、时长、标签等） |
| `source_resource_id` | bigint unsigned | 可空 | 源资源 ID（用于资源复制/派生关系追踪） |
| `status` | tinyint | 默认 0，NOT NULL | 资源状态（0=正常） |
| `created_at` | bigint | NOT NULL | 上传时间 |
| `edited_at` | bigint | NOT NULL | 最后编辑时间 |
| `created_by` | varchar(255) | 可空 | 上传者 uid |
| `legacy_id` | varchar(100) | 可空，唯一 | 旧系统迁移 ID |

**约束**：
- `uq_resources_legacy_id`：legacy_id 唯一
- `metadata_json` 有 `json_valid()` 检查约束，确保是合法 JSON

**索引**：`idx_resources_course_status`（course_id, status）

**设计亮点**：
- `permission` 字段实现资源可见性分级（仅教师 / 学生可见 / 公开）
- `metadata_json` 用 JSON 字段存储扩展属性，避免频繁加列
- `source_resource_id` 支持资源派生关系（如从教师资源复制一份给学生）

---

## 四、班级体系（5 张表）

### 4.1 class（教学班级表）

**文件**：`class.sql`
**定位**：教学班级管理，是课程下的行政/教学分组，作业和任务都挂在班级上。

| 字段名 | 类型 | 约束 | 含义 |
|--------|------|------|------|
| `id` | int | 主键，自增 | 班级唯一 ID |
| `status` | int | NOT NULL | 班级状态（0=正常） |
| `name` | varchar(255) | NOT NULL | 班级名称（如"计科2403"、"计科2401"） |
| `course` | varchar(255) | 可空 | 关联课程名（同一课程可下设多个班级） |
| `private` | tinyint(1) | NOT NULL | 是否私有（0=公开，1=私有） |
| `created_at` | int | NOT NULL | 创建时间（UNIX 时间戳） |
| `created_by` | varchar(255) | 可空 | 创建者 uid |
| `edited_at` | int | NOT NULL | 最后编辑时间 |

**约束**：`class_course_name_status_uindex`（course, name, status）联合唯一

**索引**：course、created_by、name、private、status 均有单列索引

**示例数据**：
| id | name | course | created_by |
|----|------|--------|------------|
| 2 | 计科2403 | 新建班级 | 9999999999 |
| 3 | 计科2401 | 计算机科学与技术 2024 级 1 班 | 1001 |

**注意**：
- `course` 字段存的是**课程名称字符串**，不是课程 ID，存在数据冗余和一致性风险
- 与 `course_classes` 表配合使用，后者才是课程与班级的规范化关联

---

### 4.2 class_record（班级成员记录表）

**文件**：`class_record.sql`
**定位**：记录哪些用户（学生/教师）属于哪个教学班级，是班级的成员关系表。

| 字段名 | 类型 | 约束 | 含义 |
|--------|------|------|------|
| `id` | int | 主键，自增 | 记录唯一 ID |
| `uid` | int | NOT NULL | 学生学号/用户 ID |
| `status` | int | NOT NULL | 记录状态（0=正常） |
| `role` | int | NOT NULL | 在班级中的角色（0=教师，1=学生） |
| `class_id` | int | NOT NULL | 所属教学班级 ID（→ class.id） |
| `created_at` | int | NOT NULL | 加入班级时间（UNIX 时间戳） |
| `edited_at` | int | NOT NULL | 最后编辑时间 |
| `created_by` | varchar(255) | NOT NULL | 操作人（谁把这个学生加进班级的） |

**约束**：`class_record_uid_class_id_uindex`（uid, class_id）联合唯一，防止同一用户重复加入同一班级

**索引**：class_id、created_by、role、status、uid 均有单列索引

**示例数据**：uid=2025060144（韦开腾）→ class_id=2（计科2403班），role=1（学生）

**说明**：
- `uid` 直接用学号作为用户标识（如 2025060144），与 `user_rft.uid` 对应
- `role` 字段区分班级内教师和学生，支持助教等角色扩展

---

### 4.3 class_notices（班级公告表）

**文件**：`class_notices.sql`
**定位**：教师在班级内发布的公告/通知。

| 字段名 | 类型 | 约束 | 含义 |
|--------|------|------|------|
| `id` | bigint unsigned | 主键，自增 | 公告唯一 ID |
| `class_id` | int | NOT NULL | 所属班级 ID（→ class.id） |
| `notice_type` | varchar(50) | NOT NULL | 公告类型（如 general=普通通知，important=重要通知，emergency=紧急通知） |
| `content` | text | NOT NULL | 公告正文内容 |
| `status` | tinyint | 默认 0，NOT NULL | 公告状态（0=正常/已发布） |
| `created_at` | bigint | NOT NULL | 发布时间 |
| `edited_at` | bigint | NOT NULL | 最后编辑时间 |
| `created_by` | varchar(255) | 可空 | 发布者 uid |
| `legacy_id` | varchar(100) | 可空，唯一 | 旧系统迁移 ID |

**索引**：`idx_notices_class_status`（class_id, status）

---

### 4.4 class_tasks（班级任务表）

**文件**：`class_tasks.sql`
**定位**：教师在班级内发布的学习任务/练习，与 assignments（作业）并列的另一种任务形式。

| 字段名 | 类型 | 约束 | 含义 |
|--------|------|------|------|
| `id` | bigint unsigned | 主键，自增 | 任务唯一 ID |
| `class_id` | int | NOT NULL | 所属班级 ID（→ class.id） |
| `task_type` | varchar(50) | NOT NULL | 任务类型（如 reading=阅读，practice=练习，project=项目，lab=实验） |
| `content` | text | NOT NULL | 任务内容/要求描述 |
| `deadline` | datetime | 可空 | 截止时间 |
| `status` | tinyint | 默认 0，NOT NULL | 任务状态（0=已发布/进行中） |
| `created_at` | bigint | NOT NULL | 发布时间 |
| `edited_at` | bigint | NOT NULL | 最后编辑时间 |
| `created_by` | varchar(255) | 可空 | 发布者 uid |
| `legacy_id` | varchar(100) | 可空，唯一 | 旧系统迁移 ID |

**索引**：`idx_tasks_class_status`（class_id, status）

**与 assignments 的区别**：
| 对比项 | assignments（作业） | class_tasks（班级任务） |
|--------|---------------------|------------------------|
| 关联维度 | 课程 + 班级 | 仅班级 |
| 附件支持 | 有 attachment_url | 无 |
| 提交方式 | assignment_submissions（含内容+附件+分数+反馈） | class_task_completions（仅标记完成） |
| 批阅打分 | 支持 score + feedback | 不支持，仅完成/未完成 |
| 适用场景 | 正式作业、需要评分 | 日常练习、阅读任务、打卡 |

---

### 4.5 class_task_completions（班级任务完成记录表）

**文件**：`class_task_completions.sql`
**定位**：记录学生完成班级任务的情况，轻量级打卡表。

| 字段名 | 类型 | 约束 | 含义 |
|--------|------|------|------|
| `id` | bigint unsigned | 主键，自增 | 记录唯一 ID |
| `task_id` | bigint unsigned | NOT NULL | 关联任务 ID（→ class_tasks.id） |
| `student_user_id` | int | NOT NULL | 学生用户 ID |
| `completed_at` | datetime | 默认当前时间，NOT NULL | 完成时间 |
| `status` | tinyint | 默认 0，NOT NULL | 完成状态（0=已完成） |

**约束**：`uq_task_student`（task_id, student_user_id）联合唯一，每个学生对每个任务只能有一条完成记录

**索引**：`idx_completions_student_status`（student_user_id, status）

**特点**：
- 极简设计，只记录"谁在什么时候完成了哪个任务"
- 无分数、无反馈、无附件，适合不需要评分的日常任务
- 与 `assignment_submissions` 形成互补（正式作业 vs 轻量任务）

---

## 五、作业体系（2 张表）

### 5.1 assignments（作业表）

**文件**：`assignments.sql`
**定位**：核心业务表，教师发布的正式作业，支持附件、截止时间、统计人数。

| 字段名 | 类型 | 约束 | 含义 |
|--------|------|------|------|
| `id` | bigint unsigned | 主键，自增 | 作业唯一 ID |
| `course_id` | bigint unsigned | 可空，外键 | 所属课程 ID（→ courses.id，可空表示不绑定课程） |
| `class_id` | int | NOT NULL | 所属班级 ID（→ class.id） |
| `publisher_user_id` | int | NOT NULL | 发布者用户 ID（教师） |
| `title` | varchar(200) | NOT NULL | 作业标题（如"第一次作业"） |
| `content` | text | NOT NULL | 作业要求/内容描述 |
| `deadline` | datetime | 可空 | 截止时间 |
| `attachment_url` | varchar(500) | 可空 | 附件文件路径（作业模板/题目文件） |
| `status` | tinyint | 默认 0，NOT NULL | 作业状态（0=已发布/进行中） |
| `created_at` | bigint | NOT NULL | 发布时间 |
| `edited_at` | bigint | NOT NULL | 最后编辑时间 |
| `created_by` | varchar(255) | 可空 | 创建者 uid |
| `legacy_id` | varchar(100) | 可空，唯一 | 旧系统迁移 ID |
| `attachment_name` | varchar(255) | 可空 | 附件原始文件名 |
| `attachment_size` | int unsigned | 可空 | 附件大小（字节） |
| `total_students` | int unsigned | 默认 0，NOT NULL | 应提交学生总数（发布时统计，用于进度计算） |

**约束**：
- `uq_assignments_legacy_id`：legacy_id 唯一
- `fk_assignments_course`：外键，课程删除时置空（on delete set null）

**索引**：
- `idx_assignments_class_status`（class_id, status）
- `idx_assignments_course_status`（course_id, status）
- `idx_assignments_deadline`（deadline）

**示例数据**：
- title=`第一次作业`，content=`及时完成`，class_id=2，deadline=2026-07-31，total_students=2

**设计说明**：
- `course_id` 可空：作业可以只挂在班级上，不强制关联课程
- `total_students` 冗余存储应提交人数，避免每次统计都关联查询
- 附件三字段（url/name/size）完整记录附件信息

---

### 5.2 assignment_submissions（作业提交表）

**文件**：`assignment_submissions.sql`
**定位**：核心业务表，学生提交作业的记录，包含内容、附件、分数、教师反馈，是师生互动的核心载体。

| 字段名 | 类型 | 约束 | 含义 |
|--------|------|------|------|
| `id` | bigint unsigned | 主键，自增 | 提交记录唯一 ID |
| `assignment_id` | bigint unsigned | NOT NULL，外键 | 关联作业 ID（→ assignments.id） |
| `student_user_id` | int | NOT NULL | 提交学生用户 ID |
| `content` | text | 可空 | 提交的文字内容/答案 |
| `attachment_url` | varchar(500) | 可空 | 提交的附件文件路径（学生上传的作业文件） |
| `submitted_at` | datetime | 默认当前时间，NOT NULL | 提交时间 |
| `status` | tinyint | 默认 0，NOT NULL | 提交状态（0=已提交待批阅，1=已批阅，其他待定义） |
| `score` | decimal(5,2) | 可空 | 教师评分（最大 999.99，支持两位小数） |
| `feedback` | text | 可空 | 教师批阅反馈/评语 |
| `created_at` | bigint | NOT NULL | 记录创建时间 |
| `edited_at` | bigint | NOT NULL | 最后编辑时间（教师批阅时更新） |
| `created_by` | varchar(255) | 可空 | 创建者（通常是学生自己） |

**约束**：
- `uq_assignment_student`：(assignment_id, student_user_id) 联合唯一，**每个学生对每个作业只能提交一次**
- `fk_submissions_assignment`：外键，作业删除时级联删除提交记录

**索引**：`idx_submissions_student_status`（student_user_id, status）

**业务流转**：
```
学生提交 → status=0（待批阅）→ 教师批阅 → status=1（已批阅）
                                    ↓
                              填写 score + feedback
                                    ↓
                              学生查看分数和反馈
```

**设计要点**：
- 联合唯一约束保证一人一次提交，不支持多次提交覆盖（如需重做需教师删除记录）
- `score` 用 decimal(5,2)，支持百分制精确到 0.01
- `feedback` 文本字段支持教师写详细评语
- 作业删除时级联删除所有提交，数据一致性有保障

---

## 六、消息体系（1 张表）

### 6.1 personal_messages（个人消息表）

**文件**：`personal_messages.sql`
**定位**：系统内个人消息/通知中心，教师发布作业/公告时自动推送给学生，支持已读状态和附件。

| 字段名 | 类型 | 约束 | 含义 |
|--------|------|------|------|
| `id` | bigint unsigned | 主键，自增 | 消息唯一 ID |
| `title` | varchar(200) | NOT NULL | 消息标题（如"第一次作业"） |
| `content` | text | NOT NULL | 消息正文（如"及时完成"） |
| `sender_id` | int | NOT NULL | 发送者用户 ID |
| `sender_name` | varchar(100) | NOT NULL | 发送者姓名（冗余存储，避免关联查询） |
| `receiver_id` | int | NOT NULL | 接收者用户 ID |
| `message_type` | enum('assignment','notice','system') | NOT NULL | 消息类型（assignment=作业通知，notice=公告通知，system=系统通知） |
| `status` | enum('unread','read','deleted') | 默认 'unread'，NOT NULL | 消息状态（unread=未读，read=已读，deleted=已删除） |
| `created_at` | timestamp | 默认当前时间，NOT NULL | 消息创建时间 |
| `read_at` | timestamp | 可空 | 阅读时间（未读时为 NULL） |
| `deadline` | timestamp | 可空 | 关联的截止时间（作业通知时同步作业 deadline） |
| `attachment_url` | varchar(500) | 可空 | 附件文件路径 |
| `attachment_name` | varchar(255) | 可空 | 附件文件名 |
| `attachment_size` | int unsigned | 可空 | 附件大小（字节） |
| `assignment_id` | bigint unsigned | 可空 | 关联作业 ID（→ assignments.id，作业通知时填充） |

**索引**：
- `idx_messages_assignment`（assignment_id）
- `idx_messages_created`（created_at）
- `idx_messages_deadline`（deadline）
- `idx_messages_receiver_status`（receiver_id, status）

**示例数据**：
- 张老师（sender_id=1001）→ 学生 2025060144，类型 assignment，标题"第一次作业"，附件"认识实习报告模板-2024级.docx"，关联 assignment_id=1

**设计说明**：
- 每条消息是**单收件人**模式：教师发布一个作业给 N 个学生，会生成 N 条消息记录（每个学生一条）
- `sender_name` 冗余存储，消息列表展示时无需关联用户表
- `message_type` 用 enum 严格限制类型，便于前端图标区分
- `status` 用 enum 管理消息生命周期（未读→已读→删除）
- `assignment_id` 可空，非作业类消息不关联

---

## 七、知识图谱（1 张表）

### 7.1 knowledge_graphs（知识图表）

**文件**：`knowledge_graphs.sql`
**定位**：课程知识图谱数据存储，每门课程对应一份图谱，以 JSON 格式存储图结构数据。

| 字段名 | 类型 | 约束 | 含义 |
|--------|------|------|------|
| `id` | bigint unsigned | 主键，自增 | 记录唯一 ID |
| `course_id` | bigint unsigned | NOT NULL | 所属课程 ID（→ courses.id） |
| `graph_data` | longtext (utf8mb4_bin) | NOT NULL，JSON 校验 | 知识图谱数据（JSON 格式，包含节点和边） |
| `created_at` | bigint | NOT NULL | 创建时间 |
| `edited_at` | bigint | NOT NULL | 最后编辑时间 |
| `created_by` | varchar(255) | 可空 | 创建者 uid |

**约束**：
- `uq_knowledge_graph_course`：course_id 唯一，**每门课程只能有一份知识图谱**
- `graph_data` 有 `json_valid()` 检查约束

**graph_data JSON 结构推测**：
```json
{
  "nodes": [
    {"id": "1", "label": "线性表", "chapter": "第2章"},
    {"id": "2", "label": "链表", "chapter": "第2章"}
  ],
  "edges": [
    {"source": "1", "target": "2", "relation": "包含"}
  ]
}
```

**设计说明**：
- 一门课程一份图谱，通过 course_id 唯一约束保证
- 图谱结构灵活变化，用 JSON 存储避免频繁修改表结构
- `utf8mb4_bin` 排序规则支持存储特殊字符和 emoji
- 属于平台的高级/特色功能，与作业体系解耦

---

## 八、表间关系与业务流转

### 8.1 实体关系图（ER 概览）

```
teacher_actors ──created_by──> courses
                                     │
                          ┌──────────┼──────────┐
                          ▼          ▼          ▼
                   course_classes  course_students  course_resources
                          │
                          ▼
                        class ──┬──> class_record（成员）
                                ├──> class_notices（公告）
                                ├──> class_tasks ──> class_task_completions
                                └──> assignments ──> assignment_submissions
                                                          │
                                                          ▼
                                                  personal_messages（通知）

courses ──1:1──> knowledge_graphs
```

### 8.2 核心业务流程

**流程一：教师创建课程并发布作业**

```
1. 教师账号（teacher_actors）登录
2. 创建课程（courses），status=1 发布
3. 创建/关联教学班级（class + course_classes）
4. 学生加入班级（class_record）或直接选课（course_students）
5. 教师发布作业（assignments），绑定 class_id
6. 系统自动为每个学生生成消息通知（personal_messages，type=assignment）
```

**流程二：学生完成并提交作业**

```
1. 学生收到消息通知（personal_messages，status=unread）
2. 学生查看作业要求（assignments）和附件
3. 学生完成作业，上传附件，提交（assignment_submissions）
   - 写入 content + attachment_url
   - status=0（待批阅）
4. 提交记录通过 (assignment_id, student_user_id) 唯一约束保证一人一次
```

**流程三：教师批阅并反馈**

```
1. 教师查看作业提交列表（assignment_submissions where assignment_id=X）
2. 教师批阅：填写 score（分数）+ feedback（评语）
3. 更新 status=1（已批阅），edited_at 更新
4. 学生查看自己的分数和反馈
5. 作业进度统计：已提交人数 / total_students
```

**流程四：班级日常任务（轻量级）**

```
1. 教师发布班级任务（class_tasks），如阅读任务
2. 学生完成后标记完成（class_task_completions）
3. 无需评分，仅记录完成时间
4. 教师查看完成情况统计
```

### 8.3 外键关系汇总

| 子表 | 外键字段 | 父表 | 父表字段 | 删除策略 |
|------|---------|------|---------|---------|
| course_classes | course_id | courses | id | CASCADE（级联删除） |
| course_students | course_id | courses | id | CASCADE（级联删除） |
| assignments | course_id | courses | id | SET NULL（置空） |
| assignment_submissions | assignment_id | assignments | id | CASCADE（级联删除） |

> 注意：其他表间关联（如 class_id、student_user_id）未建立物理外键，仅靠业务逻辑维护引用完整性。

---

## 九、设计特点与注意事项

### 9.1 设计亮点

1. **新旧两套用户体系并存**：`user`（旧）+ `user_rft`（新），体现了项目迭代重构过程
2. **作业与任务双轨制**：`assignments`（正式作业，支持评分反馈）+ `class_tasks`（轻量任务，仅打卡），满足不同教学场景
3. **消息通知独立**：`personal_messages` 单独建表，支持已读状态、附件、截止时间提醒
4. **知识图谱特色功能**：`knowledge_graphs` 用 JSON 存储课程知识结构，是平台的差异化功能
5. **legacy_id 迁移支持**：多张表都有 `legacy_id` 字段，支持从旧系统平滑迁移数据
6. **资源权限分级**：`course_resources.permission` 实现教师-only / 学生可见 / 公开三级权限
7. **软删除/状态管理**：通过 `status` 字段管理数据生命周期，避免物理删除（courses.status=100 表示归档）

### 9.2 存在的问题与风险

1. **密码安全**：`user` 表密码明文存储，`user_rft` 已改为 bcrypt，但旧表数据仍有风险
2. **用户 ID 类型不统一**：有的表用 int（user.uid），有的用 varchar（user_rft.uid、teacher_actors.uid），关联时需类型转换
3. **class.course 字段冗余**：存课程名而非课程 ID，与 `course_classes` 关联表功能重叠，可能导致数据不一致
4. **外键不完整**：class_id、student_user_id 等关键字段未建立物理外键，依赖业务层保证引用完整性
5. **时间戳格式不统一**：有的用 bigint UNIX 时间戳（created_at），有的用 datetime/timestamp（deadline、submitted_at）
6. **user 表字段全部可空**：数据完整性约束弱，可能出现大量空值记录
7. **作业不支持多次提交**：`assignment_submissions` 联合唯一约束限制一人一次，学生无法覆盖提交，需要教师手动删除
8. **消息表单收件人模式**：群发消息会产生大量重复记录（N 个学生 = N 条消息），数据冗余较高

### 9.3 命名规范观察

- **表名**：统一小写，下划线分隔，部分用复数（courses、assignments），部分用单数（class、user）
- **主键**：统一 `id`，自增
- **时间字段**：`created_at` / `edited_at`（注意不是 `updated_at`）
- **操作人**：`created_by`（varchar 类型，存 uid 而非 id）
- **状态字段**：统一 `status`（tinyint/int，0 通常表示正常/默认）
- **迁移 ID**：`legacy_id`（varchar，唯一索引）
- **索引命名**：`idx_表名_字段名`（联合索引用字段名拼接）
- **唯一约束命名**：`uq_表名_字段名`

---

> **文档生成时间**：2026-08-31
> **数据来源**：D:\buct_cip 目录下 16 个 SQL 建表文件
> **覆盖范围**：全部 16 张表的字段、约束、索引、业务含义及表间关系
