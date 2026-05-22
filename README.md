# Genius Loci — Autonomous Mobile Robot System

**Genius Loci** is an autonomous mobile robot (AMR) designed for warehouse logistics automation. This project includes a complete software stack: onboard robot operating system, central dispatch server, and a web-based automated information system (AIS) for real-time monitoring and fleet management.

Developed as a diploma project at Kazan Innovative University (KIU), specialty 09.02.07 Information Systems and Programming.

---

## Table of Contents

- [Overview](#overview)
- [System Architecture](#system-architecture)
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
  - [Prerequisites](#prerequisites)
  - [Server Setup](#server-setup)
  - [Web AIS Setup](#web-ais-setup)
  - [Robot Simulation](#robot-simulation)
- [Multi-Robot Simulation](#multi-robot-simulation)
- [Web AIS Interface](#web-ais-interface)
- [Warehouse Map](#warehouse-map)
- [API Documentation](#api-documentation)
- [Configuration](#configuration)
- [Screenshots](#screenshots)
- [Development Roadmap](#development-roadmap)
- [License](#license)

---

## Overview

The Genius Loci project aims to create an affordable and adaptive domestic solution for warehouse logistics automation. The system combines:

- **Onboard Robot OS (GenomeOS)**: Modular architecture with SLAM navigation, stereo vision, A* and DWA path planners, stability control, and gripper management
- **Central Dispatch Server**: FastAPI-based server with PostgreSQL database, task dispatcher, and real-time WebSocket communication
- **Web AIS**: React-based responsive web interface for monitoring robot fleets, warehouse maps, task management, and system administration

### Key Capabilities

- Autonomous warehouse navigation with real-time map building (SLAM)
- Multi-robot fleet management and task assignment
- Depth mapping via stereo vision
- ArUco marker detection for precise docking
- YOLO-based cargo detection
- Dynamic obstacle avoidance (DWA)
- Global path planning (A*)
- Center-of-mass compensation for stability
- Real-time telemetry and status monitoring
- Web-based control center with live warehouse map

---

## System Architecture

```
+-----------------------------------------------------+
|                    Web AIS (React)                   |
|  - Authentication  - Dashboard   - Robot Details    |
|  - Warehouse Map   - Task Mgmt   - System Logs      |
+-----------------------------------------------------+
                         | REST API / WebSocket
+-----------------------------------------------------+
|              Central Dispatch Server                 |
|  FastAPI | PostgreSQL | Task Dispatcher | WebSockets |
+-----------------------------------------------------+
                         | ZeroMQ / WebSocket
+-----------------------------------------------------+
|              Robot Fleet (GenomeOS)                  |
|  +---------+  +---------+  +---------+              |
|  | Robot 1 |  | Robot 2 |  | Robot N |              |
|  |GL-001   |  |GL-002   |  |GL-00N   |              |
|  +---------+  +---------+  +---------+              |
|  - SLAM      - A* Planner   - Stability Control      |
|  - Stereo    - DWA Local    - Gripper Control        |
|  - ArUco     - YOLO Detect  - Motor Control          |
+-----------------------------------------------------+
```

### Communication Flow

1. **Operator** creates a transport task via Web AIS
2. **Server** receives the task via REST API and queues it
3. **Dispatcher** assigns the task to the nearest available robot
4. **Robot** receives the task via WebSocket, plans path using A* + DWA
5. **Robot** executes the task while sending telemetry every 200ms
6. **Server** relays telemetry to all connected Web AIS clients in real-time
7. **Operator** watches robot movement on the live warehouse map

---

## Features

### Onboard Robot Software (GenomeOS)

| Module | Description | Status |
|--------|-------------|--------|
| SLAM (Graph-based) | Real-time mapping and localization with scan matching | Implemented |
| A* Path Planner | Global path planning on occupancy grid | Implemented |
| DWA Local Planner | Dynamic obstacle avoidance | Implemented |
| Stereo Vision | Depth map generation from stereo cameras | Implemented |
| ArUco Detection | Marker-based precise positioning | Implemented |
| YOLO Detection | Cargo/object detection | Implemented |
| Stability Control | Center-of-mass compensation with PID | Implemented |
| Gripper Control | Pneumatic gripper management | Implemented |
| Motor Control | Differential drive with encoder feedback | Implemented |
| ZeroMQ Bus | Inter-module communication | Implemented |

### Web AIS (Automated Information System)

| Feature | Description | Status |
|---------|-------------|--------|
| Authentication | JWT-based login with role separation (admin/operator) | Implemented |
| Dashboard | Real-time overview: robot counts, task status, live map | Implemented |
| Warehouse Map | Interactive map with robot positions, zones, trails | Implemented |
| Robot Details | Full telemetry: odometry, IMU, gripper, stability, battery | Implemented |
| Task Management | Create, assign, and monitor transport tasks | Implemented |
| System Logs | Filterable log viewer with severity levels | Implemented |
| Animations | Smooth UI transitions with Framer Motion | Implemented |
| Responsive | Mobile-friendly adaptive layout | Implemented |

### Server

| Feature | Description | Status |
|---------|-------------|--------|
| REST API | Full CRUD for robots, tasks, maps, users, logs | Implemented |
| WebSocket | Real-time bidirectional communication | Implemented |
| Task Dispatcher | Automatic task assignment by proximity | Implemented |
| Database | PostgreSQL with SQLAlchemy ORM | Implemented |
| Auth | JWT tokens with bcrypt password hashing | Implemented |

---

## Technology Stack

### Robot (Onboard)
- **Language**: Python 3.10+
- **Navigation**: NumPy, SciPy, custom SLAM implementation
- **Vision**: OpenCV (SGBM stereo, ArUco, YOLOv8)
- **Communication**: ZeroMQ
- **Simulation**: Built-in sensor emulators with configurable noise

### Server
- **Framework**: FastAPI (async Python)
- **Database**: PostgreSQL 14+
- **ORM**: SQLAlchemy 2.0
- **Auth**: python-jose + passlib
- **Real-time**: Native WebSockets

### Web AIS
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **Animations**: Framer Motion
- **Maps**: Leaflet.js
- **Icons**: Lucide React

---

## Project Structure

Проект разделён на две независимые части:

```
Genius_Loci/
├── GenomeOS/               # Локальная ОС робота (Python)
│   ├── main.py             # Оркестратор
│   ├── config/             # Конфигурация робота
│   ├── core/               # PID, balancer, logger
│   ├── navigation/         # SLAM, A*, DWA
│   ├── perception/         # Stereo vision, ArUco, YOLO
│   ├── sensors/            # Эмуляторы датчиков
│   ├── control/            # Движение, гриппер
│   ├── hw_abstraction/     # Абстракция железа
│   ├── communication/      # ZeroMQ + WebSocket клиент
│   └── simulation/         # Симуляция флота роботов
│
├── Server/                 # Серверная часть
│   ├── backend/            # FastAPI + PostgreSQL
│   │   ├── main.py
│   │   ├── config.py
│   │   └── app/
│   │       ├── models/     # SQLAlchemy
│   │       ├── schemas/    # Pydantic
│   │       ├── routers/    # REST API
│   │       └── services/   # WebSocket, Dispatcher
│   └── frontend/           # React Web AIS
│       └── src/
│           ├── components/ # Layout, RobotMap
│           ├── pages/      # Dashboard, Tasks, etc.
│           └── hooks/      # useWebSocket
│
└── PROTOCOL.md             # API контракт GenomeOS ↔ Server
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- PostgreSQL 14+ (or use SQLite for testing)
- Git

### Robot (GenomeOS)

```bash
cd Genius_Loci/GenomeOS
pip install -r requirements.txt
python main.py --sim
```

### Server + Frontend

См. `Server/README.md`:

```bash
# Backend
cd Genius_Loci/Server/backend
pip install -r requirements.txt
python main.py
# → http://localhost:8000 (Swagger: /docs)

# Frontend
cd Genius_Loci/Server/frontend
npm install && npm run dev
# → http://localhost:5173
```

---

## Multi-Robot Simulation

Launch multiple simulated robots to test the web AIS:

```bash
cd Genius_Loci/GenomeOS
python -m simulation.multi_robot_sim --count 3 --duration 300
```

**Parameters:**
- `--count N` — Number of robots (1-8, default: 3)
- `--duration S` — Duration in seconds, 0 = infinite (default: 300)
- `--server URL` — WebSocket server URL (default: ws://localhost:8000)

**Example — launch 5 robots for 10 minutes:**
```bash
python -m simulation.multi_robot_sim --count 5 --duration 600
```

**Example — launch 3 robots indefinitely:**
```bash
python -m simulation.multi_robot_sim --count 3 --duration 0
```

The simulator creates realistic robot behavior:
- Robots patrol between warehouse waypoints
- Battery drains over time, robots go to charging station
- Random task assignments with payload simulation
- Realistic encoder and IMU data
- SLAM keyframe generation

---

## Web AIS Interface

### Login Page
- JWT authentication with role-based access
- Demo credentials pre-displayed for testing
- Smooth animated transitions

**Demo accounts:**
- `admin` / `admin` — Full access
- `operator` / `operator` — Monitoring and task creation

### Dashboard
- Real-time statistics cards with animated counters
- Live warehouse map with robot positions
- Robot status panel with battery, position, and payload info
- Task summary (pending, active, completed)

### Robot Details
- Complete telemetry visualization:
  - Position (X, Y) and orientation
  - Linear and angular velocity
  - Stability score
  - Battery level with color coding
- Odometry and IMU section:
  - Left/right encoder values
  - IMU pitch and roll
- Gripper and payload status
- SLAM keyframes count
- Manual control buttons

### Warehouse Map
- Full warehouse layout with:
  - Storage racks (A-I zones)
  - Loading docks
  - Charging station
  - Obstacles (pillars)
  - Aisle labels
- Robot markers with:
  - Color-coded status
  - Direction indicator
  - Movement trails
  - Detailed popup on click

---

## Warehouse Map

The warehouse map is rendered using Leaflet.js with a custom coordinate system. The warehouse is 100x100 meters with:

- **9 storage racks** organized in 3 rows
- **2 loading docks** for pickup/dropoff
- **1 charging station** in the corner
- **2 structural pillars** as obstacles
- **Labeled aisles** for navigation reference

The map supports:
- Zoom and pan
- Robot position updates in real-time
- Movement trail visualization
- Zone popups with information

---

## API Documentation

Once the server is running, full API documentation is available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/login` | POST | User authentication |
| `/api/v1/auth/register` | POST | Register new user |
| `/api/v1/auth/me` | GET | Current user info |
| `/api/v1/robots` | GET | List all robots |
| `/api/v1/robots/{id}` | GET | Robot details |
| `/api/v1/robots/{id}` | PATCH | Update robot |
| `/api/v1/tasks` | GET | List tasks |
| `/api/v1/tasks` | POST | Create task |
| `/api/v1/tasks/{id}` | DELETE | Cancel task |
| `/api/v1/maps` | GET | List maps |
| `/api/v1/maps` | POST | Upload map |
| `/api/v1/logs` | GET | Query logs |
| `/ws/robot/{id}` | WS | Robot WebSocket |
| `/ws/client` | WS | Client WebSocket |

---

## Configuration

Key configuration files:

- **`config/hw_config.py`** — Hardware parameters, server settings, database URL
- **`web_ais/vite.config.ts`** — Vite build configuration
- **`web_ais/tailwind.config.js`** — Tailwind theme (if customized)

### Important Settings

```python
# Database (config/hw_config.py)
SERVER_CONFIG = {
    "database_url": "postgresql://user:pass@localhost:5432/genius_loci",
    # or for testing:
    # "database_url": "sqlite:///./genius_loci.db",
    "host": "0.0.0.0",
    "port": 8000,
    "jwt_secret": "your-secret-key-change-in-production",
    "cors_origins": ["http://localhost:5173"],
}
```

---

## Development Roadmap

- [x] Core navigation (SLAM, A*, DWA)
- [x] Stereo vision and depth mapping
- [x] ArUco marker detection
- [x] WebSocket real-time communication
- [x] Web AIS with authentication
- [x] Warehouse map visualization
- [x] Multi-robot simulation
- [x] Task dispatcher
- [x] Stability control
- [ ] YOLO cargo detection training
- [ ] PyBullet 3D simulation
- [ ] Physical robot integration
- [ ] Multi-robot collision avoidance
- [ ] Cloud deployment

---

## License

This project is developed for educational purposes as part of a diploma thesis at Kazan Innovative University.

---

**Author**: Tyurin Dmitry Aleksandrovich
**Supervisor**: Vafina Veronika Vladimirovna
**Institution**: College of Kazan Innovative University (KIU)
**Specialty**: 09.02.07 Information Systems and Programming

---

*Genius Loci — "The spirit of the place" — Bringing intelligence to warehouse logistics.*
