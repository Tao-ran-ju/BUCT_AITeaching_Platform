# 后端接口文档（FastAPI）

- 基础前缀：`/api/v1`
- 统一响应格式：成功 `{ "code": 0, "message": "success", "data": ... }`，失败 `{ "code": <HTTP状态码>, "message": "错误说明", "data": null }`
- 鉴权方式：`Authorization: Bearer <access_token>`（登录后获取）
- 交互式文档（Swagger）：启动后访问 `http://127.0.0.1:8000/docs`

## 认证 /auth

| 方法 | 路径 | 说明 | 鉴权 |
|---|---|---|---|
| POST | `/auth/login` | 登录，返回 access_token + 用户信息 | 否 |
| POST | `/auth/register` | 创建用户（教师/学生/管理员） | 管理员 |

## 用户 /users

| 方法 | 路径 | 说明 | 鉴权 |
|---|---|---|---|
| GET | `/users/me` | 获取当前用户信息 | 是 |
| PUT | `/users/me` | 更新个人资料 | 是 |
| POST | `/users/me/password` | 修改密码 | 是 |
| GET | `/users` | 用户列表（role/keyword 过滤） | 管理员 |

## 课程 /courses

| 方法 | 路径 | 说明 | 鉴权 |
|---|---|---|---|
| GET | `/courses` | 课程列表（分页） | 是 |
| POST | `/courses` | 创建课程 | 是 |
| GET | `/courses/{id}` | 课程详情 | 是 |
| PUT | `/courses/{id}` | 更新课程 | 是 |
| DELETE | `/courses/{id}` | 删除课程 | 是 |
| GET | `/courses/{id}/chapters` | 章节列表 | 是 |
| POST | `/courses/{id}/chapters` | 创建章节 | 是 |
| GET | `/courses/chapters/{id}/knowledge-points` | 知识点列表 | 是 |
| POST | `/courses/chapters/{id}/knowledge-points` | 创建知识点 | 是 |

## 班级 /classes

| 方法 | 路径 | 说明 | 鉴权 |
|---|---|---|---|
| GET | `/classes` | 班级列表（分页） | 是 |
| POST | `/classes` | 创建班级 | 是 |
| PUT | `/classes/{id}` | 更新班级 | 是 |
| DELETE | `/classes/{id}` | 删除班级 | 是 |
| POST | `/classes/{id}/students` | 批量添加学生 | 是 |
| GET | `/classes/{id}/students` | 班级学生列表 | 是 |
| DELETE | `/classes/{id}/students/{sid}` | 移除学生 | 是 |

## 教学资源 /resources

| 方法 | 路径 | 说明 | 鉴权 |
|---|---|---|---|
| POST | `/resources` | 上传资源（multipart：title/file/course_id） | 是 |
| GET | `/resources` | 资源列表（course_id 过滤） | 是 |
| PATCH | `/resources/{id}/visibility` | 设置可见性 public/course/private | 是 |
| DELETE | `/resources/{id}` | 删除资源 | 是 |

## 作业 /assignments

| 方法 | 路径 | 说明 | 鉴权 |
|---|---|---|---|
| POST | `/assignments` | 发布作业 | 是 |
| GET | `/assignments?course_id=` | 按课程查作业 | 是 |
| POST | `/assignments/submit` | 学生提交作业 | 是 |
| POST | `/assignments/{id}/judge` | 触发评测（OJ + AI 评语） | 是 |
| GET | `/assignments/{id}/submissions` | 提交记录 | 是 |

## AI 备课中心 /teaching

| 方法 | 路径 | 说明 | 鉴权 |
|---|---|---|---|
| POST | `/teaching/plan` | AI 生成教案（knowledge_point） | 是 |
| POST | `/teaching/quiz` | AI 生成题库（知识点/数量/难度） | 是 |
| POST | `/teaching/summarize` | AI 资源摘要 | 是 |

> 未配置 `LLM_API_KEY` 时这些接口返回 422 提示，不影响其他功能。

## 教学过程 /discussions

| 方法 | 路径 | 说明 | 鉴权 |
|---|---|---|---|
| GET | `/discussions?course_id=` | 帖子列表 | 是 |
| POST | `/discussions` | 发布帖子 | 是 |
| GET | `/discussions/{id}/replies` | 回复列表 | 是 |
| POST | `/discussions/{id}/replies` | 回复帖子 | 是 |

## 学情预警 /warnings

| 方法 | 路径 | 说明 | 鉴权 |
|---|---|---|---|
| POST | `/warnings/scan` | 触发规则引擎扫描 | 是 |
| GET | `/warnings` | 预警列表（risk_level 过滤） | 是 |
| POST | `/warnings/{id}/suggestion` | AI 生成干预建议 | 是 |
| POST | `/warnings/{id}/resolve` | 标记预警已处理 | 是 |

## 数据驾驶舱 /dashboard

| 方法 | 路径 | 说明 | 鉴权 |
|---|---|---|---|
| GET | `/dashboard/overview` | 核心指标总览 | 是 |
| GET | `/dashboard/heatmap` | 能力矩阵热力图 | 是 |
