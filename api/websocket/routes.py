"""
WebSocket routes and endpoints for real-time communication.

Provides WebSocket endpoints for:
- Real-time dashboard updates
- Live scraper status monitoring  
- Contact discovery notifications
- System health monitoring
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException, Depends
from fastapi.responses import HTMLResponse

from .manager import (
    websocket_manager, 
    WebSocketConnection, 
    MessageType, 
    WebSocketMessage
)
from api.auth import get_current_user
from mwa_core.config.settings import get_settings

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/websocket", tags=["WebSocket"])

# HTML pages for WebSocket testing
WEBSOCKET_TEST_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <title>MWA Core WebSocket Test</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }
        .status { padding: 10px; border-radius: 5px; margin: 10px 0; }
        .connected { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .disconnected { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .message { background: #e2e3e5; padding: 10px; margin: 5px 0; border-radius: 3px; }
        #messages { max-height: 300px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; }
        input, button { padding: 10px; margin: 5px; }
        button { background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #0056b3; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔌 MWA Core WebSocket Test</h1>
        
        <div id="connection-status" class="status disconnected">
            Status: Disconnected
        </div>
        
        <div>
            <input type="text" id="room" placeholder="Room (optional)" style="width: 200px;">
            <input type="text" id="token" placeholder="JWT Token (optional)" style="width: 300px;">
            <button onclick="connect()">Connect</button>
            <button onclick="disconnect()">Disconnect</button>
        </div>
        
        <div>
            <button onclick="sendHeartbeat()">Send Heartbeat</button>
            <button onclick="sendPing()">Send Ping</button>
            <button onclick="sendDashboardUpdate()">Send Dashboard Update</button>
        </div>
        
        <div>
            <input type="text" id="custom-message" placeholder="Custom message" style="width: 400px;">
            <button onclick="sendCustomMessage()">Send Custom</button>
        </div>
        
        <h3>Messages:</h3>
        <div id="messages"></div>
    </div>

    <script>
        let ws = null;
        let messageCount = 0;

        function updateStatus(status, className) {
            const statusDiv = document.getElementById('connection-status');
            statusDiv.textContent = 'Status: ' + status;
            statusDiv.className = 'status ' + className;
        }

        function addMessage(message) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message';
            messageDiv.textContent = `[${new Date().toISOString()}] ${message}`;
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
            messageCount++;
            
            if (messageCount > 50) {
                messagesDiv.removeChild(messagesDiv.firstChild);
                messageCount--;
            }
        }

        function connect() {
            const room = document.getElementById('room').value;
            const token = document.getElementById('token').value;
            
            const wsUrl = `ws://localhost:8000/api/v1/websocket/connect`;
            const url = token ? `${wsUrl}?token=${encodeURIComponent(token)}` : wsUrl;
            
            ws = new WebSocket(url);
            
            ws.onopen = function(event) {
                updateStatus('Connected', 'connected');
                addMessage('WebSocket connected');
                
                // Join room if specified
                if (room) {
                    ws.send(JSON.stringify({
                        type: 'join_room',
                        data: { room: room }
                    }));
                }
            };
            
            ws.onmessage = function(event) {
                try {
                    const data = JSON.parse(event.data);
                    addMessage(`Received: ${JSON.stringify(data, null, 2)}`);
                } catch (e) {
                    addMessage(`Received: ${event.data}`);
                }
            };
            
            ws.onclose = function(event) {
                updateStatus('Disconnected', 'disconnected');
                addMessage(`WebSocket closed: ${event.code} - ${event.reason}`);
            };
            
            ws.onerror = function(error) {
                addMessage('WebSocket error: ' + error);
            };
        }
        
        function disconnect() {
            if (ws) {
                ws.close();
                ws = null;
            }
        }
        
        function sendHeartbeat() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'heartbeat',
                    data: { timestamp: new Date().toISOString() }
                }));
            }
        }
        
        function sendPing() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'ping',
                    data: { timestamp: new Date().toISOString() }
                }));
            }
        }
        
        function sendDashboardUpdate() {
            if (ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'dashboard_update',
                    data: { 
                        action: 'refresh_stats',
                        timestamp: new Date().toISOString()
                    }
                }));
            }
        }
        
        function sendCustomMessage() {
            const message = document.getElementById('custom-message').value;
            if (ws && ws.readyState === WebSocket.OPEN && message) {
                ws.send(message);
            }
        }
        
        // Auto-connect for testing
        window.onload = function() {
            addMessage('WebSocket test page loaded. Click Connect to start.');
        };
    </script>
</body>
</html>
"""


@router.get("/test")
async def websocket_test_page():
    """WebSocket test page."""
    return HTMLResponse(content=WEBSOCKET_TEST_PAGE)


@router.websocket("/connect")
async def websocket_endpoint(
    websocket: WebSocket,
    room: Optional[str] = Query(None, description="Room to join"),
    token: Optional[str] = Query(None, description="JWT token for authentication")
):
    """Main WebSocket endpoint for real-time communication."""
    connection: Optional[WebSocketConnection] = None
    
    try:
        # Accept connection with authentication
        connection = await websocket_manager.connect(websocket, room, token)
        
        # Handle incoming messages
        while True:
            try:
                # Receive message
                data = await websocket.receive_text()
                
                # Process message
                await websocket_manager.handle_message(connection, data)
                
            except WebSocketDisconnect:
                logger.info(f"WebSocket client disconnected: {connection.connection_id}")
                break
            except Exception as e:
                logger.error(f"Error handling WebSocket message: {e}")
                # Send error message to client
                await connection.send_data(
                    {"error": str(e), "timestamp": datetime.now().isoformat()},
                    MessageType.ERROR
                )
    
    except HTTPException as e:
        logger.warning(f"WebSocket authentication failed: {e.detail}")
        await websocket.close(code=e.status_code, reason=e.detail)
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection.connection_id if connection else 'unknown'}")
    
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        if connection:
            await connection.close(code=1011, reason="Internal server error")
    
    finally:
        # Clean up connection
        if connection:
            await websocket_manager.disconnect(connection)


@router.post("/broadcast")
async def broadcast_message(
    message: Dict[str, Any],
    room: Optional[str] = None,
    user_id: Optional[str] = None,
    current_user: Optional[Dict] = Depends(get_current_user)
):
    """
    Broadcast message to WebSocket clients.
    
    Requires admin permissions.
    """
    # Check admin permissions
    if not current_user or current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin permissions required")
    
    # Create message
    ws_message = WebSocketMessage(
        message_type=MessageType(message.get("type", "notification")),
        data=message.get("data", {}),
        sender_id=current_user.get("username")
    )
    
    # Send to appropriate recipients
    if room:
        sent_count = await websocket_manager.send_to_room(room, ws_message)
    elif user_id:
        sent_count = await websocket_manager.send_to_user(user_id, ws_message)
    else:
        sent_count = await websocket_manager.broadcast(ws_message)
    
    return {
        "status": "broadcast_sent",
        "sent_count": sent_count,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/stats")
async def websocket_stats():
    """Get WebSocket connection statistics."""
    return websocket_manager.get_stats()


@router.get("/connections")
async def list_connections():
    """List all active WebSocket connections."""
    connections = []
    for connection_id, connection in websocket_manager.connections.items():
        connections.append({
            "connection_id": connection.connection_id,
            "user_id": connection.user_id,
            "room": connection.room,
            "status": connection.status.value,
            "created_at": connection.created_at.isoformat(),
            "uptime_seconds": (datetime.now() - connection.created_at).total_seconds()
        })
    
    return {"connections": connections}


@router.get("/rooms")
async def list_rooms():
    """List all active WebSocket rooms."""
    rooms = []
    for room, connection_ids in websocket_manager.room_connections.items():
        rooms.append({
            "room": room,
            "connection_count": len(connection_ids),
            "connections": list(connection_ids)
        })
    
    return {"rooms": rooms}


@router.post("/system-status")
async def broadcast_system_status(
    status_data: Dict[str, Any],
    current_user: Optional[Dict] = Depends(get_current_user)
):
    """
    Broadcast system status update to dashboard clients.
    
    Requires user permissions or higher.
    """
    # Check user permissions
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Add timestamp and sender info
    status_data.update({
        "timestamp": datetime.now().isoformat(),
        "sender": current_user.get("username"),
        "sender_role": current_user.get("role")
    })
    
    # Create and broadcast message
    message = WebSocketMessage(
        message_type=MessageType.SYSTEM_STATUS,
        data=status_data,
        sender_id=current_user.get("username"),
        room="dashboard"
    )
    
    sent_count = await websocket_manager.send_to_room("dashboard", message)
    
    return {
        "status": "broadcast_sent",
        "sent_count": sent_count,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/scraper-update")
async def broadcast_scraper_update(
    update_data: Dict[str, Any],
    current_user: Optional[Dict] = Depends(get_current_user)
):
    """
    Broadcast scraper status update.
    
    Requires user permissions or higher.
    """
    # Check user permissions
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Add timestamp and sender info
    update_data.update({
        "timestamp": datetime.now().isoformat(),
        "sender": current_user.get("username")
    })
    
    # Create and broadcast message
    message = WebSocketMessage(
        message_type=MessageType.SCRAPER_UPDATE,
        data=update_data,
        sender_id=current_user.get("username"),
        room="scraper"
    )
    
    sent_count = await websocket_manager.send_to_room("scraper", message)
    
    return {
        "status": "broadcast_sent",
        "sent_count": sent_count,
        "timestamp": datetime.now().isoformat()
    }


@router.post("/contact-discovery")
async def broadcast_contact_discovery(
    discovery_data: Dict[str, Any],
    current_user: Optional[Dict] = Depends(get_current_user)
):
    """
    Broadcast contact discovery update.
    
    Requires user permissions or higher.
    """
    # Check user permissions
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Add timestamp and sender info
    discovery_data.update({
        "timestamp": datetime.now().isoformat(),
        "sender": current_user.get("username")
    })
    
    # Create and broadcast message
    message = WebSocketMessage(
        message_type=MessageType.CONTACT_DISCOVERY,
        data=discovery_data,
        sender_id=current_user.get("username"),
        room="contacts"
    )
    
    sent_count = await websocket_manager.send_to_room("contacts", message)
    
    return {
        "status": "broadcast_sent",
        "sent_count": sent_count,
        "timestamp": datetime.now().isoformat()
    }