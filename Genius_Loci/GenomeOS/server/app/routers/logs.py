"""
System logs router.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from server.app.models.database import get_db, SystemLog

router = APIRouter()


@router.get("")
async def get_logs(
    level: Optional[str] = None,
    robot_id: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    query = db.query(SystemLog)
    if level:
        query = query.filter(SystemLog.level == level)
    if robot_id:
        query = query.filter(SystemLog.robot_id == robot_id)
    logs = query.order_by(SystemLog.timestamp.desc()).limit(limit).all()
    return [{
        "id": l.id, "timestamp": l.timestamp, "level": l.level,
        "source": l.source, "message": l.message,
        "robot_id": l.robot_id, "task_id": l.task_id
    } for l in logs]


@router.post("")
async def add_log(log_data: dict, db: Session = Depends(get_db)):
    log = SystemLog(
        level=log_data.get("level", "INFO"),
        source=log_data["source"],
        message=log_data["message"],
        robot_id=log_data.get("robot_id"),
        task_id=log_data.get("task_id"),
        extra=log_data.get("extra")
    )
    db.add(log)
    db.commit()
    return {"id": log.id}
