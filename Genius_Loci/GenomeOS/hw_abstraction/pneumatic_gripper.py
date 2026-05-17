"""
Simulated pneumatic gripper with pressure-based force control.
"""
from typing import Dict, Any
from hw_abstraction.base_node import BaseNode


class PneumaticGripper(BaseNode):
    """Simulated pneumatic gripper with realistic pressure dynamics."""

    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self._pressure = 0.0
        self._target_pressure = 0.0
        self._is_gripping = False
        self.max_pressure = config["max_pressure_bar"]
        self.pump_rate = config["pump_rate"]
        self.leak_rate = config["leak_rate"]
        self.force_per_bar = config["grip_force_per_bar"]
        self.max_force = config.get("max_grip_force_n", 200.0)

    def read(self) -> Dict[str, Any]:
        current_force = min(self._pressure * self.force_per_bar, self.max_force)
        return {
            "pressure_bar": round(self._pressure, 2),
            "force_n": round(current_force, 1),
            "is_gripping": self._is_gripping,
            "active": self.is_active
        }

    def write(self, command: Dict[str, Any]) -> bool:
        action = command.get("action", "hold")
        if action == "grip":
            target = command.get("pressure", self.max_pressure * 0.8)
            self._target_pressure = min(target, self.max_pressure)
            self._is_gripping = True
        elif action == "release":
            self._target_pressure = 0.0
            self._is_gripping = False
        elif action == "hold":
            pass
        return True

    def update(self, dt: float):
        super().update(dt)
        if self._pressure < self._target_pressure:
            self._pressure = min(self._target_pressure, 
                                self._pressure + self.pump_rate * dt)
        elif self._pressure > self._target_pressure:
            self._pressure = max(self._target_pressure, 
                                self._pressure - self.pump_rate * dt * 2)
        # Natural leak
        self._pressure = max(0, self._pressure - self.leak_rate * dt)

    def reset(self):
        self._pressure = 0.0
        self._target_pressure = 0.0
        self._is_gripping = False
