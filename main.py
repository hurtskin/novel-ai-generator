"""
Novel AI Generator - 应用入口

精简版入口文件，仅包含应用初始化和启动逻辑。
所有业务逻辑已迁移至服务层和 API 层。
"""

import logging
import os
from typing import Dict, Any

# 启动时清空 app.log
app_log_path = 'logs/app.log'
try:
    os.makedirs(os.path.dirname(app_log_path), exist_ok=True)
    if os.path.exists(app_log_path):
        with open(app_log_path, "w", encoding="utf-8") as f:
            f.write("")
        print("App log cleared on startup")
except Exception as e:
    print(f"Failed to clear app log: {e}")

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def print_dependency_mappings(container: Any) -> None:
    """
    打印依赖映射信息
    
    用于开发和调试，显示容器中注册的接口与实现映射
    
    Args:
        container: 依赖注入容器
    """
    logger.info("=" * 60)
    logger.info("Dependency Injection Container Mappings")
    logger.info("=" * 60)
    
    interfaces = container.get_registered_interfaces()
    for interface in interfaces:
        registrations = container._registrations.get(interface, [])
        for reg in registrations:
            impl_name = reg.implementation.__name__ if reg.implementation else "N/A"
            scope_name = reg.scope.name if hasattr(reg.scope, 'name') else str(reg.scope)
            logger.info(f"  {interface.__name__} -> {impl_name} ({scope_name})")
    
    logger.info("=" * 60)


def initialize_application() -> Any:
    """
    初始化应用程序
    
    执行以下初始化步骤：
    1. 确保必要目录存在
    2. 初始化依赖注入容器
    3. 打印依赖映射信息
    
    Returns:
        FastAPI: 配置完成的 FastAPI 应用实例
    """
    # 确保必要目录存在
    os.makedirs("logs", exist_ok=True)
    os.makedirs("storage", exist_ok=True)
    os.makedirs("output", exist_ok=True)
    
    logger.info("Initializing Novel AI Generator...")
    
    # 初始化依赖注入容器
    from core.container_config import initialize_container_with_rag
    container = initialize_container_with_rag()
    logger.info("Dependency injection container initialized")

    # 主动解析 DebugLogService 以触发初始化（会执行启动时清空）
    try:
        from services.interfaces import DebugLogService
        debug_log_service = container.resolve(DebugLogService)
        logger.info("DebugLogService initialized, debug log cleared on startup")
    except Exception as e:
        logger.warning(f"Failed to initialize DebugLogService: {e}")

    # 打印依赖映射
    print_dependency_mappings(container)
    
    # 创建并配置 FastAPI 应用
    from api.app import create_app
    app = create_app()
    
    # 将容器附加到应用状态
    app.state.container = container
    
    logger.info("Application initialization completed")
    return app


# 创建应用实例（供 ASGI 服务器使用）
app = initialize_application()


if __name__ == "__main__":
    import uvicorn
    
    # 从配置读取端口
    try:
        from core.container_config import initialize_container
        container = initialize_container()
        config_provider = container.resolve(__import__('interfaces', fromlist=['ConfigProvider']).ConfigProvider)
        port = config_provider.get_int("api.port", 8000)
    except Exception:
        port = 8000
    
    logger.info(f"Starting server on port {port}")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info",
    )
