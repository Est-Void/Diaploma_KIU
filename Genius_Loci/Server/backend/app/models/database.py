"""
SQLAlchemy database models for Genius Loci server.
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime,     ForeignKey, JSON, Boolean, Text, Index, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from datetime import datetime
import enum
import config as cfg

Base = declarative_base()
engine = create_engine(cfg.SERVER_CONFIG["database_url"])
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class UserRole(str, enum.Enum):
    OPERATOR = "operator"
    ADMIN = "admin"


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    ACCEPTED = "accepted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class RobotStatus(str, enum.Enum):
    FREE = "free"
    BUSY = "busy"
    CHARGING = "charging"
    ERROR = "error"
    OFFLINE = "offline"


class User(Base):
    """User account for web interface access."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.OPERATOR)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)


class Robot(Base):
    """Robot registration and state."""
    __tablename__ = "robots"

    id = Column(Integer, primary_key=True)
    robot_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    status = Column(Enum(RobotStatus), default=RobotStatus.OFFLINE)
    current_x = Column(Float, default=0.0)
    current_y = Column(Float, default=0.0)
    current_theta = Column(Float, default=0.0)
    battery_percent = Column(Float, default=100.0)
    current_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    last_seen = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    config = Column(JSON, default=dict)

    tasks = relationship("Task", back_populates="robot", foreign_keys="Task.robot_id")
    current_task = relationship("Task", foreign_keys=[current_task_id])

    __table_args__ = (Index('idx_robot_status', 'status'),)


class Task(Base):
    """Transport task definition."""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    task_id = Column(String(50), unique=True, nullable=False)
    type = Column(String(20), default="transport")
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING)

    # Locations (JSON for flexibility)
    pickup_x = Column(Float, nullable=False)
    pickup_y = Column(Float, nullable=False)
    dropoff_x = Column(Float, nullable=False)
    dropoff_y = Column(Float, nullable=False)

    priority = Column(Integer, default=1)  # 1=normal, 2=high, 3=critical
    payload_description = Column(String(255), nullable=True)
    payload_weight_kg = Column(Float, nullable=True)

    robot_id = Column(Integer, ForeignKey("robots.id"), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    assigned_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    robot = relationship("Robot", back_populates="tasks", foreign_keys=[robot_id])

    __table_args__ = (Index('idx_task_status', 'status'), Index('idx_task_robot', 'robot_id'))


class MapData(Base):
    """Stored warehouse map."""
    __tablename__ = "maps"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    resolution_m = Column(Float, default=0.05)
    width = Column(Integer)
    height = Column(Integer)
    origin_x = Column(Float, default=0.0)
    origin_y = Column(Float, default=0.0)
    grid_data = Column(Text)  # Hex-encoded occupancy grid
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    is_default = Column(Boolean, default=False)


class SystemLog(Base):
    """System event log."""
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    level = Column(String(10), default="INFO")
    source = Column(String(50))  # module name
    message = Column(Text)
    robot_id = Column(String(50), nullable=True)
    task_id = Column(String(50), nullable=True)
    extra = Column(JSON, default=dict)

    __table_args__ = (Index('idx_log_timestamp', 'timestamp'),)


class TelemetryRecord(Base):
    """Robot telemetry history."""
    __tablename__ = "telemetry"

    id = Column(Integer, primary_key=True)
    robot_id = Column(String(50), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    x = Column(Float)
    y = Column(Float)
    theta = Column(Float)
    linear_velocity = Column(Float)
    angular_velocity = Column(Float)
    battery_percent = Column(Float)
    status = Column(String(20))

    __table_args__ = (Index('idx_telemetry_robot_time', 'robot_id', 'timestamp'),)
