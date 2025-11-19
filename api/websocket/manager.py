"""
WebSocket connection manager for real-time communication.

Provides comprehensive WebSocket handling with:
- Connection management and tracking
- Real-time broadcasting
- Room-based messaging
- Authentication and authorization
- Heartbeat and keep-alive
"""

import asyncio
import json
import logging
from typing import Dict, Set, List, Optional, Any, Callable
from datetime import datetime, timedelta
from enum import Enum
import uuid

from fastapi import WebSocket, WebSocketDisconnect, Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from mwa_core.config.settings import get_settings

logger = logging.getLogger(__name__)

class ConnectionStatus(Enum):
    """WebSocket connection status."""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"


class MessageType(Enum):
    """Types of WebSocket messages."""
    HEARTBEAT = "heartbeat"
    SYSTEM_STATUS = "system_status"
    SCRAPER_UPDATE = "scraper_update"
    CONTACT_DISCOVERY = "contact_discovery"
    NOTIFICATION = "notification"
    ERROR = "error"
    PING = "ping"
    PONG = "pong"
    DASHBOARD_UPDATE = "dashboard_update"
    JOB_STATUS = "job_status"


class WebSocketMessage:
    """WebSocket message structure."""
    
    def __init__(
        self,
        message_type: MessageType,
        data: Dict[str, Any],
        sender_id: Optional[str] = None,
        room: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        self.id = str(uuid.uuid4())
        self.type = message_type
        self.data = data
        self.sender_id = sender_id
        self.room = room
        self.timestamp = timestamp or datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "data": self.data,
            "sender_id": self.sender_id,
            "room": self.room,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WebSocketMessage':
        """Create message from dictionary."""
        message = cls(
            message_type=MessageType(data["type"]),
            data=data["data"],
            sender_id=data.get("sender_id"),
            room=data.get("room")
        )
        message.id = data["id"]
        message.timestamp = datetime.fromisoformat(data["timestamp"])
        return message


class WebSocketConnection:
    """WebSocket connection wrapper."""
    
    def __init__(
        self,
        websocket: WebSocket,
        user_id: Optional[str] = None,
        room: Optional[str] = None,
        connection_id: Optional[str] = None
    ):
        self.websocket = websocket
        self.user_id = user_id
        self.room = room
        self.connection_id = connection_id or str(uuid.uuid4())
        self.status = ConnectionStatus.CONNECTING
        self.created_at = datetime.now()
        self.last_heartbeat = datetime.now()
        self.metadata = {}
        
        # Callbacks
        self.on_connect: Optional[Callable] = None
        self.on_disconnect: Optional[Callable] = None
        self.on_message: Optional[Callable] = None
    
    async def send_message(self, message: WebSocketMessage) -> bool:
        """Send message to this connection."""
        try:
            await self.websocket.send_text(json.dumps(message.to_dict()))
            return True
        except Exception as e:
            logger.error(f"Failed to send message to connection {self.connection_id}: {e}")
            self.status = ConnectionStatus.DISCONNECTED
            return False
    
    async def send_data(self, data: Dict[str, Any], message_type: MessageType) -> bool:
        """Send data as message."""
        message = WebSocketMessage(message_type=message_type, data=data)
        return await self.send_message(message)
    
    async def close(self, code: int = 1000, reason: str = "Connection closed"):
        """Close the connection."""
        self.status = ConnectionStatus.DISCONNECTING
        try:
            await self.websocket.close(code=code, reason=reason)
        except Exception as e:
            logger.warning(f"Error closing websocket: {e}")
        finally:
            self.status = ConnectionStatus.DISCONNECTED


class WebSocketManager:
    """Comprehensive WebSocket connection manager."""
    
    def __init__(self):
        # Connection storage
        self.connections: Dict[str, WebSocketConnection] = {}
        self.room_connections: Dict[str, Set[str]] = {}
        self.user_connections: Dict[str, Set[str]] = {}
        
        # Authentication
        self.security = HTTPBearer()
        self.jwt_secret = get_settings().secret_key
        
        # Heartbeat and cleanup
        self.heartbeat_interval = 30  # seconds
        self.cleanup_interval = 300   # 5 minutes
        self.connection_timeout = 120  # 2 minutes
        
        # Statistics
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "disconnections": 0,
            "rooms_active": 0
        }
        
        # Background tasks
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
    
    def _generate_token(self, user_id: str, expires_in: int = 3600) -> str:
        """Generate JWT token for WebSocket connection."""
        payload = {
            "user_id": user_id,
            "type": "websocket",
            "exp": datetime.utcnow() + timedelta(seconds=expires_in)
        }
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
    
    def _verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token."""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            if payload.get("type") != "websocket":
                return None
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Expired WebSocket token")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid WebSocket token")
            return None
    
    async def connect(
        self,
        websocket: WebSocket,
        room: Optional[str] = None,
        token: Optional[str] = None
    ) -> WebSocketConnection:
        """Accept WebSocket connection."""
        await websocket.accept()
        
        # Authenticate if token provided
        user_id = None
        if token:
            payload = self._verify_token(token)
            if payload:
                user_id = payload.get("user_id")
            else:
                await websocket.close(code=4001, reason="Authentication failed")
                raise HTTPException(status_code=4001, detail="Authentication failed")
        
        # Create connection
        connection = WebSocketConnection(websocket, user_id, room)
        self.connections[connection.connection_id] = connection
        
        # Track in rooms
        if room:
            if room not in self.room_connections:
                self.room_connections[room] = set()
            self.room_connections[room].add(connection.connection_id)
        
        # Track for user
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = set()
            self.user_connections[user_id].add(connection.connection_id)
        
        # Update status
        connection.status = ConnectionStatus.CONNECTED
        self.stats["total_connections"] += 1
        self.stats["active_connections"] += 1
        if room:
            self.stats["rooms_active"] = len(self.room_connections)
        
        # Start background tasks if first connection
        if self.stats["active_connections"] == 1:
            await self._start_background_tasks()
        
        logger.info(f"WebSocket connected: {connection.connection_id} (room: {room}, user: {user_id})")
        
        # Send welcome message
        await connection.send_data(
            {
                "connection_id": connection.connection_id,
                "user_id": user_id,
                "room": room,
                "server_time": datetime.now().isoformat()
            },
            MessageType.DASHBOARD_UPDATE
        )
        
        return connection
    
    async def disconnect(self, connection: WebSocketConnection):
        """Handle WebSocket disconnection."""
        if connection.connection_id not in self.connections:
            return
        
        # Update status
        connection.status = ConnectionStatus.DISCONNECTED
        
        # Remove from tracking
        del self.connections[connection.connection_id]
        
        # Remove from room
        if connection.room and connection.room in self.room_connections:
            self.room_connections[connection.room].discard(connection.connection_id)
            if not self.room_connections[connection.room]:
                del self.room_connections[connection.room]
        
        # Remove from user connections
        if connection.user_id and connection.user_id in self.user_connections:
            self.user_connections[connection.user_id].discard(connection.connection_id)
            if not self.user_connections[connection.user_id]:
                del self.user_connections[connection.user_id]
        
        # Update statistics
        self.stats["active_connections"] -= 1
        self.stats["disconnections"] += 1
        if connection.room:
            self.stats["rooms_active"] = len(self.room_connections)
        
        logger.info(f"WebSocket disconnected: {connection.connection_id}")
        
        # Stop background tasks if no connections
        if self.stats["active_connections"] == 0:
            await self._stop_background_tasks()
    
    async def send_to_connection(self, connection_id: str, message: WebSocketMessage) -> bool:
        """Send message to specific connection."""
        connection = self.connections.get(connection_id)
        if not connection or connection.status != ConnectionStatus.CONNECTED:
            return False
        
        success = await connection.send_message(message)
        if success:
            self.stats["messages_sent"] += 1
        
        return success
    
    async def send_to_room(self, room: str, message: WebSocketMessage) -> int:
        """Broadcast message to all connections in room."""
        if room not in self.room_connections:
            return 0
        
        sent_count = 0
        failed_connections = []
        
        for connection_id in list(self.room_connections[room]):
            connection = self.connections.get(connection_id)
            if connection and connection.status == ConnectionStatus.CONNECTED:
                if await connection.send_message(message):
                    sent_count += 1
                else:
                    failed_connections.append(connection_id)
            else:
                failed_connections.append(connection_id)
        
        # Clean up failed connections
        for connection_id in failed_connections:
            await self.disconnect(self.connections.get(connection_id))
        
        if sent_count > 0:
            self.stats["messages_sent"] += sent_count
        
        return sent_count
    
    async def send_to_user(self, user_id: str, message: WebSocketMessage) -> int:
        """Send message to all connections for a user."""
        if user_id not in self.user_connections:
            return 0
        
        sent_count = 0
        failed_connections = []
        
        for connection_id in list(self.user_connections[user_id]):
            connection = self.connections.get(connection_id)
            if connection and connection.status == ConnectionStatus.CONNECTED:
                if await connection.send_message(message):
                    sent_count += 1
                else:
                    failed_connections.append(connection_id)
            else:
                failed_connections.append(connection_id)
        
        # Clean up failed connections
        for connection_id in failed_connections:
            await self.disconnect(self.connections.get(connection_id))
        
        if sent_count > 0:
            self.stats["messages_sent"] += sent_count
        
        return sent_count
    
    async def broadcast(self, message: WebSocketMessage) -> int:
        """Broadcast message to all connected clients."""
        if not self.connections:
            return 0
        
        sent_count = 0
        failed_connections = []
        
        for connection_id, connection in list(self.connections.items()):
            if connection.status == ConnectionStatus.CONNECTED:
                if await connection.send_message(message):
                    sent_count += 1
                else:
                    failed_connections.append(connection_id)
            else:
                failed_connections.append(connection_id)
        
        # Clean up failed connections
        for connection_id in failed_connections:
            await self.disconnect(self.connections.get(connection_id))
        
        if sent_count > 0:
            self.stats["messages_sent"] += sent_count
        
        return sent_count
    
    async def handle_message(self, connection: WebSocketConnection, message_data: str):
        """Handle incoming message from connection."""
        try:
            data = json.loads(message_data)
            message = WebSocketMessage.from_dict(data)
            self.stats["messages_received"] += 1
            
            # Handle different message types
            if message.type == MessageType.PING:
                await connection.send_data({"timestamp": datetime.now().isoformat()}, MessageType.PONG)
            elif message.type == MessageType.HEARTBEAT:
                connection.last_heartbeat = datetime.now()
                await connection.send_data({"status": "ok"}, MessageType.HEARTBEAT)
            elif message.type == MessageType.DASHBOARD_UPDATE:
                # Handle dashboard-specific updates
                await self._handle_dashboard_update(connection, message)
            
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON message from {connection.connection_id}")
        except Exception as e:
            logger.error(f"Error handling message from {connection.connection_id}: {e}")
    
    async def _handle_dashboard_update(self, connection: WebSocketConnection, message: WebSocketMessage):
        """Handle dashboard-specific update messages."""
        # Implementation for dashboard updates
        # This could trigger real-time data refreshes, statistics updates, etc.
        pass
    
    async def _heartbeat_task(self):
        """Background task for heartbeat and connection health."""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                
                # Check for stale connections
                stale_connections = []
                cutoff_time = datetime.now() - timedelta(seconds=self.connection_timeout)
                
                for connection_id, connection in self.connections.items():
                    if connection.status == ConnectionStatus.CONNECTED:
                        # Send heartbeat
                        await connection.send_data(
                            {"timestamp": datetime.now().isoformat()},
                            MessageType.HEARTBEAT
                        )
                        
                        # Check if connection is stale
                        if connection.last_heartbeat < cutoff_time:
                            stale_connections.append(connection_id)
                
                # Close stale connections
                for connection_id in stale_connections:
                    connection = self.connections.get(connection_id)
                    if connection:
                        await connection.close(code=1001, reason="Connection stale")
                        await self.disconnect(connection)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat task: {e}")
    
    async def _cleanup_task(self):
        """Background task for cleaning up resources."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                
                # Clean up old statistics
                current_time = datetime.now()
                
                # Log connection statistics
                if self.stats["active_connections"] > 0:
                    logger.info(f"WebSocket stats: {self.stats}")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
    
    async def _start_background_tasks(self):
        """Start background tasks."""
        if not self._heartbeat_task or self._heartbeat_task.done():
            self._heartbeat_task = asyncio.create_task(self._heartbeat_task())
        
        if not self._cleanup_task or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_task())
    
    async def _stop_background_tasks(self):
        """Stop background tasks."""
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
    
    def get_connection_info(self, connection_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific connection."""
        connection = self.connections.get(connection_id)
        if not connection:
            return None
        
        return {
            "connection_id": connection.connection_id,
            "user_id": connection.user_id,
            "room": connection.room,
            "status": connection.status.value,
            "created_at": connection.created_at.isoformat(),
            "last_heartbeat": connection.last_heartbeat.isoformat(),
            "uptime_seconds": (datetime.now() - connection.created_at).total_seconds()
        }
    
    def get_room_info(self, room: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific room."""
        if room not in self.room_connections:
            return None
        
        connections = [
            self.get_connection_info(conn_id) 
            for conn_id in self.room_connections[room]
        ]
        
        return {
            "room": room,
            "connection_count": len(connections),
            "connections": connections
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket statistics."""
        return {
            **self.stats,
            "active_rooms": len(self.room_connections),
            "connected_users": len(self.user_connections)
        }


# Global WebSocket manager instance
websocket_manager = WebSocketManager()