"""
Gripper control module for cargo handling operations.
Manages pneumatic gripper sequences with safety checks.
"""
import time
from enum import Enum, auto
from typing import Dict, Any, Optional
from core.logger import get_logger


class GripperState(Enum):
    """Gripper operational states."""
    IDLE = auto()
    APPROACHING = auto()
    GRIPPING = auto()
    HOLDING = auto()
    RELEASING = auto()
    ERROR = auto()


class GripperController:
    """
    Pneumatic gripper controller with state machine.
    Manages grip sequences with pressure feedback.
    """

    def __init__(self, config: Dict[str, Any]):
        self.logger = get_logger("Control.Gripper")

        self.max_pressure = config.get("max_pressure_bar", 6.0)
        self.max_force = config.get("max_grip_force_n", 200.0)
        self.grip_width = config.get("grip_width_m", 0.4)
        self.force_per_bar = config.get("grip_force_per_bar", 15.0)

        self.state = GripperState.IDLE
        self.current_pressure = 0.0
        self.current_force = 0.0
        self.is_holding = False
        self.payload_weight = 0.0
        self.payload_detected = False

        self._state_time = 0.0
        self._grip_start_time = 0.0
        self._grip_timeout = 5.0

        self.logger.info("Gripper controller initialized")

    def grip(self, target_pressure: Optional[float] = None) -> bool:
        """
        Start grip sequence.

        Args:
            target_pressure: Target pressure in bar (default 80% of max)

        Returns:
            True if grip sequence started successfully
        """
        if self.state in [GripperState.GRIPPING, GripperState.HOLDING]:
            self.logger.warning("Already gripping")
            return False

        target = target_pressure or self.max_pressure * 0.8
        self.current_pressure = min(target, self.max_pressure)
        self.state = GripperState.GRIPPING
        self._grip_start_time = time.monotonic()

        self.logger.info(f"Grip started: target={self.current_pressure:.1f} bar")
        return True

    def release(self) -> bool:
        """Release grip."""
        if self.state == GripperState.IDLE:
            return True

        self.state = GripperState.RELEASING
        self.current_pressure = 0.0
        self.current_force = 0.0
        self.is_holding = False
        self.payload_weight = 0.0

        self.logger.info("Gripper released")
        return True

    def update(self, dt: float) -> Dict[str, Any]:
        """
        Update gripper state machine.

        Returns:
            Current state info
        """
        now = time.monotonic()

        if self.state == GripperState.GRIPPING:
            # Check if pressure reached
            if self.current_force >= self.current_pressure * self.force_per_bar * 0.9:
                self.state = GripperState.HOLDING
                self.is_holding = True
                self.logger.info("Grip confirmed - holding payload")
            elif now - self._grip_start_time > self._grip_timeout:
                self.state = GripperState.ERROR
                self.logger.error("Grip timeout!")

        elif self.state == GripperState.RELEASING:
            if self.current_pressure <= 0.1:
                self.state = GripperState.IDLE
                self.logger.info("Release complete")

        # Update force based on pressure
        self.current_force = min(
            self.current_pressure * self.force_per_bar,
            self.max_force
        )

        return {
            "state": self.state.name,
            "pressure_bar": round(self.current_pressure, 2),
            "force_n": round(self.current_force, 1),
            "is_holding": self.is_holding,
            "payload_weight_kg": round(self.payload_weight, 2),
            "can_lift": self.current_force > self.payload_weight * 9.81 * 1.5
        }

    def set_payload_weight(self, weight_kg: float):
        """Set expected payload weight for force calculation."""
        self.payload_weight = weight_kg
        self.logger.debug(f"Payload weight set: {weight_kg}kg")

    def is_ready(self) -> bool:
        """Check if gripper is ready for operation."""
        return self.state == GripperState.IDLE

    def is_holding_payload(self) -> bool:
        """Check if gripper is currently holding payload."""
        return self.state == GripperState.HOLDING and self.is_holding

    def reset(self):
        """Reset gripper to idle state."""
        self.state = GripperState.IDLE
        self.current_pressure = 0.0
        self.current_force = 0.0
        self.is_holding = False
        self.payload_weight = 0.0
