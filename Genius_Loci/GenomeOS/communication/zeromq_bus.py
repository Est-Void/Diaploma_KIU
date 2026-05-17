"""
ZeroMQ-based communication bus for inter-module messaging.
Provides pub/sub pattern for telemetry and command distribution.
"""
import json
import time
import threading
import zmq
from typing import Dict, Any, Callable, Optional, List
from dataclasses import asdict, dataclass
from core.logger import get_logger


@dataclass
class RobotTelemetry:
    """Robot telemetry message structure."""
    robot_id: str
    timestamp: float
    pose: Dict[str, float]
    velocity: Dict[str, float]
    battery_percent: float
    status: str
    task_id: Optional[str] = None
    gripper_state: str = "idle"
    stability_score: float = 1.0
    has_payload: bool = False
    payload_weight_kg: float = 0.0


class ZeroMQBus:
    """
    ZeroMQ communication bus for robot modules.
    Publishes telemetry and receives commands.
    """

    def __init__(self, config: Dict[str, Any]):
        self.logger = get_logger("Comm.ZMQ")
        self.robot_id = config.get("robot_id", "genius_loci_001")
        self.pub_addr = config.get("zeromq_pub_addr", "tcp://127.0.0.1:5555")
        self.sub_addr = config.get("zeromq_sub_addr", "tcp://127.0.0.1:5556")
        self.cmd_addr = config.get("zeromq_cmd_addr", "tcp://127.0.0.1:5557")
        self.telemetry_rate = config.get("telemetry_rate_hz", 5)

        self._ctx = zmq.Context.instance()
        self._publisher: Optional[zmq.Socket] = None
        self._subscriber: Optional[zmq.Socket] = None
        self._command_socket: Optional[zmq.Socket] = None
        self._connected = False

        self._callbacks: Dict[str, List[Callable]] = {}
        self._running = False
        self._recv_thread: Optional[threading.Thread] = None

        self.logger.info("ZeroMQ bus initialized")

    def connect(self):
        """Initialize all ZMQ sockets."""
        try:
            # Publisher for telemetry
            self._publisher = self._ctx.socket(zmq.PUB)
            self._publisher.bind(self.pub_addr)

            # Subscriber for commands
            self._subscriber = self._ctx.socket(zmq.SUB)
            self._subscriber.bind(self.sub_addr)
            self._subscriber.setsockopt_string(zmq.SUBSCRIBE, "")

            # Command socket (router for bidirectional)
            self._command_socket = self._ctx.socket(zmq.REP)
            self._command_socket.bind(self.cmd_addr)

            self._connected = True
            self.logger.info(f"ZMQ connected: pub={self.pub_addr}, sub={self.sub_addr}")

        except zmq.ZMQError as e:
            self.logger.error(f"ZMQ connection failed: {e}")
            self._connected = False

    def start(self):
        """Start communication loops."""
        if not self._connected:
            self.connect()

        self._running = True
        self._recv_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self._recv_thread.start()
        self.logger.info("Communication bus started")

    def stop(self):
        """Stop communication loops."""
        self._running = False
        if self._recv_thread:
            self._recv_thread.join(timeout=2.0)

        for sock in [self._publisher, self._subscriber, self._command_socket]:
            if sock:
                sock.close()

        self.logger.info("Communication bus stopped")

    def publish_telemetry(self, telemetry: RobotTelemetry):
        """Publish robot telemetry to all subscribers."""
        if not self._publisher:
            return

        msg = {
            "type": "telemetry",
            "robot_id": telemetry.robot_id,
            "timestamp": time.time(),
            "data": {
                "pose": telemetry.pose,
                "velocity": telemetry.velocity,
                "battery_percent": telemetry.battery_percent,
                "status": telemetry.status,
                "task_id": telemetry.task_id,
                "gripper_state": telemetry.gripper_state,
                "stability_score": telemetry.stability_score,
                "has_payload": telemetry.has_payload,
                "payload_weight_kg": telemetry.payload_weight_kg
            }
        }

        try:
            self._publisher.send_json(msg, flags=zmq.NOBLOCK)
        except zmq.Again:
            pass

    def send_command(self, command: Dict[str, Any], target: Optional[str] = None):
        """Send command to robot or module."""
        if not self._publisher:
            return

        msg = {
            "type": "command",
            "timestamp": time.time(),
            "target": target or "all",
            "data": command
        }

        try:
            self._publisher.send_json(msg, flags=zmq.NOBLOCK)
        except zmq.Again:
            pass

    def register_callback(self, msg_type: str, callback: Callable):
        """Register callback for message type."""
        if msg_type not in self._callbacks:
            self._callbacks[msg_type] = []
        self._callbacks[msg_type].append(callback)

    def _receive_loop(self):
        """Background thread for receiving messages."""
        while self._running:
            try:
                if self._subscriber and self._subscriber.poll(100):
                    msg = self._subscriber.recv_json(flags=zmq.NOBLOCK)
                    self._dispatch(msg)

                if self._command_socket and self._command_socket.poll(100):
                    msg = self._command_socket.recv_json(flags=zmq.NOBLOCK)
                    self._dispatch(msg)
                    # Reply with ack
                    self._command_socket.send_json({"status": "ok", "timestamp": time.time()})

            except zmq.Again:
                pass
            except Exception as e:
                self.logger.error(f"Receive error: {e}")

    def _dispatch(self, msg: Dict):
        """Dispatch message to registered callbacks."""
        msg_type = msg.get("type", "unknown")
        for callback in self._callbacks.get(msg_type, []):
            try:
                callback(msg)
            except Exception as e:
                self.logger.error(f"Callback error: {e}")

    def is_connected(self) -> bool:
        return self._connected


class WebSocketBridge:
    """
    Bridge between ZeroMQ and WebSocket for server communication.
    Translates ZMQ messages to WebSocket format.
    """

    def __init__(self, server_host: str, server_port: int, robot_id: str):
        self.logger = get_logger("Comm.WSBridge")
        self.server_url = f"ws://{server_host}:{server_port}/ws/robot/{robot_id}"
        self.robot_id = robot_id
        self._connected = False
        self._on_telemetry: Optional[Callable] = None

    def connect(self):
        """Connect to server WebSocket."""
        try:
            import websocket
            self._ws = websocket.WebSocketApp(
                self.server_url,
                on_open=self._on_open,
                on_message=self._on_message,
                on_error=self._on_error,
                on_close=self._on_close
            )
            self._connected = True
            self.logger.info(f"WebSocket connected to {self.server_url}")
        except ImportError:
            self.logger.warning("websocket-client not installed")
        except Exception as e:
            self.logger.error(f"WebSocket connection failed: {e}")

    def send_telemetry(self, telemetry: RobotTelemetry):
        """Send telemetry to server."""
        if not self._connected:
            return

        msg = {
            "type": "telemetry",
            "robot_id": telemetry.robot_id,
            "timestamp": time.time(),
            **{k: v for k, v in telemetry.__dict__.items() if k != "robot_id"}
        }

        try:
            self._ws.send(json.dumps(msg))
        except Exception as e:
            self.logger.error(f"Send error: {e}")
            self._connected = False

    def _on_open(self, ws):
        self.logger.info("WebSocket opened")
        self._connected = True

    def _on_message(self, ws, message):
        try:
            msg = json.loads(message)
            if msg.get("type") == "command" and self._on_telemetry:
                self._on_telemetry(msg)
        except json.JSONDecodeError:
            pass

    def _on_error(self, ws, error):
        self.logger.error(f"WebSocket error: {error}")
        self._connected = False

    def _on_close(self, ws, close_status, close_msg):
        self.logger.info("WebSocket closed")
        self._connected = False
