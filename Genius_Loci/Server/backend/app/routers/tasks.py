"""
Task management router.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.models.database import get_db, Task as TaskModel, TaskStatus
from app.schemas.schemas import TaskCreate, TaskUpdate, TaskResponse
from app.services.dispatcher import TaskDispatcher

router = APIRouter()


@router.get("")
async def list_tasks(status: Optional[str] = None, robot_id: Optional[int] = None, 
                     db: Session = Depends(get_db)):
    query = db.query(TaskModel)
    if status:
        query = query.filter(TaskModel.status == status)
    if robot_id:
        query = query.filter(TaskModel.robot_id == robot_id)
    tasks = query.order_by(TaskModel.created_at.desc()).all()
    return [{
        "id": t.id, "task_id": t.task_id, "type": t.type,
        "status": t.status.value if hasattr(t.status, 'value') else t.status,
        "pickup_x": t.pickup_x, "pickup_y": t.pickup_y,
        "dropoff_x": t.dropoff_x, "dropoff_y": t.dropoff_y,
        "priority": t.priority, "payload_description": t.payload_description,
        "payload_weight_kg": t.payload_weight_kg,
        "robot_id": t.robot_id, "created_at": t.created_at,
        "assigned_at": t.assigned_at, "started_at": t.started_at,
        "completed_at": t.completed_at
    } for t in tasks]


@router.post("")
async def create_task(task: TaskCreate, db: Session = Depends(get_db)):
    import uuid
    from app.models.database import Task as TaskModel

    task_id = f"TASK-{uuid.uuid4().hex[:8].upper()}"
    t = TaskModel(
        task_id=task_id,
        type="transport",
        pickup_x=task.pickup_x,
        pickup_y=task.pickup_y,
        dropoff_x=task.dropoff_x,
        dropoff_y=task.dropoff_y,
        priority=task.priority,
        payload_description=task.payload_description,
        payload_weight_kg=task.payload_weight_kg
    )
    db.add(t)
    db.commit()
    db.refresh(t)

    return {"task_id": task_id, "status": "pending"}


@router.get("/{task_id}")
async def get_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(TaskModel).filter(TaskModel.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "id": task.id, "task_id": task.task_id,
        "status": task.status.value if hasattr(task.status, 'value') else task.status,
        "pickup_x": task.pickup_x, "pickup_y": task.pickup_y,
        "dropoff_x": task.dropoff_x, "dropoff_y": task.dropoff_y,
        "priority": task.priority
    }


@router.patch("/{task_id}")
async def update_task(task_id: str, update: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(TaskModel).filter(TaskModel.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if update.status:
        task.status = update.status
    if update.robot_id is not None:
        task.robot_id = update.robot_id

    db.commit()
    return {"status": "updated"}


@router.delete("/{task_id}")
async def cancel_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(TaskModel).filter(TaskModel.task_id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = TaskStatus.CANCELLED
    db.commit()
    return {"status": "cancelled"}
