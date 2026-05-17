"""
IMU (Inertial Measurement Unit) emulator with drift and noise.
"""
import random
import math
from typing import Dict, Any, Optional
from core.logger import get_logger


class IMUEmulator:
    """Emulates IMU with gyro drift, accelerometer noise, and vibration."""

    def __init__(self, drift_rate: float = 0.001, noise_std: float = 0.05,
                 update_rate_hz: float = 100):
        self.logger = get_logger("Sensors.IMU")
        self.drift_rate = drift_rate
        self.noise_std = noise_std
        self.update_rate_hz = update_rate_hz

        self._gyro_drift = [0.0, 0.0, 0.0]
        self._pitch = 0.0
        self._roll = 0.0
        self._yaw = 0.0
        self._accel = [0.0, 0.0, 9.81]
        self._angular_velocity = [0.0, 0.0, 0.0]
        self._time_accumulator = 0.0

    def update(self, true_pitch: float, true_roll: float, true_yaw: float,
               true_accel: Optional[list] = None, dt: float = 0.01) -> Dict[str, Any]:
        """Generate IMU reading based on true orientation."""
        # Update gyro drift
        for i in range(3):
            self._gyro_drift[i] += random.gauss(0, self.drift_rate * dt)

        # Calculate angular velocity (derivative + drift)
        self._angular_velocity = [
            random.gauss(0, self.noise_std) + self._gyro_drift[0],
            random.gauss(0, self.noise_std) + self._gyro_drift[1],
            random.gauss(0, self.noise_std) + self._gyro_drift[2]
        ]

        # Add noise to orientation
        self._pitch = true_pitch + self._gyro_drift[1] + random.gauss(0, self.noise_std * 0.5)
        self._roll = true_roll + self._gyro_drift[0] + random.gauss(0, self.noise_std * 0.5)
        self._yaw = true_yaw + self._gyro_drift[2] + random.gauss(0, self.noise_std * 0.5)

        # Accelerometer with gravity and noise
        true_accel = true_accel or [0.0, 0.0, 9.81]
        self._accel = [
            true_accel[0] + random.gauss(0, self.noise_std * 0.1),
            true_accel[1] + random.gauss(0, self.noise_std * 0.1),
            true_accel[2] + random.gauss(0, self.noise_std * 0.1)
        ]

        return {
            "pitch_rad": round(self._pitch, 6),
            "roll_rad": round(self._roll, 6),
            "yaw_rad": round(self._yaw, 6),
            "angular_velocity_rad_s": [round(v, 6) for v in self._angular_velocity],
            "acceleration_mps2": [round(a, 6) for a in self._accel],
            "temperature_c": round(25.0 + random.gauss(0, 1), 1)
        }

    def reset(self):
        self._gyro_drift = [0.0, 0.0, 0.0]
        self._pitch = self._roll = self._yaw = 0.0
        self._angular_velocity = [0.0, 0.0, 0.0]
