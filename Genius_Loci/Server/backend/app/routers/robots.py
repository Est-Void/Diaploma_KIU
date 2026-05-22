"""
Robot management router.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.database import get_db, Robot
from app.schemas.schemas import RobotCreate, RobotUpdate, RobotResponse

router = APIRouter()


@router.get("", response_model=list)
async def list_robots(status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(Robot)
    if status:
        query = query.filter(Robot.status == status)
    robots = query.all()
    return [{
        "id": r.id, "robot_id": r.robot_id, "name": r.name,
        "status": r.status.value if hasattr(r.status, 'value') else r.status,
        "current_x": r.current_x, "current_y": r.current_y,
        "current_theta": r.current_theta, "battery_percent": r.battery_percent,
        "current_task_id": r.current_task_id, "last_seen": r.last_seen,
        "config": r.config or {}
    } for r in robots]


@router.post("")
async def register_robot(robot: RobotCreate, db: Session = Depends(get_db)):
    existing = db.query(Robot).filter(Robot.robot_id == robot.robot_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Robot already registered")

    r = Robot(robot_id=robot.robot_id, name=robot.name, config=robot.config)
    db.add(r)
    db.commit()
    db.refresh(r)
    return {"id": r.id, "robot_id": r.robot_id, "name": r.name}


@router.get("/{robot_id}")
async def get_robot(robot_id: str, db: Session = Depends(get_db)):
    robot = db.query(Robot).filter(Robot.robot_id == robot_id).first()
    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found")
    return {
        "id": robot.id, "robot_id": robot.robot_id, "name": robot.name,
        "status": robot.status.value if hasattr(robot.status, 'value') else robot.status,
        "current_x": robot.current_x, "current_y": robot.current_y,
        "current_theta": robot.current_theta, "battery_percent": robot.battery_percent,
        "current_task_id": robot.current_task_id, "config": robot.config or {}
    }


@router.patch("/{robot_id}")
async def update_robot(robot_id: str, update: RobotUpdate, db: Session = Depends(get_db)):
    robot = db.query(Robot).filter(Robot.robot_id == robot_id).first()
    if not robot:
        raise HTTPException(status_code=404, detail="Robot not found")

    if update.name is not None:
        robot.name = update.name
    if update.status is not None:
        robot.status = update.status
    if update.x is not None:
        robot.current_x = update.x
    if update.y is not None:
        robot.current_y = update.y
    if update.theta is not None:
        robot.current_theta = update.theta
    if update.battery_percent is not None:
        robot.battery_percent = update.battery_percent

    db.commit()
    return {"status": "updated"}
