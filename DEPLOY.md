# 部署指南（DEPLOY）

> 面向轻量级服务器（如阿里云 ECS / 腾讯云轻量应用服务器）的部署说明。
> 已部署示例：`http://101.42.1.248/`。本文同时覆盖「全新部署」与「已部署服务器升级到最新代码」。

## 架构总览

```
浏览器
   │  http://<服务器 IP>/
   ▼
nginx（80 端口）
   ├── /            → 前端静态文件（frontend/ 目录）
   ├── /api/        → 反向代理到 uvicorn（127.0.0.1:8000）
   └── /uploads/    → 反向代理到 uvicorn（后端挂载的 StaticFiles）
                          │
                          ▼
                 uvicorn（FastAPI，127.0.0.1:8000）
                          ├── MySQL 8.0（元数据）
                          ├── 本地磁盘 uploads/（工作副本）
                          └── 阿里云 OSS（可选，镜像 + 文档在线预览）
```

前端 `api.js` 已改为**相对路径** `/api/v1`（同源部署），因此**必须**通过 nginx 同源反代，前端和后端要在同一个域名/IP 下。

---

## 一、环境准备

| 依赖 | 说明 |
|---|---|
| Python 3.10+ | 后端运行环境 |
| MySQL 8.0 | 业务数据库 |
| ffmpeg / ffprobe | 视频转码、关键帧抽取（缺失不影响其它功能，仅视频后处理降级） |
| nginx | 反向代理 + 静态资源托管 |
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

MySQL 8.0 请按官方文档安装（也可用服务器自带的数据库，或云 RDS）。

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
├── frontend/          # 前端静态文件（nginx 的 root）
└── backend/           # 后端（uvicorn 的 WorkingDirectory）
    ├── main.py
    ├── requirements.txt
    ├── .env           # 环境变量（不入 git）
    ├── uploads/       # 上传文件（工作副本，可整体备份）
    └── scripts/       # init_db.py / migrate_batch_*.py / seed_*.py
```

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
| `DB_HOST` / `DB_PORT` / `DB_USER` / `DB_PASSWORD` / `DB_NAME` | MySQL 连接 |
| `SECRET_KEY` | JWT 密钥，**务必改成随机长字符串** |
| `LLM_API_KEY` / `LLM_API_BASE` / `LLM_MODEL` | 大模型 API |
| `OJ_API_BASE` / `OJ_USERNAME` / `OJ_PASSWORD` | 学校 OJ 对接 |
| `OJ_DB_*` | 学校 OJ 只读库（可选） |
| `OSS_*` | 阿里云 OSS（可选，见第五节） |

### 3.2 初始化数据库

**全新部署**（库里还没有表）——用 ORM 一次性建全部表：

```bash
cd /opt/buct-ai-teaching/backend
python3 scripts/init_db.py
```

**已部署服务器升级**（库已存在，只差新字段）——按需跑增量迁移脚本（均幂等，可重复执行）：

```bash
python3 scripts/migrate_batch_d.py   # 较早批次（如已执行过可跳过）
python3 scripts/migrate_batch_e.py   # 视频 duration/thumbnail/transcoded 字段
python3 scripts/migrate_batch_f.py   # OSS 镜像字段 resource.oss_key
```

> 迁移脚本只补「已经存在的表」缺的列；全新库直接 `init_db.py` 即可，无需跑 migrate_*。

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
    root /opt/buct-ai-teaching/frontend;
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

> 说明：前端为多页应用（`pages/*.html` 是真实文件），因此 `/` 用 `try_files $uri $uri/ =404`；`/api/` 原样透传（后端 `API_PREFIX=/api/v1`）；`/uploads/` 交给后端 `StaticFiles` 提供，保证与 OSS 回退逻辑一致。

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
