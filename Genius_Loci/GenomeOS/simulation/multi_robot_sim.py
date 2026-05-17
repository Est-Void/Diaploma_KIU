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
        (-40, -40), (-40, 0), (-40, 40), (0, 40), (40, 40),
        (40, 0), (40, -40), (0, -40), (-20, -20), (-20, 20),
        (20, 20), (20, -20), (0, 0)
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
        # Random behavior changes
        if random.random() < 0.005:
            robot.status = random.choice(["free", "busy", "charging"])

        if robot.status == "charging":
            robot.battery = min(100, robot.battery + 0.5)
            robot.linear_vel = 0
            robot.angular_vel = 0
            return

        # Movement towards random waypoint
        if random.random() < 0.02:
            robot.current_task_id = f"TASK-{random.randint(1000, 9999)}"

        target = random.choice(self.WAYPOINTS)
        dx = target[0] - robot.x
        dy = target[1] - robot.y
        dist = math.sqrt(dx*dx + dy*dy)

        if dist > 1.0:
            target_theta = math.atan2(dy, dx)
            angle_diff = target_theta - robot.theta
            while angle_diff > math.pi:
                angle_diff -= 2 * math.pi
            while angle_diff < -math.pi:
                angle_diff += 2 * math.pi

            robot.angular_vel = angle_diff * 0.5 + random.uniform(-0.1, 0.1)
            robot.linear_vel = min(1.2, dist * 0.1) + random.uniform(-0.05, 0.05)
            robot.theta += robot.angular_vel * dt
            robot.x += robot.linear_vel * math.cos(robot.theta) * dt
            robot.y += robot.linear_vel * math.sin(robot.theta) * dt
        else:
            robot.linear_vel = 0
            robot.angular_vel = 0
            robot.current_task_id = None

        # Update encoders
        robot.encoder_left += robot.linear_vel * dt * 100
        robot.encoder_right += robot.linear_vel * dt * 100

        # Update IMU
        robot.imu_pitch = random.uniform(-0.05, 0.05)
        robot.imu_roll = random.uniform(-0.03, 0.03)

        # Update battery
        robot.battery = max(0, robot.battery - 0.01)
        if robot.battery < 20:
            robot.status = "charging"

        # Update stability
        robot.stability_score = min(1.0, max(0.5, 1.0 - abs(robot.imu_pitch) - abs(robot.imu_roll)))

        # Occasional payload
        if random.random() < 0.001:
            robot.has_payload = not robot.has_payload
            robot.payload_weight_kg = random.uniform(5, 40) if robot.has_payload else 0
            robot.gripper_state = "holding" if robot.has_payload else "idle"

        # Increment keyframes occasionally
        if random.random() < 0.01:
            robot.slam_keyframes += 1

        # Keep within bounds
        robot.x = max(-48, min(48, robot.x))
        robot.y = max(-48, min(48, robot.y))

    async def _send_telemetry(self, robot: SimRobot):
        """Send telemetry for one robot."""
        ws = self.ws_connections.get(robot.robot_id)
        if ws and ws.open:
            try:
                await ws.send(json.dumps(robot.to_telemetry()))
            except Exception as e:
                print(f"[Sim] Send error for {robot.name}: {e}")

    async def run(self, duration: Optional[float] = None):
        """Run the simulation loop."""
        self.running = True
        connected = await self.connect_robots()

        if not connected and not self.ws_connections:
            print("[Sim] No server connection. Robots will move but data won't be sent.")
            print("[Sim] Start the server first: python -m server.main")

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
