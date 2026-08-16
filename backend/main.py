"""BUCT AI 教学平台 - FastAPI 应用入口。

启动方式（在 backend/ 目录下）：
    uvicorn main:app --host 0.0.0.0 --port 8000 --reload
"""
import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.exceptions import AppError
from app.middleware import AccessLogMiddleware
from app.utils.logger import setup_logging

# 导入模型包，确保所有 ORM 表注册到 Base.metadata（供 create_all / alembic 使用）
import app.models  # noqa: F401

from app.routers import (  # noqa: E402
    assignment, auth, class_ as class_router, course, dashboard,
    message, process, qa, resource, task, teaching, team, user, warning,
)

setup_logging()
logger = logging.getLogger("app")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description="面向大学算法竞赛指导教师的 AI 教学管理平台后端",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    # CORS：前后端完全分离，允许跨域访问
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(AccessLogMiddleware)

    # ---------- 全局异常处理 ----------
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        """业务异常统一转成 {code, message, data:null}。"""
        return JSONResponse(status_code=exc.code, content=exc.to_dict())

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception):
        """兜底：未捕获异常返回 500，同时打印完整堆栈便于排查。"""
        logger.exception("未处理异常: %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": "服务器内部错误", "data": None},
        )

    # ---------- 注册路由 ----------
    prefix = settings.API_PREFIX
    app.include_router(auth.router, prefix=prefix)
    app.include_router(user.router, prefix=prefix)
    app.include_router(course.router, prefix=prefix)
    app.include_router(class_router.router, prefix=prefix)
    app.include_router(resource.router, prefix=prefix)
    app.include_router(assignment.router, prefix=prefix)
    app.include_router(teaching.router, prefix=prefix)
    app.include_router(process.router, prefix=prefix)
    app.include_router(warning.router, prefix=prefix)
    app.include_router(dashboard.router, prefix=prefix)
    app.include_router(message.router, prefix=prefix)
    app.include_router(team.router, prefix=prefix)
    app.include_router(task.router, prefix=prefix)
    app.include_router(qa.router, prefix=prefix)

    # ---------- 上传文件静态访问 ----------
    uploads_dir = Path(settings.UPLOAD_DIR)
    uploads_dir.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

    @app.get("/", include_in_schema=False)
    def health():
        return {"code": 0, "message": f"{settings.APP_NAME} 后端运行中", "data": None}

    return app


app = create_app()
