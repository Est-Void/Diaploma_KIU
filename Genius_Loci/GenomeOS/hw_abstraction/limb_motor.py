"""
Simulated limb motor for robot legs.
"""
from typing import Dict, Any
from hw_abstraction.base_node import BaseNode


class LimbMotor(BaseNode):
    """Simulated limb motor with angle control."""

    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self._current_angle = 0.0
        self._target_angle = 0.0
        self.max_angle = config["max_angle_deg"]
        self.max_speed = config["max_speed_deg_per_sec"]
        self.inertia = config["inertia_factor"]
        self.friction = config["friction_coeff"]
        self.gravity = config["gravity_effect"]

    def read(self) -> Dict[str, Any]:
        return {
            "angle_deg": self._current_angle,
            "target_deg": self._target_angle,
            "active": self.is_active
        }

    def write(self, command: Dict[str, Any]) -> bool:
        target = command.get("angle_deg", 0.0)
        self._target_angle = max(-self.max_angle, min(self.max_angle, target))
        return True

    def update(self, dt: float):
        super().update(dt)
        error = self._target_angle - self._current_angle
        speed = error * (1 - self.inertia) * 10
        speed = max(-self.max_speed, min(self.max_speed, speed))
        self._current_angle += speed * dt
        self._current_angle *= (1 - self.friction * dt)

    def reset(self):
        self._current_angle = 0.0
        self._target_angle = 0.0
