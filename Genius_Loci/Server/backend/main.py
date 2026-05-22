"""
FastAPI server for Genius Loci central dispatch system.
Manages robots, tasks, maps, and provides WebSocket real-time updates.
"""
from fastapi import FastAPI, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import uvicorn
from typing import Optional
import json

from app.models.database import engine, Base, get_db, SessionLocal, User, UserRole
from app.routers import auth, robots, tasks, maps, logs
from app.services.websocket_manager import WebSocketManager
from app.services.dispatcher import TaskDispatcher
from core.logger import setup_logging
import config as cfg

# Setup logging
setup_logging()

# Create database tables
Base.metadata.create_all(bind=engine)

# Seed default users if database is empty
def _seed_users():
    """Create default admin and operator accounts."""
    import bcrypt
    db = SessionLocal()
    try:
        if db.query(User).count() == 0:
            db.add(User(
                username="admin",
                email="admin@genius-loci.local",
                hashed_password=bcrypt.hashpw("admin".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                role=UserRole.ADMIN,
                is_active=True
            ))
            db.add(User(
                username="operator",
                email="operator@genius-loci.local",
                hashed_password=bcrypt.hashpw("operator".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
                role=UserRole.OPERATOR,
                is_active=True
            ))
            db.commit()
            print("[Seed] Default users created: admin/admin, operator/operator")
    finally:
        db.close()

_seed_users()

# Seed demo tasks
import uuid as _uuid
from datetime import datetime as _dt

def _seed_demo_tasks():
    """Create demo transport tasks for the warehouse."""
    from app.models.database import Task as TaskModel, TaskStatus
    db = SessionLocal()
    try:
        if db.query(TaskModel).count() > 0:
            return
        demo_tasks = [
            {"pickup": (-70, -60), "dropoff": (70, 60), "desc": "Box of electronics", "weight": 15.0},
            {"pickup": (60, -50), "dropoff": (-60, 70), "desc": "Pallet of spare parts", "weight": 45.0},
            {"pickup": (-80, 70), "dropoff": (50, -70), "desc": "Raw materials bundle", "weight": 30.0},
            {"pickup": (20, -80), "dropoff": (-40, 80), "desc": "Packaging supplies", "weight": 8.0},
            {"pickup": (-30, 80), "dropoff": (80, -20), "desc": "Finished goods crate", "weight": 22.0},
            {"pickup": (80, 40), "dropoff": (-70, -40), "desc": "Tools & equipment", "weight": 12.0},
            {"pickup": (-85, -85), "dropoff": (85, 85), "desc": "Priority shipment", "weight": 35.0},
            {"pickup": (75, 10), "dropoff": (-75, -10), "desc": "Medical supplies", "weight": 5.0},
        ]
        for i, t in enumerate(demo_tasks):
            task = TaskModel(
                task_id=f"TASK-{i+1:04d}",
                type="transport",
                status=TaskStatus.PENDING,
                pickup_x=t["pickup"][0], pickup_y=t["pickup"][1],
                dropoff_x=t["dropoff"][0], dropoff_y=t["dropoff"][1],
                priority=(i % 3) + 1,
                payload_description=t["desc"],
                payload_weight_kg=t["weight"],
                created_at=_dt.utcnow()
            )
            db.add(task)
        db.commit()
        print(f"[Seed] {len(demo_tasks)} demo tasks created")
    finally:
        db.close()

_seed_demo_tasks()

# WebSocket manager
ws_manager = WebSocketManager()
dispatcher = TaskDispatcher(ws_manager)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    dispatcher.start()
    yield
    # Shutdown
    dispatcher.stop()


app = FastAPI(
    title="Genius Loci Dispatch Server",
    description="Central dispatch and monitoring API for Genius Loci robot fleet",
    version="0.2.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=cfg.SERVER_CONFIG["cors_origins"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(robots.router, prefix="/api/v1/robots", tags=["Robots"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["Tasks"])
app.include_router(maps.router, prefix="/api/v1/maps", tags=["Maps"])
app.include_router(logs.router, prefix="/api/v1/logs", tags=["Logs"])


@app.get("/")
async def root():
    return {
        "name": "Genius Loci Dispatch Server",
        "version": "0.2.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "robots_connected": ws_manager.robot_count}


# WebSocket endpoints
@app.websocket("/ws/robot/{robot_id}")
async def robot_websocket(websocket: WebSocket, robot_id: str):
    """WebSocket endpoint for robot connections."""
    await ws_manager.connect_robot(websocket, robot_id)
    try:
        while True:
            data = await websocket.receive_json()
            await ws_manager.handle_robot_message(robot_id, data)
    except WebSocketDisconnect:
        await ws_manager.disconnect_robot(robot_id)


@app.websocket("/ws/client")
async def client_websocket(websocket: WebSocket):
    """WebSocket endpoint for web client connections."""
    await ws_manager.connect_client(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await ws_manager.handle_client_message(websocket, data)
    except WebSocketDisconnect:
        await ws_manager.disconnect_client(websocket)


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=cfg.SERVER_CONFIG["host"],
        port=cfg.SERVER_CONFIG["port"]
    )
