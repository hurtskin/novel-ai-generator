"""
FastAPI 应用主模块

提供 Novel AI Generator 的后端 API 服务
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    应用生命周期管理
    
    处理应用启动和关闭时的初始化与清理工作
    """
    # 启动时执行
    logger.info("Starting Novel AI Generator API...")
    
    # 确保必要的目录存在
    os.makedirs("logs", exist_ok=True)
    os.makedirs("storage", exist_ok=True)
    
    # 初始化依赖注入容器（仅在容器未初始化时创建）
    # 避免覆盖 main.py 中已设置的容器，确保单例状态不丢失
    if not hasattr(app.state, "container") or app.state.container is None:
        from core.container_config import initialize_container
        app.state.container = initialize_container()
        logger.info("Dependency injection container initialized")
    else:
        logger.info(f"Using existing container from app.state: {id(app.state.container)}")
    
    yield
    
    # 关闭时执行
    logger.info("Shutting down Novel AI Generator API...")


def create_app() -> FastAPI:
    """
    创建 FastAPI 应用实例
    
    Returns:
        FastAPI: 配置完成的 FastAPI 应用
    """
    app = FastAPI(
        title="Novel AI Generator",
        description="AI-powered novel generation system with multi-style support",
        version="2.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )
    
    # 配置 CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生产环境应该限制具体域名
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册路由
    _register_routes(app)
    
    # 配置静态文件
    _setup_static_files(app)
    
    # 配置全局异常处理
    _setup_exception_handlers(app)
    
    # 注册根路由
    @app.get("/")
    async def root():
        """根路径 - API 信息"""
        return {
            "name": "Novel AI Generator API",
            "version": "2.0.0",
            "docs": "/docs",
            "health": "/health",
        }
    
    @app.get("/health")
    async def health_check():
        """健康检查端点"""
        return {
            "status": "healthy",
            "service": "novel-ai-generator",
        }
    
    return app


def _register_routes(app: FastAPI) -> None:
    """注册所有路由模块"""
    from api.routes import generation, websocket, snapshots, versions
    
    # 生成相关路由
    app.include_router(
        generation.router,
        prefix="/api",
        tags=["generation"],
    )
    
    # WebSocket 路由
    app.include_router(
        websocket.router,
        prefix="/api",
        tags=["websocket"],
    )
    
    # 快照管理路由
    app.include_router(
        snapshots.router,
        prefix="/api",
        tags=["snapshots"],
    )
    
    # 版本管理路由
    app.include_router(
        versions.router,
        prefix="/api",
        tags=["versions"],
    )
    
    logger.info("Routes registered successfully")


def _setup_static_files(app: FastAPI) -> None:
    """配置静态文件服务"""
    ui_dir = os.path.join(os.path.dirname(__file__), "..", "ui", "dist")
    if os.path.exists(ui_dir):
        app.mount("/static", StaticFiles(directory=ui_dir), name="static")
        logger.info(f"Static files mounted from {ui_dir}")


def _setup_exception_handlers(app: FastAPI) -> None:
    """配置全局异常处理"""
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request, exc):
        """全局异常处理器"""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "detail": str(exc) if os.getenv("DEBUG") else "Please check server logs",
            },
        )
    
    @app.exception_handler(ValueError)
    async def value_error_handler(request, exc):
        """值错误处理器"""
        return JSONResponse(
            status_code=400,
            content={
                "error": "Bad request",
                "detail": str(exc),
            },
        )


# 创建应用实例（供导入使用）
app = create_app()
