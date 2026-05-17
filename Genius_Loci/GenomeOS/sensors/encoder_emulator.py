"""
Encoder emulator with configurable noise for odometry testing.
"""
import random
import math
from typing import Dict, Any
from core.logger import get_logger


class EncoderEmulator:
    """Emulates wheel encoders with Gaussian noise and slip simulation."""

    def __init__(self, ticks_per_rev: int = 1024, wheel_diameter_m: float = 0.15,
                 noise_std: float = 2.0, slip_prob: float = 0.02):
        self.logger = get_logger("Sensors.Encoder")
        self.ticks_per_rev = ticks_per_rev
        self.wheel_circumference = math.pi * wheel_diameter_m
        self.noise_std = noise_std
        self.slip_prob = slip_prob
        self._total_ticks = 0
        self._total_distance = 0.0
        self._last_speed = 0.0

    def update(self, true_speed_mps: float, dt: float) -> Dict[str, Any]:
        """Generate encoder reading based on true speed."""
        distance = true_speed_mps * dt

        # Add noise
        noisy_distance = distance + random.gauss(0, self.noise_std / self.ticks_per_rev * self.wheel_circumference)

        # Simulate slip
        if random.random() < self.slip_prob:
            noisy_distance *= random.uniform(0.85, 0.98)
            self.logger.debug("Wheel slip detected")

        ticks = int(noisy_distance / self.wheel_circumference * self.ticks_per_rev)
        self._total_ticks += ticks
        self._total_distance += noisy_distance
        self._last_speed = true_speed_mps

        return {
            "ticks": ticks,
            "total_ticks": self._total_ticks,
            "speed_mps": round(true_speed_mps + random.gauss(0, self.noise_std * 0.01), 3),
            "total_distance_m": round(self._total_distance, 4)
        }

    def reset(self):
        self._total_ticks = 0
        self._total_distance = 0.0
        self._last_speed = 0.0
