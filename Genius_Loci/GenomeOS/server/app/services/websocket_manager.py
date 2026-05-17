"""
WebSocket connection manager for real-time communication.
Handles robot and client connections with message routing.
"""
import asyncio
import json
from typing import Dict, List, Set
from fastapi import WebSocket
from core.logger import get_logger


class WebSocketManager:
    """Manages WebSocket connections for robots and web clients."""

    def __init__(self):
        self.logger = get_logger("Server.WebSocket")

        # Robot connections: robot_id -> WebSocket
        self._robot_connections: Dict[str, WebSocket] = {}

        # Client connections: set of WebSockets
        self._client_connections: Set[WebSocket] = set()

        self.robot_count = 0
        self.client_count = 0

    async def connect_robot(self, websocket: WebSocket, robot_id: str):
        """Accept robot WebSocket connection."""
        await websocket.accept()
        self._robot_connections[robot_id] = websocket
        self.robot_count = len(self._robot_connections)
        self.logger.info(f"Robot connected: {robot_id} (total: {self.robot_count})")

        # Notify clients
        await self.broadcast_to_clients({
            "type": "robot_connected",
            "robot_id": robot_id
        })

    async def disconnect_robot(self, robot_id: str):
        """Handle robot disconnection."""
        if robot_id in self._robot_connections:
            del self._robot_connections[robot_id]
            self.robot_count = len(self._robot_connections)
            self.logger.info(f"Robot disconnected: {robot_id}")

            await self.broadcast_to_clients({
                "type": "robot_disconnected",
                "robot_id": robot_id
            })

    async def connect_client(self, websocket: WebSocket):
        """Accept client WebSocket connection."""
        await websocket.accept()
        self._client_connections.add(websocket)
        self.client_count = len(self._client_connections)
        self.logger.info(f"Client connected (total: {self.client_count})")

    async def disconnect_client(self, websocket: WebSocket):
        """Handle client disconnection."""
        self._client_connections.discard(websocket)
        self.client_count = len(self._client_connections)

    async def handle_robot_message(self, robot_id: str, data: dict):
        """Process message from robot."""
        msg_type = data.get("type", "unknown")

        if msg_type == "telemetry":
            # Forward telemetry to all clients
            await self.broadcast_to_clients({
                "type": "telemetry",
                "robot_id": robot_id,
                "data": data.get("data", {})
            })
        elif msg_type == "task_update":
            await self.broadcast_to_clients({
                "type": "task_update",
                "robot_id": robot_id,
                "task": data.get("task", {})
            })
        elif msg_type == "log":
            self.logger.info(f"[{robot_id}] {data.get('message', '')}")

    async def handle_client_message(self, websocket: WebSocket, data: dict):
        """Process message from web client."""
        msg_type = data.get("type", "unknown")

        if msg_type == "create_task":
            # Forward to dispatcher
            pass
        elif msg_type == "command_robot":
            robot_id = data.get("robot_id")
            command = data.get("command", {})
            await self.send_to_robot(robot_id, command)

    async def send_to_robot(self, robot_id: str, message: dict):
        """Send message to specific robot."""
        ws = self._robot_connections.get(robot_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception as e:
                self.logger.error(f"Send to robot {robot_id} failed: {e}")

    async def broadcast_to_clients(self, message: dict):
        """Broadcast message to all connected clients."""
        disconnected = set()
        for ws in self._client_connections:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.add(ws)

        for ws in disconnected:
            self._client_connections.discard(ws)

    async def broadcast_to_robots(self, message: dict):
        """Broadcast message to all robots."""
        disconnected = []
        for rid, ws in self._robot_connections.items():
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(rid)

        for rid in disconnected:
            await self.disconnect_robot(rid)

    def get_connected_robots(self) -> List[str]:
        return list(self._robot_connections.keys())
