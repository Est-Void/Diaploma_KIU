"""
Base node class for all hardware components.
Provides unified interface for simulated and real hardware.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from core.logger import get_logger
import random
import time


class BaseNode(ABC):
    """Abstract base class for all hardware nodes."""

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.is_active = False
        self.logger = get_logger(f"HW.{name}")
        self._simulated = True
        self._last_update = time.monotonic()

    @abstractmethod
    def read(self) -> Dict[str, Any]:
        """Read sensor data or current state."""
        pass

    @abstractmethod
    def write(self, command: Dict[str, Any]) -> bool:
        """Send command to actuator."""
        pass

    @abstractmethod
    def reset(self):
        """Reset node to initial state."""
        pass

    def update(self, dt: float):
        """Update simulation state."""
        self._last_update = time.monotonic()

    @property
    def is_simulated(self) -> bool:
        return self._simulated

    def _add_noise(self, value: float, std_dev: float) -> float:
        """Add Gaussian noise to value."""
        if std_dev <= 0:
            return value
        return value + random.gauss(0, std_dev)
