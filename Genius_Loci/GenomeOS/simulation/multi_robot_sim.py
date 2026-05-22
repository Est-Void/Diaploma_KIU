"""
Multi-Robot Simulation for Genius Loci
========================================
Launches multiple simulated robots with realistic movement patterns
for testing and demonstration of the web AIS.

Usage:
    python multi_robot_sim.py --count 3 --duration 300

Options:
    --count     Number of robots to simulate (default: 3)
    --duration  Simulation duration in seconds (default: 300)
    --server    WebSocket server URL (default: ws://localhost:8000)
"""
import asyncio
import json
import math
import random
import signal
import sys
import time
from dataclasses import dataclass, asdict
from typing import Optional
import argparse

import websockets


@dataclass
class SimRobot:
    """Simulated robot state."""
    robot_id: str
    name: str
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0
    battery: float = 100.0
    status: str = "free"
    linear_vel: float = 0.0
    angular_vel: float = 0.0
    stability_score: float = 1.0
    gripper_state: str = "idle"
    has_payload: bool = False
    payload_weight_kg: float = 0.0
    encoder_left: float = 0.0
    encoder_right: float = 0.0
    imu_pitch: float = 0.0
    imu_roll: float = 0.0
    slam_keyframes: int = 0
    path_waypoints: int = 0
    current_task_id: Optional[str] = None
    # Task execution state
    task_phase: str = "idle"  # idle, moving_to_pickup, picking, moving_to_dropoff, dropping
    task_pickup: tuple = (0, 0)
    task_dropoff: tuple = (0, 0)
    task_timer: float = 0.0

    def to_telemetry(self) -> dict:
        return {
            "type": "telemetry",
            "data": {
                "pose": {"x": self.x, "y": self.y, "theta": self.theta},
                "velocity": {"linear": self.linear_vel, "angular": self.angular_vel},
                "battery_percent": self.battery,
                "status": self.status,
                "gripper_state": self.gripper_state,
                "stability_score": self.stability_score,
                "has_payload": self.has_payload,
                "payload_weight_kg": self.payload_weight_kg,
                "encoder": {"left": self.encoder_left, "right": self.encoder_right},
                "imu": {"pitch": self.imu_pitch, "roll": self.imu_roll, "yaw": self.theta},
                "slam_keyframes": self.slam_keyframes,
                "path_waypoints": self.path_waypoints,
                "task_id": self.current_task_id
            }
        }


class MultiRobotSimulation:
    """Simulates multiple robots moving in a warehouse environment."""

    # Warehouse waypoints for patrol routes
    WAYPOINTS = [
        (-80, -80), (-80, -40), (-80, 0), (-80, 40), (-80, 80),
        (-40, -80), (-40, 40), (-40, 80),
        (0, -80), (0, -30), (0, 30), (0, 80),
        (40, -80), (40, -40), (40, 40), (40, 80),
        (80, -80), (80, -40), (80, 0), (80, 40), (80, 80),
        (-60, -60), (-60, 20), (-60, 60),
        (20, -60), (20, 20), (20, 60),
        (60, -60), (60, 20), (60, 60),
        (0, 0),
    ]

    # Obstacles: list of (x1, y1, x2, y2) bounding boxes
    OBSTACLES = [
        (-70, -80, -50, -40), (-70, -30, -50, 10), (-70, 20, -50, 60), (-70, 70, -50, 90),
        (-20, -80, 0, -40), (-20, -30, 0, 10), (-20, 20, 0, 60), (-20, 70, 0, 90),
        (30, -80, 50, -40), (30, -30, 50, 10), (30, 20, 50, 60), (30, 70, 50, 90),
        (60, -60, 80, -20), (60, -10, 80, 30), (60, 40, 80, 80),
        # Pillars (as small boxes)
        (-43, -43, -37, -37), (37, 37, 43, 43), (-3, -3, 3, 3),
        (-43, 47, -37, 53), (47, -53, 53, -47),
        # Docks
        (-90, 85, -75, 98), (75, 85, 90, 98), (-98, -60, -75, -45),
        # Charging station
        (80, -98, 95, -80),
    ]

    def __init__(self, robot_count: int = 3, server_url: str = "ws://localhost:8000"):
        self.robot_count = robot_count
        self.server_url = server_url
        self.robots: list[SimRobot] = []
        self.running = False
        self.ws_connections: dict[str, websockets.WebSocketClientProtocol] = {}
        self._shutdown_event = asyncio.Event()

        # Generate robots
        names = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta"]
        colors = ["GL-001", "GL-002", "GL-003", "GL-004", "GL-005", "GL-006", "GL-007", "GL-008"]

        for i in range(robot_count):
            wp = self.WAYPOINTS[i % len(self.WAYPOINTS)]
            robot = SimRobot(
                robot_id=colors[i],
                name=f"Genius Loci {names[i]}",
                x=wp[0] + random.uniform(-3, 3),
                y=wp[1] + random.uniform(-3, 3),
                theta=random.uniform(0, 2 * math.pi),
                battery=random.uniform(60, 100),
                status=random.choice(["free", "busy", "charging"]),
                slam_keyframes=random.randint(10, 200)
            )
            self.robots.append(robot)

        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        print(f"[Sim] Initialized {robot_count} robots for simulation")
        for r in self.robots:
            print(f"  - {r.name} ({r.robot_id}) at ({r.x:.1f}, {r.y:.1f})")

    def _signal_handler(self, signum, frame):
        print(f"\n[Sim] Received signal {signum}, shutting down...")
        self.running = False
        self._shutdown_event.set()

    async def connect_robots(self):
        """Connect all robots to the WebSocket server."""
        for robot in self.robots:
            try:
                ws_url = f"{self.server_url}/ws/robot/{robot.robot_id}"
                ws = await websockets.connect(ws_url)
                self.ws_connections[robot.robot_id] = ws
                print(f"[Sim] {robot.name} connected to server")
            except Exception as e:
                print(f"[Sim] Warning: Could not connect {robot.name}: {e}")
                print(f"[Sim] Running in standalone mode (no server)")
                return False
        return True

    async def disconnect_robots(self):
        """Disconnect all robots."""
        for robot_id, ws in self.ws_connections.items():
            try:
                await ws.close()
            except Exception:
                pass
        self.ws_connections.clear()
        print("[Sim] All robots disconnected")

    def _update_robot(self, robot: SimRobot, dt: float):
        """Update single robot state for one timestep."""
        # Battery drain
        if robot.status != "charging":
            robot.battery = max(0, robot.battery - 0.008)

        # Charging behavior
        if robot.status == "charging" or robot.battery < 15:
            robot.status = "charging"
            robot.battery = min(100, robot.battery + 1.0)
            robot.linear_vel = 0
            robot.angular_vel = 0
            if robot.battery > 90:
                robot.status = "free"
            return

        # Task execution
        if robot.task_phase == "moving_to_pickup":
            self._move_towards(robot, robot.task_pickup, dt)
            if self._distance(robot, robot.task_pickup) < 2.0:
                robot.task_phase = "picking"
                robot.task_timer = 2.0
                robot.gripper_state = "grabbing"
        elif robot.task_phase == "picking":
            robot.linear_vel = 0
            robot.angular_vel = 0
            robot.task_timer -= dt
            if robot.task_timer <= 0:
                robot.has_payload = True
                robot.payload_weight_kg = random.uniform(5, 40)
                robot.gripper_state = "holding"
                robot.task_phase = "moving_to_dropoff"
        elif robot.task_phase == "moving_to_dropoff":
            self._move_towards(robot, robot.task_dropoff, dt)
            if self._distance(robot, robot.task_dropoff) < 2.0:
                robot.task_phase = "dropping"
                robot.task_timer = 1.5
                robot.gripper_state = "releasing"
        elif robot.task_phase == "dropping":
            robot.linear_vel = 0
            robot.angular_vel = 0
            robot.task_timer -= dt
            if robot.task_timer <= 0:
                robot.has_payload = False
                robot.payload_weight_kg = 0
                robot.gripper_state = "idle"
                robot.task_phase = "idle"
                robot.status = "free"
                robot.current_task_id = None
        else:
            # Free roaming between waypoints
            if random.random() < 0.01:
                target = random.choice(self.WAYPOINTS)
                robot.task_pickup = target  # reuse as target
            self._move_towards(robot, robot.task_pickup, dt)

        # Update encoders & IMU
        robot.encoder_left += robot.linear_vel * dt * 100
        robot.encoder_right += robot.linear_vel * dt * 100
        robot.imu_pitch = random.uniform(-0.05, 0.05)
        robot.imu_roll = random.uniform(-0.03, 0.03)
        robot.stability_score = min(1.0, max(0.5, 1.0 - abs(robot.imu_pitch) - abs(robot.imu_roll)))
        if random.random() < 0.01:
            robot.slam_keyframes += 1

        # Keep within bounds
        robot.x = max(-95, min(95, robot.x))
        robot.y = max(-95, min(95, robot.y))

    def _distance(self, robot: SimRobot, target: tuple) -> float:
        return math.sqrt((target[0] - robot.x)**2 + (target[1] - robot.y)**2)

    def _move_towards(self, robot: SimRobot, target: tuple, dt: float):
        """Move robot towards a target point with obstacle avoidance."""
        dx = target[0] - robot.x
        dy = target[1] - robot.y
        dist = math.sqrt(dx*dx + dy*dy)
        if dist < 0.5:
            robot.linear_vel = 0
            robot.angular_vel = 0
            return

        target_theta = math.atan2(dy, dx)

        # Obstacle avoidance: check if path ahead is blocked
        lookahead = min(dist, 15.0)
        next_x = robot.x + math.cos(target_theta) * lookahead
        next_y = robot.y + math.sin(target_theta) * lookahead

        # Check if next position hits an obstacle
        blocked = self._is_blocked(next_x, next_y)

        if blocked:
            # Try steering left or right
            for steer_angle in [0.8, -0.8, 1.5, -1.5, 2.5, -2.5]:
                alt_theta = target_theta + steer_angle
                alt_x = robot.x + math.cos(alt_theta) * lookahead
                alt_y = robot.y + math.sin(alt_theta) * lookahead
                if not self._is_blocked(alt_x, alt_y):
                    target_theta = alt_theta
                    break

        angle_diff = target_theta - robot.theta
        while angle_diff > math.pi: angle_diff -= 2 * math.pi
        while angle_diff < -math.pi: angle_diff += 2 * math.pi

        robot.angular_vel = angle_diff * 0.5 + random.uniform(-0.05, 0.05)
        robot.linear_vel = min(1.2, dist * 0.15) + random.uniform(-0.03, 0.03)

        # Check if next step would enter obstacle - stop if blocked at close range
        step_x = robot.x + robot.linear_vel * math.cos(robot.theta) * dt
        step_y = robot.y + robot.linear_vel * math.sin(robot.theta) * dt
        if self._is_blocked(step_x, step_y):
            robot.linear_vel = 0.1  # creep slowly
        else:
            robot.theta += robot.angular_vel * dt
            robot.x = step_x
            robot.y = step_y

    def _is_blocked(self, x: float, y: float) -> bool:
        """Check if a point is inside any obstacle."""
        margin = 2.0  # extra clearance around obstacles
        for (x1, y1, x2, y2) in self.OBSTACLES:
            if (x1 - margin) <= x <= (x2 + margin) and (y1 - margin) <= y <= (y2 + margin):
                return True
        return False

    def _assign_task(self, robot: SimRobot, task: dict):
        """Assign a task to a robot."""
        if robot.task_phase != "idle":
            return  # already busy
        robot.current_task_id = task.get("id", "")
        robot.task_phase = "moving_to_pickup"
        robot.task_pickup = (task.get("pickup_x", 0), task.get("pickup_y", 0))
        robot.task_dropoff = (task.get("dropoff_x", 0), task.get("dropoff_y", 0))
        robot.status = "busy"
        robot.payload_weight_kg = task.get("payload_weight_kg", 10)
        print(f"[Sim] {robot.name} assigned task {robot.current_task_id}: "
              f"pickup({robot.task_pickup[0]:.0f},{robot.task_pickup[1]:.0f}) → "
              f"dropoff({robot.task_dropoff[0]:.0f},{robot.task_dropoff[1]:.0f})")

    async def _send_telemetry(self, robot: SimRobot):
        """Send telemetry for one robot."""
        ws = self.ws_connections.get(robot.robot_id)
        if ws:
            try:
                await ws.send(json.dumps(robot.to_telemetry()))
                # Also send task update when task phase changes
                if robot.current_task_id and robot.task_phase in ("picking", "dropping"):
                    await ws.send(json.dumps({
                        "type": "task_update",
                        "task": {
                            "id": robot.current_task_id,
                            "status": "in_progress" if robot.task_phase == "picking" else "completing"
                        }
                    }))
            except Exception:
                pass  # silently ignore send errors

    async def _receive_commands(self, robot: SimRobot):
        """Listen for commands from server for a specific robot."""
        ws = self.ws_connections.get(robot.robot_id)
        if not ws:
            return
        try:
            msg = await asyncio.wait_for(ws.recv(), timeout=0.01)
            data = json.loads(msg)
            if data.get("type") == "execute_task":
                self._assign_task(robot, data.get("task", {}))
        except asyncio.TimeoutError:
            pass
        except websockets.ConnectionClosed:
            pass
        except Exception:
            pass

    async def run(self, duration: Optional[float] = None):
        """Run the simulation loop."""
        self.running = True
        connected = await self.connect_robots()

        if not connected and not self.ws_connections:
            print("[Sim] No server connection. Robots will move but data won't be sent.")
            print("[Sim] Start the server first: cd ../Server/backend && python main.py")

        start_time = time.monotonic()
        last_update = start_time

        print(f"[Sim] Simulation started{' (connected to server)' if connected else ''}")
        print("[Sim] Press Ctrl+C to stop\n")

        try:
            while self.running:
                now = time.monotonic()
                dt = now - last_update
                last_update = now

                # Check duration
                if duration and (now - start_time) > duration:
                    print(f"[Sim] Duration limit ({duration}s) reached")
                    break

                # Update all robots
                for robot in self.robots:
                    # Check for incoming commands
                    await self._receive_commands(robot)
                    self._update_robot(robot, dt)
                    if robot.robot_id in self.ws_connections:
                        await self._send_telemetry(robot)

                # Print status every 5 seconds
                elapsed = now - start_time
                if int(elapsed) % 5 == 0 and elapsed > 1:
                    active = sum(1 for r in self.robots if r.status == "busy")
                    print(f"\r[Sim] Elapsed: {int(elapsed)}s | Active: {active}/{len(self.robots)} robots", end="", flush=True)

                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            pass
        finally:
            print("\n[Sim] Stopping simulation...")
            self.running = False
            await self.disconnect_robots()
            print("[Sim] Simulation complete")


def main():
    parser = argparse.ArgumentParser(
        description="Genius Loci Multi-Robot Simulation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python multi_robot_sim.py                    # Start 3 robots
    python multi_robot_sim.py --count 5          # Start 5 robots
    python multi_robot_sim.py --duration 600     # Run for 10 minutes
    python multi_robot_sim.py --count 4 --duration 0  # Run 4 robots indefinitely
        """
    )
    parser.add_argument("--count", type=int, default=3,
                        help="Number of robots to simulate (default: 3, max: 8)")
    parser.add_argument("--duration", type=float, default=300,
                        help="Simulation duration in seconds, 0 = infinite (default: 300)")
    parser.add_argument("--server", type=str, default="ws://localhost:8000",
                        help="WebSocket server URL (default: ws://localhost:8000)")

    args = parser.parse_args()

    count = min(max(1, args.count), 8)
    duration = args.duration if args.duration > 0 else None

    print("=" * 60)
    print("  Genius Loci - Multi-Robot Simulation")
    print("=" * 60)
    print(f"  Robots:    {count}")
    print(f"  Duration:  {'infinite' if duration is None else f'{duration}s'}")
    print(f"  Server:    {args.server}")
    print("=" * 60 + "\n")

    sim = MultiRobotSimulation(robot_count=count, server_url=args.server)

    try:
        asyncio.run(sim.run(duration=duration))
    except KeyboardInterrupt:
        print("\n[Sim] Interrupted by user")
        sys.exit(0)


if __name__ == "__main__":
    main()
