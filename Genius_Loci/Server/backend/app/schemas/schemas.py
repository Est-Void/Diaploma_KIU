"""
Pydantic schemas for request/response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============ AUTH SCHEMAS ============

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400

class UserLogin(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    email: Optional[str] = None
    role: str = "operator"

class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str]
    role: str
    is_active: bool
    created_at: datetime


# ============ ROBOT SCHEMAS ============

class RobotCreate(BaseModel):
    robot_id: str
    name: str
    config: Optional[Dict[str, Any]] = {}

class RobotUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    theta: Optional[float] = None
    battery_percent: Optional[float] = None

class RobotResponse(BaseModel):
    id: int
    robot_id: str
    name: str
    status: str
    current_x: float
    current_y: float
    current_theta: float
    battery_percent: float
    current_task_id: Optional[int]
    last_seen: datetime
    config: Dict[str, Any]

class RobotList(BaseModel):
    robots: List[RobotResponse]
    total: int


# ============ TASK SCHEMAS ============

class TaskCreate(BaseModel):
    pickup_x: float
    pickup_y: float
    dropoff_x: float
    dropoff_y: float
    priority: int = 1
    payload_description: Optional[str] = None
    payload_weight_kg: Optional[float] = None

class TaskUpdate(BaseModel):
    status: Optional[str] = None
    robot_id: Optional[int] = None

class TaskResponse(BaseModel):
    id: int
    task_id: str
    type: str
    status: str
    pickup_x: float
    pickup_y: float
    dropoff_x: float
    dropoff_y: float
    priority: int
    payload_description: Optional[str]
    payload_weight_kg: Optional[float]
    robot_id: Optional[int]
    created_at: datetime
    assigned_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]

class TaskList(BaseModel):
    tasks: List[TaskResponse]
    total: int


# ============ MAP SCHEMAS ============

class MapCreate(BaseModel):
    name: str
    description: Optional[str] = None
    resolution_m: float = 0.05
    width: int
    height: int
    origin_x: float = 0.0
    origin_y: float = 0.0
    grid_data: str  # hex-encoded

class MapResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    resolution_m: float
    width: int
    height: int
    origin_x: float
    origin_y: float
    created_at: datetime
    is_default: bool


# ============ TELEMETRY SCHEMAS ============

class TelemetryMessage(BaseModel):
    robot_id: str
    timestamp: float
    pose: Dict[str, float]
    velocity: Dict[str, float]
    battery_percent: float
    status: str
    gripper_state: Optional[str] = None
    stability_score: Optional[float] = None
    has_payload: Optional[bool] = None
    payload_weight_kg: Optional[float] = None


# ============ LOG SCHEMAS ============

class LogEntry(BaseModel):
    level: str = "INFO"
    source: str
    message: str
    robot_id: Optional[str] = None
    task_id: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None

class LogFilter(BaseModel):
    level: Optional[str] = None
    source: Optional[str] = None
    robot_id: Optional[str] = None
    from_time: Optional[datetime] = None
    to_time: Optional[datetime] = None
    limit: int = 100
