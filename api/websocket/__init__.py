"""
WebSocket Package

Provides WebSocket functionality for real-time communication in the MWA Core API:
- Connection management
- Real-time broadcasting
- Room-based messaging
- Authentication and authorization
- Dashboard updates and notifications
"""

from .manager import (
    WebSocketManager,
    WebSocketConnection,
    WebSocketMessage,
    MessageType,
    ConnectionStatus,
    websocket_manager
)

from .routes import router as websocket_router

__all__ = [
    "WebSocketManager",
    "WebSocketConnection", 
    "WebSocketMessage",
    "MessageType",
    "ConnectionStatus",
    "websocket_manager",
    "websocket_router"
]