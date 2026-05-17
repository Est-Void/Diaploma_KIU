"""
Movement control module with center of mass compensation.
Manages robot motion through velocity commands and stability control.
"""
import math
import numpy as np
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass
from core.logger import get_logger
from core.balancer import BalancerController


@dataclass
class VelocityCommand:
    """Velocity command for robot."""
    linear_x: float = 0.0   # m/s
    angular_z: float = 0.0  # rad/s
    duration: float = 0.0   # seconds


@dataclass
class RobotPose:
    """Robot 2D pose."""
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0
    v: float = 0.0
    w: float = 0.0


class MovementController:
    """
    Movement controller with kinematic model and CoM compensation.
    Converts velocity commands to wheel speeds with stability limits.
    """

    def __init__(self, config: Dict[str, Any]):
        self.logger = get_logger("Control.Movement")

        self.wheelbase = config.get("wheelbase_m", 0.45)
        self.track_width = config.get("track_width_m", 0.32)
        self.wheel_diameter = config.get("wheel_diameter_m", 0.15)
        self.max_speed = config.get("max_speed_mps", 1.2)
        self.max_angular = config.get("max_angular_speed_rps", 1.5)

        self.pose = RobotPose()
        self.target_velocity = VelocityCommand()
        self._emergency_stop = False
        self._stability_limit = 1.0

        self.logger.info("Movement controller initialized")

    def set_velocity(self, linear_x: float, angular_z: float):
        """
        Set target velocity with limits and stability scaling.

        Args:
            linear_x: Forward speed in m/s
            angular_z: Rotation speed in rad/s
        """
        if self._emergency_stop:
            self.target_velocity = VelocityCommand(0, 0)
            return

        # Apply limits
        linear_x = max(-self.max_speed, min(self.max_speed, linear_x))
        linear_x *= self._stability_limit

        angular_z = max(-self.max_angular, min(self.max_angular, angular_z))
        angular_z *= self._stability_limit

        self.target_velocity = VelocityCommand(linear_x, angular_z)

    def update(self, dt: float, imu_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Update robot state with velocity command.

        Returns:
            Dict with wheel speeds, pose, and status
        """
        v = self.target_velocity.linear_x
        w = self.target_velocity.angular_z

        # Differential drive kinematics
        v_left, v_right = self._compute_wheel_speeds(v, w)

        # Update pose (odometry integration)
        self.pose.v = (v_left + v_right) / 2.0
        self.pose.w = (v_right - v_left) / self.track_width

        # Integrate
        if abs(w) > 0.01:
            # Circular arc
            R = v / w
            self.pose.x += R * (math.sin(self.pose.theta + w * dt) - math.sin(self.pose.theta))
            self.pose.y += -R * (math.cos(self.pose.theta + w * dt) - math.cos(self.pose.theta))
            self.pose.theta += w * dt
        else:
            # Straight line
            self.pose.x += v * math.cos(self.pose.theta) * dt
            self.pose.y += v * math.sin(self.pose.theta) * dt

        # Normalize theta
        self.pose.theta = self._normalize_angle(self.pose.theta)

        return {
            "pose": {
                "x": round(self.pose.x, 4),
                "y": round(self.pose.y, 4),
                "theta": round(self.pose.theta, 6),
                "theta_deg": round(math.degrees(self.pose.theta), 2)
            },
            "velocity": {
                "linear": round(v, 3),
                "angular": round(w, 3)
            },
            "wheel_speeds": {
                "left_mps": round(v_left, 3),
                "right_mps": round(v_right, 3),
                "left_rpm": round(v_left / (math.pi * self.wheel_diameter) * 60, 1),
                "right_rpm": round(v_right / (math.pi * self.wheel_diameter) * 60, 1)
            },
            "stability_limit": round(self._stability_limit, 2)
        }

    def _compute_wheel_speeds(self, v: float, w: float) -> Tuple[float, float]:
        """Compute left and right wheel speeds from velocity command."""
        v_left = v - w * self.track_width / 2.0
        v_right = v + w * self.track_width / 2.0
        return v_left, v_right

    def apply_stability_limit(self, stability_score: float):
        """Scale maximum speed based on stability score."""
        self._stability_limit = 0.3 + 0.7 * stability_score
        if stability_score < 0.5:
            self.logger.warning(f"Low stability: limiting speed to {self._stability_limit:.0%}")

    def emergency_stop(self):
        """Trigger emergency stop."""
        self._emergency_stop = True
        self.target_velocity = VelocityCommand(0, 0)
        self.logger.warning("EMERGENCY STOP activated")

    def clear_emergency(self):
        """Clear emergency stop."""
        self._emergency_stop = False
        self.logger.info("Emergency stop cleared")

    def reset_odometry(self):
        """Reset pose to origin."""
        self.pose = RobotPose()
        self.logger.info("Odometry reset")

    @staticmethod
    def _normalize_angle(angle: float) -> float:
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle

    def get_pose(self) -> Dict[str, float]:
        return {
            "x": round(self.pose.x, 4),
            "y": round(self.pose.y, 4),
            "theta": round(self.pose.theta, 6)
        }
