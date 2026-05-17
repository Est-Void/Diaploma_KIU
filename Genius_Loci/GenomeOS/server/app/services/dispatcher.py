"""
Task dispatcher for automatic task assignment to robots.
"""
import asyncio
import uuid
from typing import Optional, Dict, Any
from datetime import datetime
from core.logger import get_logger


class TaskDispatcher:
    """
    Automatic task dispatcher.
    Assigns pending tasks to available robots based on proximity.
    """

    def __init__(self, ws_manager):
        self.logger = get_logger("Server.Dispatcher")
        self.ws_manager = ws_manager
        self._running = False
        self._task_queue = asyncio.Queue()
        self._dispatch_task: Optional[asyncio.Task] = None
        self._check_interval = 5.0  # seconds

    def start(self):
        """Start dispatcher loop."""
        self._running = True
        self._dispatch_task = asyncio.create_task(self._dispatch_loop())
        self.logger.info("Task dispatcher started")

    def stop(self):
        """Stop dispatcher loop."""
        self._running = False
        if self._dispatch_task:
            self._dispatch_task.cancel()
        self.logger.info("Task dispatcher stopped")

    async def _dispatch_loop(self):
        """Main dispatch loop."""
        while self._running:
            try:
                await self._check_and_assign()
                await asyncio.sleep(self._check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Dispatch error: {e}")

    async def _check_and_assign(self):
        """Check for pending tasks and assign to available robots."""
        from server.app.models.database import SessionLocal
        from server.app.models.database import Task as TaskModel, Robot, TaskStatus, RobotStatus

        db = SessionLocal()
        try:
            # Find pending tasks
            pending_tasks = db.query(TaskModel).filter(
                TaskModel.status == TaskStatus.PENDING
            ).order_by(TaskModel.priority.desc(), TaskModel.created_at).all()

            # Find free robots
            free_robots = db.query(Robot).filter(
                Robot.status == RobotStatus.FREE
            ).all()

            for task in pending_tasks:
                if not free_robots:
                    break

                # Find closest robot
                best_robot = None
                best_distance = float('inf')

                for robot in free_robots:
                    dist = ((robot.current_x - task.pickup_x)**2 + 
                           (robot.current_y - task.pickup_y)**2)**0.5
                    if dist < best_distance:
                        best_distance = dist
                        best_robot = robot

                if best_robot:
                    # Assign task
                    task.status = TaskStatus.ASSIGNED
                    task.robot_id = best_robot.id
                    task.assigned_at = datetime.utcnow()
                    best_robot.status = RobotStatus.BUSY
                    best_robot.current_task_id = task.id

                    db.commit()
                    free_robots.remove(best_robot)

                    # Send to robot
                    await self.ws_manager.send_to_robot(
                        best_robot.robot_id,
                        {
                            "type": "execute_task",
                            "task": {
                                "id": task.task_id,
                                "pickup_x": task.pickup_x,
                                "pickup_y": task.pickup_y,
                                "dropoff_x": task.dropoff_x,
                                "dropoff_y": task.dropoff_y,
                                "payload_weight_kg": task.payload_weight_kg
                            }
                        }
                    )

                    self.logger.info(f"Task {task.task_id} assigned to robot {best_robot.robot_id}")

                    # Notify clients
                    await self.ws_manager.broadcast_to_clients({
                        "type": "task_assigned",
                        "task_id": task.task_id,
                        "robot_id": best_robot.robot_id
                    })

        finally:
            db.close()

    async def submit_task(self, task_data: Dict[str, Any]) -> str:
        """Submit a new task to the queue."""
        task_id = f"TASK-{uuid.uuid4().hex[:8].upper()}"

        from server.app.models.database import SessionLocal, Task as TaskModel

        db = SessionLocal()
        try:
            task = TaskModel(
                task_id=task_id,
                type="transport",
                pickup_x=task_data["pickup_x"],
                pickup_y=task_data["pickup_y"],
                dropoff_x=task_data["dropoff_x"],
                dropoff_y=task_data["dropoff_y"],
                priority=task_data.get("priority", 1),
                payload_description=task_data.get("payload_description"),
                payload_weight_kg=task_data.get("payload_weight_kg")
            )
            db.add(task)
            db.commit()

            self.logger.info(f"Task submitted: {task_id}")
            return task_id
        finally:
            db.close()
