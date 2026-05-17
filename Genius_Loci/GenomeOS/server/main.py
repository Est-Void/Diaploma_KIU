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

from server.app.models.database import engine, Base, get_db, SessionLocal
from server.app.routers import auth, robots, tasks, maps, logs
from server.app.services.websocket_manager import WebSocketManager
from server.app.services.dispatcher import TaskDispatcher
from core.logger import setup_logging
import config.hw_config as cfg

# Setup logging
setup_logging()

# Create database tables
Base.metadata.create_all(bind=engine)

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
