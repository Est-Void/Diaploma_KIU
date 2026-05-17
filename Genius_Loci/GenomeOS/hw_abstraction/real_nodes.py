"""
Stubs for real hardware nodes (Raspberry Pi / physical robot).
These raise errors when real hardware is not available.
"""
from core.logger import get_logger

logger = get_logger("HW.RealNodes")


class HardwareInitializationError(Exception):
    """Raised when real hardware cannot be initialized."""
    pass


class RealLimbMotor:
    def __init__(self, *args, **kwargs):
        raise HardwareInitializationError("Real Limb Motor not connected. Run in simulation mode.")


class RealWheelMotor:
    def __init__(self, *args, **kwargs):
        raise HardwareInitializationError("Real Wheel Motor not connected. Run in simulation mode.")


class RealPneumaticGripper:
    def __init__(self, *args, **kwargs):
        raise HardwareInitializationError("Real Pneumatic Gripper not connected. Run in simulation mode.")


class RealPositionSensor:
    def __init__(self, *args, **kwargs):
        raise HardwareInitializationError("Real Position Sensor not connected. Run in simulation mode.")
