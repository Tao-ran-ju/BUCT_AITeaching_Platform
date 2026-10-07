# BUCT AI 教学平台
面向大学算法竞赛指导教师的 **AI 教学管理平台**（北化 AI 教师管理端），采用前后端完全分离的单体分层架构。

## 技术栈
| 层 | 技术 |
|---|---|
| 前端 | Vue 3（组合式API / `<script setup>`）+ Vite + Vue Router + Pinia + ECharts |
| 后端 | Python 3.10+ · FastAPI · Uvicorn |
| 数据库 | MySQL 8.0 · SQLAlchemy 2.0 (ORM) · Alembic |
| 缓存 | Redis（可选） |
| AI 能力 | 大模型 API 统一封装（通义千问 / DeepSeek 等，OpenAI 兼容接口） |
| 文件存储 | 本地磁盘（初期）→ OSS（后期） |

## 功能模块
1. **课程与资源管理**：班级学生管理（建班、批量导入、队伍关联）、课程生命周期、多格式教学资源上传与权限、章-节-知识点三级树状组织
2. **AI 教研与备课中心**：AI 教案生成、智能题库生成、实践项目设计助手
3. **教学过程与竞赛管理**：通知与任务发布、进度可视化、主题讨论区、学习社群、学情预警（规则引擎 + AI 干预建议）
4. **AI 助教与智能评测**：编程题自动判题（对接学校 OJ）、代码质量分析、AI 个性化评语、代码查重（后续阶段）
5. **数据驾驶舱与教学优化**：核心指标看板、能力矩阵热力图、教学效果对比、AI 教学反思
6. **系统基础管理**：用户与权限、系统配置、操作日志

## 目录结构
```
BUCT_AITeaching_Platform/
├── frontend/                 # 前端（Vue 3 + Vite）
│   ├── index.html            # 应用入口 HTML
│   ├── package.json          # 依赖管理与脚本配置
│   ├── vite.config.js        # Vite 构建配置
│   ├── public/               # 静态资源（不参与构建，直接输出）
│   │   └── favicon.ico
│   └── src/
│       ├── main.js           # 应用入口文件
│       ├── App.vue           # 根组件
│       ├── router/           # Vue Router 路由配置
│       ├── store/            # Pinia 全局状态管理
│       ├── views/            # 页面级组件（课程资源/班级管理/备课中心等）
│       ├── components/       # 公共可复用业务组件
│       ├── api/              # 后端接口请求统一封装
│       ├── utils/            # 通用工具函数
│       ├── assets/           # 静态资源（图片、图标字体等）
│       └── styles/           # 全局样式、CSS 变量与主题
├── backend/                  # 后端（FastAPI）
│   ├── main.py               # 应用入口
│   ├── requirements.txt      # 依赖清单
│   ├── alembic.ini           # 数据库迁移配置
│   ├── alembic/              # Alembic 迁移脚本目录
│   ├── .env.example          # 环境变量模板（.env 不入库）
│   ├── scripts/              # 运维脚本（初始化库、OJ 探查）
│   └── app/
│       ├── config.py         # 全局配置（读 .env）
│       ├── database.py       # 数据库连接
│       ├── dependencies.py   # 全局依赖（JWT 鉴权等）
│       ├── exceptions.py     # 业务异常
│       ├── middleware.py     # 访问日志中间件
│       ├── models/           # ORM 数据模型（user/class/course/...）
│       ├── schemas/          # Pydantic 校验模型
│       ├── services/         # 业务服务层
│       ├── routers/          # 路由层（auth/course/resource/...）
│       ├── clients/          # 第三方客户端（大模型/OJ/存储）
│       └── utils/            # 工具（加密/日志/分页/文件）
└── docs/
    ├── api.md                # 接口文档
    └── database/init.sql     # 数据库初始化脚本
```

## 快速开始
### 1. 准备数据库
- 本机安装 MySQL 8.0，或使用远程 MySQL。
- 在 MySQL 中执行 `docs/database/init.sql` 创建库表（或运行 `python scripts/init_db.py` 由 ORM 自动建表）。

### 2. 配置后端环境变量
```bash
cd backend
copy .env.example .env        # Windows
# 编辑 .env，填写 DB_*、SECRET_KEY、OJ_DB_*、LLM_API_KEY 等
```

### 3. 安装依赖并启动后端
```bash
cd backend
pip install -r requirements.txt          # 国内可加 -i https://pypi.tuna.tsinghua.edu.cn/simple
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
- 后端接口文档（Swagger）：http://127.0.0.1:8000/docs
- 统一响应格式：`{ "code": 0, "message": "success", "data": ... }`

### 4. 启动前端开发服务
```bash
cd frontend
npm install          # 安装依赖（国内可加 --registry https://registry.npmmirror.com）
npm run dev          # 启动本地开发服务器
```
- 前端访问地址：http://127.0.0.1:5173
- 生产环境构建：执行 `npm run build`，产物输出至 `frontend/dist/`，可由 Nginx 等静态服务托管

## 数据库迁移（Alembic）
```bash
cd backend
alembic revision --autogenerate -m "init"   # 生成迁移脚本
alembic upgrade head                        # 应用迁移
```

## 统一约定
- 接口统一响应 `{code, message, data}`；业务异常由全局处理器统一转换
- 环境变量一律写 `.env`，经 `config.py` 读取，不硬编码
- 命名：Python/数据库 `snake_case`，前端 JS `camelCase`，Vue 组件文件 `PascalCase`，普通文件/URL `kebab-case`
- Git 提交信息格式：`feat:` / `fix:` / `docs:` 等

## 安全提醒
`backend/.env` 与 `backend/scripts/legacy/` 含敏感凭据（OJ 数据库密码等），已被 `.gitignore` 排除，**严禁提交 git**。
