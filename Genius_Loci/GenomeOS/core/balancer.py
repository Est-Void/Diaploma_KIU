"""
Balancer controller with center of mass compensation.
Manages robot stability during movement and payload handling.
"""
import math
from typing import Dict, Optional
from core.pid import PIDController
from core.logger import get_logger


class BalancerController:
    """
    Balancer with PID-based pitch/roll control and CoM compensation.

    Controls 4 limbs to maintain balance with payload.
    """

    def __init__(self, config: dict):
        self.config = config
        self.logger = get_logger("Core.Balancer")

        self.pid_pitch = PIDController(
            kp=config["pitch_kp"],
            ki=config["pitch_ki"],
            kd=config["pitch_kd"],
            limits=(-config["max_limb_angle"], config["max_limb_angle"]),
            integral_limits=(-20, 20)
        )
        self.pid_roll = PIDController(
            kp=config["roll_kp"],
            ki=config["roll_ki"],
            kd=config["roll_kd"],
            limits=(-config["max_limb_angle"], config["max_limb_angle"]),
            integral_limits=(-15, 15)
        )

        self.wheelbase = 0.4 #config["wheelbase_m"]
        self.track_width = 0.3 #config["track_width_m"]
        self.gripper_leverage = 0.15 #config["gripper_leverage_m"]
        self.speed_to_angle = config["speed_to_angle_gain"]
        self.emergency_threshold = config.get("emergency_tilt_threshold_deg", 25.0)

        self._emergency_mode = False
        self._stability_score = 1.0

    def update(
        self,
        dt: float,
        target_speed: float,
        imu_data: Dict,
        payload_state: Dict
    ) -> Dict:
        """
        Compute target angles for 4 limbs.

        Returns dict with limb angles and stability status.
        """
        pitch = imu_data.get("pitch", 0.0)
        roll = imu_data.get("roll", 0.0)
        payload_weight = payload_state.get("weight", 0.0)
        is_held = payload_state.get("is_held", False)

        pitch_deg = math.degrees(pitch)
        roll_deg = math.degrees(roll)

        # Emergency check
        if abs(pitch_deg) > self.emergency_threshold or abs(roll_deg) > self.emergency_threshold:
            self._emergency_mode = True
            self.logger.warning(f"EMERGENCY: Tilt exceeded! pitch={pitch_deg:.1f} roll={roll_deg:.1f}")
            return self._emergency_stop()
        else:
            self._emergency_mode = False

        # Speed feedforward
        speed_ff = target_speed * self.speed_to_angle

        # Payload compensation
        payload_ff = 0.0
        if is_held and payload_weight > 0:
            payload_ff = -math.degrees(
                math.atan2(
                    payload_weight * self.gripper_leverage,
                    (payload_weight + 30) * self.wheelbase * 0.5
                )
            )
            self.logger.debug(f"Payload compensation: {payload_ff:.2f} deg for {payload_weight}kg")

        target_pitch = speed_ff + payload_ff

        # PID corrections
        pitch_correction = self.pid_pitch.compute(target_pitch, pitch_deg, dt)
        roll_correction = self.pid_roll.compute(0.0, roll_deg, dt)

        # Distribute angles to 4 limbs (FL, FR, RL, RR)
        # Front limbs counter pitch, rear limbs support
        limb_angles = {
            "limb_fl": pitch_correction + roll_correction,
            "limb_fr": pitch_correction - roll_correction,
            "limb_rl": -pitch_correction * 0.3 + roll_correction,
            "limb_rr": -pitch_correction * 0.3 - roll_correction,
        }

        # Calculate stability score
        self._stability_score = 1.0 - min(1.0, (
            abs(pitch_deg) + abs(roll_deg)
        ) / (self.emergency_threshold * 2))

        if is_held and payload_weight > 40:
            self._stability_score *= 0.7

        return {
            "limb_angles": limb_angles,
            "stability_score": self._stability_score,
            "emergency": False,
            "pitch_correction": pitch_correction,
            "roll_correction": roll_correction,
            "speed_ff": speed_ff,
            "payload_ff": payload_ff
        }

    def _emergency_stop(self) -> Dict:
        """Return emergency stop configuration."""
        return {
            "limb_angles": {"limb_fl": 0, "limb_fr": 0, "limb_rl": 0, "limb_rr": 0},
            "stability_score": 0.0,
            "emergency": True,
            "pitch_correction": 0,
            "roll_correction": 0,
            "speed_ff": 0,
            "payload_ff": 0
        }

    @property
    def is_emergency(self) -> bool:
        return self._emergency_mode

    @property
    def stability_score(self) -> float:
        return self._stability_score
