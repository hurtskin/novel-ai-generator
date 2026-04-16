"""
API 路由模块

导出所有路由模块供应用使用
"""

from api.routes import generation, websocket, snapshots

__all__ = ["generation", "websocket", "snapshots"]
