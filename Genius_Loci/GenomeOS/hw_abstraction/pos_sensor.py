"""
Simulated position sensor with configurable noise.
"""
import time
from typing import Dict, Any
from hw_abstraction.base_node import BaseNode


class PositionSensor(BaseNode):
    """Simulated position/angle sensor with realistic noise."""

    def __init__(self, name: str, config: Dict[str, Any], motor_node=None):
        super().__init__(name, config)
        self.noise_std = config["noise_std_dev"]
        self.delay_ms = config["update_delay_ms"]
        self._motor = motor_node
        self._buffer = []
        self._last_reading = 0.0

    def read(self) -> Dict[str, Any]:
        if self._motor and self._motor.is_active:
            true_value = self._motor.read().get("angle_deg", 0.0)
        else:
            true_value = self._last_reading

        noisy = self._add_noise(true_value, self.noise_std)
        self._last_reading = noisy

        return {
            "angle_deg": round(noisy, 2),
            "true_value": round(true_value, 2),
            "noise_std": self.noise_std,
            "active": self.is_active
        }

    def write(self, command: Dict[str, Any]) -> bool:
        return False  # Sensors are read-only

    def reset(self):
        self._last_reading = 0.0
        self._buffer.clear()

    def update(self, dt: float):
        super().update(dt)
