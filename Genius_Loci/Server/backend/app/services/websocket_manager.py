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

        # Upsert robot in database
        self._upsert_robot_db(robot_id, {
            "status": "free",
            "battery_percent": 100.0,
        })

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
            # Update robot state in database
            telemetry_data = data.get("data", {})
            pose = telemetry_data.get("pose", {})
            self._upsert_robot_db(robot_id, {
                "current_x": pose.get("x", 0),
                "current_y": pose.get("y", 0),
                "current_theta": pose.get("theta", 0),
                "battery_percent": telemetry_data.get("battery_percent", 100),
                "status": telemetry_data.get("status", "free"),
            })

            # Forward telemetry to all clients
            await self.broadcast_to_clients({
                "type": "telemetry",
                "robot_id": robot_id,
                "data": telemetry_data
            })
        elif msg_type == "task_update":
            task_data = data.get("task", {})
            self._update_task_db(task_data)
            await self.broadcast_to_clients({
                "type": "task_update",
                "robot_id": robot_id,
                "task": task_data
            })
        elif msg_type == "log":
            self.logger.info(f"[{robot_id}] {data.get('message', '')}")

    async def handle_client_message(self, websocket: WebSocket, data: dict):
        """Process message from web client."""
        msg_type = data.get("type", "unknown")

        if msg_type == "get_robots":
            await self._send_robots_list(websocket)
        elif msg_type == "get_tasks":
            await self._send_tasks_list(websocket)
        elif msg_type == "create_task":
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

    def _upsert_robot_db(self, robot_id: str, data: dict):
        """Create or update robot in database."""
        from app.models.database import SessionLocal, Robot, RobotStatus
        db = SessionLocal()
        try:
            robot = db.query(Robot).filter(Robot.robot_id == robot_id).first()
            if not robot:
                robot = Robot(
                    robot_id=robot_id,
                    name=f"Genius Loci {robot_id}",
                )
                db.add(robot)

            if "current_x" in data:
                robot.current_x = data["current_x"]
            if "current_y" in data:
                robot.current_y = data["current_y"]
            if "current_theta" in data:
                robot.current_theta = data["current_theta"]
            if "battery_percent" in data:
                robot.battery_percent = data["battery_percent"]
            if "status" in data:
                status_str = data["status"]
                try:
                    robot.status = RobotStatus(status_str)
                except ValueError:
                    robot.status = RobotStatus.FREE

            from datetime import datetime
            robot.last_seen = datetime.utcnow()
            db.commit()
        except Exception as e:
            self.logger.error(f"DB upsert error for {robot_id}: {e}")
            db.rollback()
        finally:
            db.close()

    def get_connected_robots(self) -> List[str]:
        return list(self._robot_connections.keys())

    async def _send_robots_list(self, websocket: WebSocket):
        """Send full robots list from database to client."""
        from app.models.database import SessionLocal, Robot
        db = SessionLocal()
        try:
            robots = db.query(Robot).all()
            await websocket.send_json({
                "type": "robots_list",
                "robots": [{
                    "id": r.robot_id,
                    "name": r.name,
                    "status": r.status.value if hasattr(r.status, 'value') else str(r.status),
                    "x": r.current_x,
                    "y": r.current_y,
                    "theta": r.current_theta,
                    "battery": r.battery_percent,
                    "currentTaskId": r.current_task_id,
                    "lastSeen": r.last_seen.isoformat() if r.last_seen else None
                } for r in robots]
            })
        finally:
            db.close()

    async def _send_tasks_list(self, websocket: WebSocket):
        """Send full tasks list from database to client."""
        from app.models.database import SessionLocal, Task as TaskModel
        db = SessionLocal()
        try:
            tasks = db.query(TaskModel).order_by(TaskModel.created_at.desc()).all()
            await websocket.send_json({
                "type": "tasks_list",
                "tasks": [{
                    "id": t.task_id,
                    "taskId": t.task_id,
                    "type": t.type,
                    "status": t.status.value if hasattr(t.status, 'value') else str(t.status),
                    "pickupX": t.pickup_x,
                    "pickupY": t.pickup_y,
                    "dropoffX": t.dropoff_x,
                    "dropoffY": t.dropoff_y,
                    "priority": t.priority,
                    "robotId": t.robot_id,
                    "payloadWeightKg": t.payload_weight_kg,
                    "payloadDescription": t.payload_description,
                    "createdAt": t.created_at.isoformat() if t.created_at else None
                } for t in tasks]
            })
        finally:
            db.close()

    def _update_task_db(self, task_data: dict):
        """Update task status in database."""
        from app.models.database import SessionLocal, Task as TaskModel, TaskStatus
        db = SessionLocal()
        try:
            task = db.query(TaskModel).filter(TaskModel.task_id == task_data.get("id")).first()
            if task:
                status_str = task_data.get("status", "")
                status_map = {
                    "in_progress": TaskStatus.IN_PROGRESS,
                    "completing": TaskStatus.COMPLETED,
                    "completed": TaskStatus.COMPLETED,
                }
                if status_str in status_map:
                    task.status = status_map[status_str]
                    if status_str in ("completing", "completed"):
                        from datetime import datetime
                        task.completed_at = datetime.utcnow()
                    db.commit()
        except Exception as e:
            db.rollback()
        finally:
            db.close()
