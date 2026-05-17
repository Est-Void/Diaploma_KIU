"""
Simulated wheel motor with realistic dynamics.
"""
import time
from typing import Dict, Any
from hw_abstraction.base_node import BaseNode


class WheelMotor(BaseNode):
    """Simulated wheel motor with inertia, friction, and load effects."""

    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self._current_rpm = 0.0
        self._target_rpm = 0.0
        self._current_angle = 0.0
        self._encoder_ticks = 0
        self._total_distance_m = 0.0

        self.max_rpm = config["max_rpm"]
        self.inertia = config["inertia_factor"]
        self.friction = config["rolling_resistance"]
        self.load_effect = config["load_effect"]
        self.encoder_resolution = config.get("encoder_ticks_per_rev", 1024)

    def read(self) -> Dict[str, Any]:
        """Return current motor state."""
        return {
            "rpm": self._current_rpm,
            "angle_deg": self._current_angle,
            "encoder_ticks": int(self._encoder_ticks),
            "distance_m": round(self._total_distance_m, 4),
            "active": self.is_active
        }

    def write(self, command: Dict[str, Any]) -> bool:
        """Set target RPM."""
        target = command.get("rpm", 0.0)
        self._target_rpm = max(-self.max_rpm, min(self.max_rpm, target))
        return True

    def update(self, dt: float):
        """Update motor physics simulation."""
        super().update(dt)

        # Apply inertia
        error = self._target_rpm - self._current_rpm
        self._current_rpm += error * (1 - self.inertia) * dt * 5

        # Apply friction
        self._current_rpm *= (1 - self.friction * dt)

        # Update encoder and distance
        wheel_circumference = 3.14159 * 0.15  # 150mm diameter
        revs_per_sec = self._current_rpm / 60.0
        self._encoder_ticks += revs_per_sec * self.encoder_resolution * dt
        self._total_distance_m += revs_per_sec * wheel_circumference * dt
        self._current_angle += self._current_rpm * 6.0 * dt  # rpm * 6 = deg/sec

    def reset(self):
        self._current_rpm = 0.0
        self._target_rpm = 0.0
        self._current_angle = 0.0
        self._encoder_ticks = 0
        self._total_distance_m = 0.0
