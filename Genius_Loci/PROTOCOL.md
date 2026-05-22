# Genius Loci Communication Protocol

## Overview

Communication between **GenomeOS** (robot) and **Server** (dispatch) uses WebSocket with JSON messages.

---

## Connection

| Endpoint | Direction | Description |
|----------|-----------|-------------|
| `ws://<server>/ws/robot/{robot_id}` | Robot → Server | Robot connects with its unique ID |
| `ws://<server>/ws/client` | Client → Server | Web AIS frontend connects |

Robot identifies itself via the URL path: `/ws/robot/genius_loci_001`.

---

## Robot → Server Messages

### Telemetry (periodic, ~200ms)

```json
{
  "type": "telemetry",
  "robot_id": "genius_loci_001",
  "timestamp": 1700000000.123,
  "data": {
    "pose": {"x": 12.5, "y": 34.2, "theta": 0.78},
    "velocity": {"linear": 0.5, "angular": 0.1},
    "battery_percent": 87.3,
    "status": "moving",
    "task_id": "TASK-A1B2C3D4",
    "gripper_state": "idle",
    "stability_score": 0.95,
    "has_payload": false,
    "payload_weight_kg": 0.0
  }
}
```

### Task Update

```json
{
  "type": "task_update",
  "robot_id": "genius_loci_001",
  "task": {
    "id": "TASK-A1B2C3D4",
    "status": "in_progress",
    "checkpoint": 2
  }
}
```

### Log

```json
{
  "type": "log",
  "robot_id": "genius_loci_001",
  "level": "INFO",
  "message": "Reached waypoint A3"
}
```

---

## Server → Robot Messages

### Execute Task

```json
{
  "type": "execute_task",
  "task": {
    "id": "TASK-A1B2C3D4",
    "pickup_x": 15.0,
    "pickup_y": 40.0,
    "dropoff_x": 80.0,
    "dropoff_y": 20.0,
    "payload_weight_kg": 25.0
  }
}
```

### Generic Command

```json
{
  "type": "command",
  "command_type": "emergency_stop",
  "params": {}
}
```

Supported `command_type` values:
- `emergency_stop` — halt all motors
- `cancel_mission` — abort current task
- `move` — direct velocity control `{"linear_x": 0.5, "angular_z": 0.0}`
- `grip` — close gripper `{"pressure": 3.0}`
- `release` — open gripper

---

## Server → Client Messages (broadcast)

### Telemetry Relay

```json
{
  "type": "telemetry",
  "robot_id": "genius_loci_001",
  "data": { ... }
}
```

### Robot Connection Events

```json
{"type": "robot_connected", "robot_id": "genius_loci_001"}
{"type": "robot_disconnected", "robot_id": "genius_loci_001"}
```

### Task Assignment

```json
{"type": "task_assigned", "task_id": "TASK-A1B2C3D4", "robot_id": "genius_loci_001"}
```

---

## REST API

Full OpenAPI docs at `http://<server>:8000/docs` once server is running.

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/v1/auth/login` | POST | No | JWT login |
| `/api/v1/auth/register` | POST | No | Register user |
| `/api/v1/auth/me` | GET | JWT | Current user |
| `/api/v1/robots` | GET | JWT | List robots |
| `/api/v1/robots/{id}` | GET/PATCH | JWT | Robot CRUD |
| `/api/v1/tasks` | GET/POST | JWT | Task CRUD |
| `/api/v1/tasks/{id}` | GET/PATCH/DELETE | JWT | Task management |
| `/api/v1/maps` | GET/POST | JWT | Map storage |
| `/api/v1/logs` | GET | JWT | System logs |
