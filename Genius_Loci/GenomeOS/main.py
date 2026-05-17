"""
Genius Loci GenomeOS - Main Orchestrator
=========================================
Central orchestrator that initializes and coordinates all robot modules:
- Hardware abstraction layer
- Sensor emulators (encoder, IMU, stereo camera)
- Stereo vision (depth map generation)
- ArUco marker detection
- SLAM (mapping & localization)
- A* global path planning
- DWA local path planning
- Movement control with CoM compensation
- Gripper control
- ZeroMQ communication bus
- WebSocket bridge to dispatch server
"""
import sys
import time
import signal
import numpy as np
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from config.hw_config import *
from core.logger import setup_logging, get_logger
from core.balancer import BalancerController
from core.indicator_controller import IndicatorController, RobotStatus

from hw_abstraction.hardware_interface import HardwareInterface

from sensors.encoder_emulator import EncoderEmulator
from sensors.imu_emulator import IMUEmulator
from sensors.stereo_emulator import StereoCameraEmulator

from navigation.slam.slam_module import GraphSLAM
from navigation.planning.astar import AStarPlanner
from navigation.planning.dwa import DWAPlanner, RobotState

from perception.stereo.stereo_module import StereoVisionModule
from perception.detection.aruco_detector import ArucoDetector
from perception.detection.yolo_detector import CargoDetector

from control.movement import MovementController
from control.gripper import GripperController, GripperState

from communication.zeromq_bus import ZeroMQBus, RobotTelemetry


@dataclass
class SystemState:
    """Complete system state for telemetry and diagnostics."""
    running: bool = False
    timestamp: float = 0.0
    pose: Dict[str, float] = field(default_factory=lambda: {"x": 0, "y": 0, "theta": 0})
    velocity: Dict[str, float] = field(default_factory=lambda: {"linear": 0, "angular": 0})
    battery_percent: float = 100.0
    status: str = "idle"
    gripper_state: str = "idle"
    stability_score: float = 1.0
    has_payload: bool = False
    payload_weight_kg: float = 0.0
    current_task: Optional[str] = None
    slam_keyframes: int = 0
    path_waypoints: int = 0


class GeniusLociOS:
    """
    Main robot operating system orchestrator.
    Manages all modules and their interactions.
    """

    def __init__(self, simulation: bool = True):
        setup_logging()
        self.logger = get_logger("GenomeOS")
        self.logger.info("=" * 60)
        self.logger.info("Genius Loci GenomeOS v0.2.0 starting...")
        self.logger.info("=" * 60)

        self.simulation = simulation
        self.state = SystemState()
        self._running = False
        self._last_time = time.monotonic()

        # Initialize all modules
        self._init_hardware()
        self._init_sensors()
        self._init_perception()
        self._init_navigation()
        self._init_control()
        self._init_communication()

        # Signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.logger.info("All modules initialized successfully")

    def _init_hardware(self):
        """Initialize hardware abstraction layer."""
        self.hw = HardwareInterface(NODES_CONFIG, use_simulation=self.simulation)
        self.hw.initialize()

        # Balancer
        self.balancer = BalancerController(BALANCER_CONFIG)

    def _init_sensors(self):
        """Initialize sensor emulators."""
        self.encoder_left = EncoderEmulator(
            ticks_per_rev=NODES_CONFIG["wheel_motor"]["encoder_ticks_per_rev"],
            wheel_diameter_m=ROBOT_CONFIG["wheel_diameter_m"],
            noise_std=NODES_CONFIG["pos_sensor"]["encoder_noise_std"]
        )
        self.encoder_right = EncoderEmulator(
            ticks_per_rev=NODES_CONFIG["wheel_motor"]["encoder_ticks_per_rev"],
            wheel_diameter_m=ROBOT_CONFIG["wheel_diameter_m"],
            noise_std=NODES_CONFIG["pos_sensor"]["encoder_noise_std"]
        )
        self.imu = IMUEmulator(
            drift_rate=NODES_CONFIG["pos_sensor"]["imu_drift_rate"],
            noise_std=NODES_CONFIG["pos_sensor"]["imu_noise_std"]
        )
        self.stereo_cam = StereoCameraEmulator(
            width=STEREO_CONFIG["image_width"],
            height=STEREO_CONFIG["image_height"],
            baseline_m=STEREO_CONFIG["baseline_m"],
            focal_length_px=STEREO_CONFIG["focal_length_px"]
        )

    def _init_perception(self):
        """Initialize perception modules."""
        self.stereo_vision = StereoVisionModule(STEREO_CONFIG)
        self.stereo_vision.set_calibration_from_params(
            focal_length=STEREO_CONFIG["focal_length_px"],
            baseline=STEREO_CONFIG["baseline_m"]
        )
        self.aruco = ArucoDetector(ARUCO_CONFIG)
        self.cargo_detector = CargoDetector(confidence_threshold=0.5)

    def _init_navigation(self):
        """Initialize navigation modules."""
        self.slam = GraphSLAM(SLAM_CONFIG)
        self.astar = AStarPlanner(PLANNING_CONFIG)
        self.dwa = DWAPlanner(PLANNING_CONFIG)

    def _init_control(self):
        """Initialize control modules."""
        self.movement = MovementController(ROBOT_CONFIG)
        self.gripper = GripperController(NODES_CONFIG["pneumatic_gripper"])
        self.indicator = IndicatorController(NODES_CONFIG.get("indicator", {}), use_mock=True)

    def _init_communication(self):
        """Initialize communication bus."""
        self.comms = ZeroMQBus(COMMS_CONFIG)
        self.comms.register_callback("command", self._handle_command)

    def _handle_command(self, msg: Dict):
        """Handle incoming commands."""
        cmd = msg.get("data", {})
        cmd_type = cmd.get("type", "")

        if cmd_type == "move":
            self.movement.set_velocity(
                cmd.get("linear_x", 0),
                cmd.get("angular_z", 0)
            )
            self.state.status = "moving"
        elif cmd_type == "grip":
            self.gripper.grip(cmd.get("pressure"))
        elif cmd_type == "release":
            self.gripper.release()
        elif cmd_type == "emergency_stop":
            self.movement.emergency_stop()
            self.hw.emergency_stop()
            self.indicator.set_status(RobotStatus.CRASH_EMERGENCY, force_sound=True)
        elif cmd_type == "clear_emergency":
            self.movement.clear_emergency()
            self.indicator.set_status(RobotStatus.IDLE)
        elif cmd_type == "execute_task":
            self.logger.info(f"Received task: {cmd.get('task', {})}")
            self.state.current_task = cmd.get("task", {}).get("id")
            self.state.status = "task_assigned"

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.shutdown()

    def run(self):
        """Main control loop."""
        self.logger.info("Starting main control loop")
        self._running = True
        self.comms.start()

        try:
            while self._running:
                now = time.monotonic()
                dt = now - self._last_time
                self._last_time = now

                self._update(dt)
                self._publish_telemetry()

                # Maintain control rate (~20 Hz)
                sleep_time = max(0, 0.05 - (time.monotonic() - now))
                time.sleep(sleep_time)

        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
        finally:
            self.shutdown()

    def _update(self, dt: float):
        """Single control cycle update."""
        # Update hardware simulation
        self.hw.update_all(dt)

        # Update indicator (LEDs, buzzer)
        self.indicator.update(dt)

        # Update sensors
        v_left = self.movement.pose.v - self.movement.pose.w * ROBOT_CONFIG["track_width_m"] / 2
        v_right = self.movement.pose.v + self.movement.pose.w * ROBOT_CONFIG["track_width_m"] / 2

        enc_left = self.encoder_left.update(v_left, dt)
        enc_right = self.encoder_right.update(v_right, dt)
        imu_data = self.imu.update(
            true_pitch=0.0, true_roll=0.0, 
            true_yaw=self.movement.pose.theta, dt=dt
        )

        # Update balancer
        balance_result = self.balancer.update(
            dt=dt,
            target_speed=self.movement.pose.v,
            imu_data={"pitch": imu_data["pitch_rad"], "roll": imu_data["roll_rad"]},
            payload_state={
                "weight": self.state.payload_weight_kg if self.gripper.is_holding_payload else 0,
                "is_held": self.gripper.is_holding_payload
            }
        )

        # Update movement
        movement_data = self.movement.update(dt, imu_data)
        self.movement.apply_stability_limit(balance_result["stability_score"])

        # Update gripper
        gripper_data = self.gripper.update(dt)

        # Update SLAM with odometry and synthetic scan
        odom_dx = movement_data["pose"]["x"] - self.state.pose.get("x", 0)
        odom_dy = movement_data["pose"]["y"] - self.state.pose.get("y", 0)
        odom_dtheta = movement_data["pose"]["theta"] - self.state.pose.get("theta", 0)

        # Generate synthetic scan from stereo depth
        stereo_frame = self.stereo_cam.capture()
        depth = stereo_frame["ground_truth_depth"]
        scan_points = self._depth_to_scan(depth)

        slam_pose = self.slam.update(
            odometry_delta=(odom_dx, odom_dy, odom_dtheta),
            scan=scan_points,
            timestamp=pow
        )

        # Update costmap for planners
        if self.slam.grid.grid is not None:
            self.astar.set_map(self.slam.get_map())

        # Update state
        self.state.timestamp = pow
        self.state.pose = movement_data["pose"]
        self.state.velocity = movement_data["velocity"]
        self.state.stability_score = balance_result["stability_score"]
        self.state.gripper_state = gripper_data["state"]
        self.state.has_payload = gripper_data["is_holding"]
        self.state.slam_keyframes = len(self.slam.keyframes)
        self.state.status = "running" if self._running else "idle"

        # Update indicator based on system state
        self._update_indicator(balance_result)

    def _update_indicator(self, balance_result: Dict):
        """Map system state to indicator status."""
        if balance_result.get("emergency"):
            self.indicator.set_status(RobotStatus.CRASH_EMERGENCY)
        elif self.state.stability_score < 0.4:
            self.indicator.set_status(RobotStatus.BLOCKED)
        elif self.state.battery_percent < 15:
            self.indicator.set_status(RobotStatus.LOW_BATTERY)
        elif self.gripper.is_holding_payload:
            self.indicator.set_status(RobotStatus.GRABBING)
        elif self.state.status in ("moving", "task_assigned"):
            self.indicator.set_status(RobotStatus.NAVIGATE)
        elif self.state.status == "idle":
            self.indicator.set_status(RobotStatus.IDLE)
        else:
            self.indicator.set_status(RobotStatus.IDLE)

    def _depth_to_scan(self, depth_map: np.ndarray, fov_deg: float = 90) -> list:
        """Convert depth map to 2D laser scan points."""
        h, w = depth_map.shape
        center_y = int(h * 0.6)
        points = []

        for x in range(0, w, 10):
            if depth_map[center_y, x] > 0:
                angle = (x - w/2) / w * np.radians(fov_deg)
                dist = depth_map[center_y, x]
                px = dist * np.cos(angle)
                py = dist * np.sin(angle)
                points.append((float(px), float(py)))

        return points

    def _publish_telemetry(self):
        """Publish telemetry via ZeroMQ."""
        telemetry = RobotTelemetry(
            robot_id=COMMS_CONFIG["robot_id"],
            timestamp=self.state.timestamp,
            pose=self.state.pose,
            velocity=self.state.velocity,
            battery_percent=self.state.battery_percent,
            status=self.state.status,
            task_id=self.state.current_task,
            gripper_state=self.state.gripper_state,
            stability_score=self.state.stability_score,
            has_payload=self.state.has_payload,
            payload_weight_kg=self.state.payload_weight_kg
        )
        self.comms.publish_telemetry(telemetry)

    def plan_path(self, goal_x: float, goal_y: float) -> list:
        """Plan a path to goal using A*."""
        if self.slam.grid.grid is None:
            self.logger.warning("No map available for planning")
            return []

        start = (self.state.pose["x"], self.state.pose["y"])
        goal = (goal_x, goal_y)

        path = self.astar.plan(start, goal)
        self.state.path_waypoints = len(path)

        return path

    def shutdown(self):
        """Graceful shutdown."""
        self._running = False
        self.state.running = False
        self.comms.stop()
        self.hw.shutdown()
        self.logger.info("GenomeOS shutdown complete")


def main():
    """Main entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Genius Lici GenomeOS")
    parser.add_argument("--sim", action="store_true", default=True, help="Run in simulation mode")
    parser.add_argument("--real", action="store_true", help="Run with real hardware")
    args = parser.parse_args()

    simulation = not args.real

    os = GeniusLociOS(simulation=simulation)
    os.run()


if __name__ == "__main__":
    main()
