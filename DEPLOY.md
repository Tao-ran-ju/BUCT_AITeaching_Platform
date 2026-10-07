# 部署指南（DEPLOY）

> 面向轻量级服务器（如阿里云 ECS / 腾讯云轻量应用服务器）的部署说明。
> 已部署示例：`http://101.42.1.248/`。本文同时覆盖「全新部署」与「已部署服务器升级到最新代码」。

## 架构总览

```
浏览器
   │  http://<服务器 IP>/
   ▼
nginx（80 端口）
   ├── /            → 前端静态文件（frontend/dist 目录，Vite 构建产物）
   ├── /api/        → 反向代理到 uvicorn（127.0.0.1:8000）
   └── /uploads/    → 反向代理到 uvicorn（后端挂载的 StaticFiles）
                          │
                          ▼
                 uvicorn（FastAPI，127.0.0.1:8000）
                          ├── 远程 MariaDB（学校 buct_cip 库）
                          ├── 本地磁盘 uploads/（工作副本）
                          └── 阿里云 OSS（可选，镜像 + 文档在线预览）
```

前端 API 层（`frontend/src/api/index.js`）使用**相对路径** `/api/v1`（同源部署），因此**必须**通过 nginx 同源反代，前端和后端要在同一个域名/IP 下。

---

## 一、环境准备

| 依赖 | 说明 |
|---|---|
| Python 3.10+ | 后端运行环境 |
| 远程 MariaDB（学校 buct_cip 库） | 业务数据库（无需本地安装，走网络连接） |
| ffmpeg / ffprobe | 视频转码、关键帧抽取（缺失不影响其它功能，仅视频后处理降级） |
| nginx | 反向代理 + 静态资源托管 |
| Node.js 18+ / npm | 前端构建（Vue3 + Vite） |
| git | 拉取代码 |

CentOS / TencentOS：

```bash
sudo yum install -y git nginx python3 python3-pip
# ffmpeg（EPEL 源）
sudo yum install -y epel-release && sudo yum install -y ffmpeg
```

Ubuntu / Debian：

```bash
sudo apt update && sudo apt install -y git nginx python3 python3-pip ffmpeg
```

Node.js 18+（前端构建用，推荐 nvm 或 NodeSource）：

```bash
# Ubuntu / Debian
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - && sudo apt install -y nodejs
# CentOS / TencentOS
curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash - && sudo yum install -y nodejs
```

数据库使用学校已部署的远程 MariaDB（`buct_cip` 库），无需在服务器上安装 MySQL；只需保证服务器能连通数据库地址（见 3.1 的 `DB_HOST` / `DB_PORT`）。

---

## 二、拉取代码

```bash
sudo mkdir -p /opt/buct-ai-teaching
sudo chown -R $USER:$USER /opt/buct-ai-teaching
cd /opt/buct-ai-teaching
git clone <你的仓库地址> .
```

目录结构（部署后）：

```
/opt/buct-ai-teaching/
├── frontend/          # 前端源码（Vue3 + Vite；构建产物在 frontend/dist）
│   ├── src/           # Vue 组件与逻辑（views / api / components 等）
│   ├── public/        # 静态资源（favicon、images）
│   ├── package.json   # 前端依赖与构建脚本
│   └── dist/          # npm run build 产物（nginx 的 root）
└── backend/           # 后端（uvicorn 的 WorkingDirectory）
    ├── main.py
    ├── requirements.txt
    ├── .env           # 环境变量（不入 git）
    ├── uploads/       # 上传文件（工作副本，可整体备份）
    └── scripts/       # create_teacher_tables.py / seed_admin.py / seed_study_behavior.py
```

### 2.1 构建前端（首次部署 / 前端代码有更新时执行）

前端已重构为 Vue 3 + Element Plus 单页应用（Vite 构建），部署前需构建一次：

```bash
cd /opt/buct-ai-teaching/frontend
npm install          # 安装依赖（生成 node_modules/，已被 .gitignore 忽略）
npm run build        # 产出 dist/（nginx 的 root）
```

> 本地开发用 `npm run dev`（内置 dev server，`/api`、`/uploads` 已代理到 `127.0.0.1:8000`）。

---

## 三、后端配置与数据库

### 3.1 配置 `.env`

```bash
cd /opt/buct-ai-teaching/backend
cp .env.example .env
vim .env
```

必填项：

| 变量 | 说明 |
|---|---|
| `DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` / `DB_NAME` | 远程 MariaDB（学校 buct_cip 库）连接，`DB_NAME=buct_cip` |
| `SECRET_KEY` | JWT 密钥，**务必改成随机长字符串** |
| `SSO_SHARED_SECRET` | 学生端 SSO 换 token 的共享密钥（学生端对接必需） |
| `LLM_API_KEY` / `LLM_API_BASE` / `LLM_MODEL` | 大模型 API |
| `OJ_API_BASE` / `OJ_USERNAME` / `OJ_PASSWORD` | 学校 OJ 对接 |
| `OJ_DB_*` | 学校 OJ 只读库（可选） |
| `OSS_*` | 阿里云 OSS（可选，见第六节） |

### 3.2 初始化数据库

后端**直接映射学校已有的 `buct_cip` 库**（16 张表，MariaDB 10.11.13），这 16 张表**保持不变、不做任何改动**；
教师端额外需要持久化的功能（OJ 评测/AI 评语/查重、讨论区、学习小组、AI 问答、题库、学情预警、学习行为）
由 `t_` 前缀的**教师端自有表**承载。

部署时执行（**全部幂等，可重复执行；列/表已存在则自动跳过**）：

```bash
cd /opt/buct-ai-teaching/backend
python3 scripts/create_teacher_tables.py   # 建 t_ 自有表（CREATE TABLE IF NOT EXISTS）
python3 scripts/migrate_batch_a.py         # 补 course.open_time、student_warning 干预列；建 task/task_assignment
python3 scripts/migrate_batch_d.py         # 补 assignment 关联 OJ 列；建 qa_question
python3 scripts/migrate_batch_e.py         # 补 resource 视频字段（duration/缩略图/转码路径）
python3 scripts/migrate_batch_f.py         # 补 resource.oss_key（OSS 镜像）
python3 scripts/seed_admin.py              # 写入第一个教师账号（默认 admin / admin123456）
```

> 说明：`create_teacher_tables.py` 建 `t_` 前缀自有表；`migrate_batch_a/d/e/f.py` 负责给学校已有的
> `buct_cip` 表（course / student_warning / assignment / resource）**补新增列**——这些列无法靠
> `create_all` 自动补（`create_all` 只建缺失的表、不给已有表加列），故用幂等 `ALTER` 脚本。
> 如需灌入演示数据，可再执行 `python3 scripts/seed_study_behavior.py`（创建演示教师/课程/班级/学生并触发学情预警扫描）。
>
> `init_db.py` 是「本地建库」时代的兜底脚本（只 `create_all` 建缺失表、不会给已有表加列），
> 直接映射 buct_cip 的场景下已由上面的 migrate_batch_* 系列取代，无需执行。

### 3.3 安装依赖

```bash
cd /opt/buct-ai-teaching/backend
python3 -m pip install --upgrade pip
pip3 install -r requirements.txt
# 国内可加速：
# pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

---

## 四、启动后端（systemd 常驻）

创建 `/etc/systemd/system/buct-ai-teaching.service`：

```ini
[Unit]
Description=BUCT AI Teaching Platform Backend
After=network.target

[Service]
User=root
WorkingDirectory=/opt/buct-ai-teaching/backend
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

> 关键点：`WorkingDirectory` 必须是 `backend/`——`.env` 与 `uploads/` 都按相对路径解析，uvicorn 必须从该目录启动。生产环境**不要**加 `--reload`。

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now buct-ai-teaching
sudo systemctl status buct-ai-teaching
```

---

## 五、nginx 反向代理

创建 `/etc/nginx/conf.d/buct-ai-teaching.conf`：

```nginx
server {
    listen 80;
    server_name 101.42.1.248;   # 换成你的 IP 或域名

    # ---- 前端静态资源 ----
    root /opt/buct-ai-teaching/frontend/dist;
    index index.html;

    location / {
        try_files $uri $uri/ =404;
    }

    # ---- 后端 API ----
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        # 上传大小限制，与 backend/.env 的 MAX_UPLOAD_SIZE_MB 保持一致（留余量）
        client_max_body_size 110m;
    }

    # ---- 上传文件（后端 StaticFiles 挂载，代理给后端即可）----
    location /uploads/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

重载：

```bash
sudo nginx -t && sudo systemctl reload nginx
```

> 说明：前端为 Vue3 单页应用（hash 路由），构建产物在 `frontend/dist`；`/` 用 `try_files $uri $uri/ =404`（hash 路由无需 SPA history 回退）；`/api/` 原样透传（后端 `API_PREFIX=/api/v1`）；`/uploads/` 交给后端 `StaticFiles` 提供，保证与 OSS 回退逻辑一致。

---

## 六、可选：阿里云 OSS（对象存储 + 文档在线预览）

> 未开通 OSS 时（`OSS_ENABLED=false`）一切照旧：文件存本地磁盘、走 `/uploads/`；PDF/图片/视频浏览器原生可预览，Office 文档只能下载。开通后自动镜像 + 签名 URL + Office 转 PDF 预览。

1. 开通对象存储 OSS，创建 **Bucket**（记下名称与地域）。
2. 创建 RAM 子账号 AccessKey，最小权限：`oss:GetObject` / `oss:PutObject` / `oss:DeleteObject`。
3. （Office 在线预览必需）开通 **智能媒体管理 IMM**，创建 Project，并在 Bucket 的「数据处理」里绑定该 Project。**IMM 项目与 Bucket 必须同地域**。
4. 在 `backend/.env` 填写并开启：

```ini
OSS_ENABLED=true
OSS_ACCESS_KEY_ID=你的AccessKeyId
OSS_ACCESS_KEY_SECRET=你的AccessKeySecret
OSS_BUCKET=你的Bucket名
OSS_ENDPOINT=oss-cn-beijing.aliyuncs.com
OSS_REGION=cn-beijing
OSS_URL_EXPIRES=3600
```

5. 装依赖 + 补字段 + 重启：

```bash
cd /opt/buct-ai-teaching/backend
pip3 install -r requirements.txt       # 装上 oss2
python3 scripts/migrate_batch_f.py     # 幂等；补 resource.oss_key
sudo systemctl restart buct-ai-teaching
```

> 说明：上传流程不变（本地落盘 → 视频/文本处理 → 镜像 OSS）；本地磁盘仍是「工作副本」，OSS 是「服务/持久化层」。`GET /resources/{id}/file` 会 302 到 OSS 签名 URL 或本地 `/uploads`；`GET /resources/{id}/preview` 返回预览 URL（Office 走 IMM 转 PDF，失败回退下载）。

---

## 七、验证

```bash
# 后端健康检查（根路径返回 {"code":0,...}）
curl http://127.0.0.1:8000/

# 经 nginx 走通（同源）
curl http://101.42.1.248/api/v1/courses   # 应返回 JSON（可能需登录）
curl -I http://101.42.1.248/             # 200，返回 index.html

# Swagger 文档
# 浏览器打开 http://101.42.1.248/api/v1/docs 或 http://127.0.0.1:8000/docs
```

浏览器打开 `http://101.42.1.248/`，确认：登录 → 课程资源 → 上传一个 PDF 和一个 MP4 → 列表出现缩略图/时长 → 点「预览」能在线打开。

---

## 八、安全清单（上线前务必逐项确认）

- [ ] `backend/.env` 中 `SECRET_KEY` 已改为随机长字符串。
- [ ] 数据库密码、OJ 密码、LLM API Key 不泄露到前端代码。
- [ ] `backend/.env` **不得提交 git**（见 `.gitignore`）。
- [ ] 若 `.env` 曾误提交，执行 `git rm --cached backend/.env` 并**轮换所有泄露的密钥**（历史提交里仍可查到，仅删缓存不够）。
- [ ] 生产关闭 `DEBUG=true`（改为 `DEBUG=false`）。
- [ ] 云安全组只开放 80/443，不直接暴露 8000、3306。

---

## 九、常见问题

| 现象 | 排查 |
|---|---|
| 访问 IP 打不开 | nginx 是否启动；安全组是否放行 80 端口 |
| 前端能开、接口 404/502 | `systemctl status buct-ai-teaching` 看后端是否起来；nginx `location /api/` 是否正确 |
| 上传大文件失败 413 | `client_max_body_size` 小于文件大小，调大后 `nginx -s reload` |
| 视频没有缩略图/时长 | 服务器未装 `ffmpeg`/`ffprobe`，安装后重启后端 |
| 接口 401 | token 过期，重新登录 |
| OSS 上传失败但上传仍成功 | 查看后端日志 `backend/logs/`，多为 AK/endpoint/权限问题；未配好时自动回退本地 |
| Office 预览仍是下载 | IMM 未开通或未绑定 Project，回退为下载属正常降级 |
