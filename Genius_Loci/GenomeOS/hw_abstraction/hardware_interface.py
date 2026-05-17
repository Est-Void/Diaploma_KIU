"""
Hardware Interface - unified access to all robot hardware.
Manages initialization of simulated or real hardware nodes.
"""
from typing import Dict, Any, Optional
from core.logger import get_logger

from hw_abstraction.limb_motor import LimbMotor
from hw_abstraction.wheel_motor import WheelMotor
from hw_abstraction.pneumatic_gripper import PneumaticGripper
from hw_abstraction.pos_sensor import PositionSensor


class HardwareInterface:
    """Central hardware management interface."""

    def __init__(self, config: Dict[str, Any], use_simulation: bool = True):
        self.logger = get_logger("HW.Interface")
        self.use_simulation = use_simulation
        self.nodes: Dict[str, Any] = {}
        self.config = config
        self._initialized = False

    def initialize(self):
        """Initialize all hardware nodes."""
        if self._initialized:
            return

        cfg = self.config

        if self.use_simulation:
            self.logger.info("Initializing SIMULATED hardware")
            self._init_simulated()
        else:
            self.logger.info("Initializing REAL hardware")
            self._init_real()

        self._initialized = True
        self.logger.info(f"Hardware initialized: {len(self.nodes)} nodes")

    def _init_simulated(self):
        """Create simulated hardware nodes."""
        cfg = self.config

        # 4 limb motors
        for i, name in enumerate(["FL", "FR", "RL", "RR"]):
            motor = LimbMotor(f"limb_{name}", cfg["limb_motor"])
            motor.is_active = True
            self.nodes[f"limb_{name}"] = motor
            self.nodes[f"limb_sensor_{name}"] = PositionSensor(
                f"limb_sens_{name}", cfg["pos_sensor"], motor
            )

        # 2 wheel motors (rear)
        for i in range(2):
            motor = WheelMotor(f"wheel_{i}", cfg["wheel_motor"])
            motor.is_active = True
            self.nodes[f"wheel_{i}"] = motor
            self.nodes[f"wheel_sensor_{i}"] = PositionSensor(
                f"wheel_sens_{i}", cfg["pos_sensor"], motor
            )

        # 2 pneumatic grippers
        for i in range(2):
            gripper = PneumaticGripper(f"gripper_{i}", cfg["pneumatic_gripper"])
            gripper.is_active = True
            self.nodes[f"gripper_{i}"] = gripper

    def _init_real(self):
        """Attempt to initialize real hardware (Raspberry Pi)."""
        try:
            from hw_abstraction.real_nodes import (
                RealLimbMotor, RealWheelMotor, 
                RealPneumaticGripper, RealPositionSensor,
                HardwareInitializationError
            )

            cfg = self.config
            self.logger.warning("Attempting REAL hardware initialization...")

            for i, name in enumerate(["FL", "FR", "RL", "RR"]):
                motor = RealLimbMotor(f"limb_{name}", cfg["limb_motor"])
                self.nodes[f"limb_{name}"] = motor

            for i in range(2):
                motor = RealWheelMotor(f"wheel_{i}", cfg["wheel_motor"])
                self.nodes[f"wheel_{i}"] = motor

            for i in range(2):
                gripper = RealPneumaticGripper(f"gripper_{i}", cfg["pneumatic_gripper"])
                self.nodes[f"gripper_{i}"] = gripper

        except HardwareInitializationError as e:
            self.logger.error(f"Real hardware init failed: {e}. Falling back to simulation.")
            self.use_simulation = True
            self._init_simulated()

    def get_node(self, name: str) -> Optional[Any]:
        """Get a hardware node by name."""
        return self.nodes.get(name)

    def read_all(self) -> Dict[str, Dict]:
        """Read all active nodes."""
        return {name: node.read() for name, node in self.nodes.items() if node.is_active}

    def write_node(self, name: str, command: Dict) -> bool:
        """Write command to a specific node."""
        node = self.nodes.get(name)
        if node and node.is_active:
            return node.write(command)
        return False

    def update_all(self, dt: float):
        """Update all nodes simulation state."""
        for node in self.nodes.values():
            if node.is_active:
                node.update(dt)

    def emergency_stop(self):
        """Emergency stop all actuators."""
        self.logger.warning("EMERGENCY STOP triggered!")
        for name, node in self.nodes.items():
            if "motor" in name or "gripper" in name:
                node.reset()

    def shutdown(self):
        """Shutdown all hardware."""
        self.logger.info("Shutting down hardware...")
        for node in self.nodes.values():
            node.reset()
        self._initialized = False
