# Genius Loci - Autonomous Warehouse Robot System

## Project Structure

```
Genius_Loci/
└── GenomeOS/
    ├── main.py                          # Main orchestrator entry point
    ├── config/                          # Configuration files
    │   ├── hw_config.py                 # Hardware & system configuration
    │   └── system_config.py             # System-wide config loader
    ├── core/                            # Core control utilities
    │   ├── __init__.py
    │   ├── balancer.py                  # Balancer controller with CoM compensation
    │   ├── pid.py                       # PID controller with anti-windup
    │   └── logger.py                    # Structured logging with JSON output
    ├── hw_abstraction/                  # Hardware abstraction layer
    │   ├── __init__.py
    │   ├── base_node.py                 # Abstract base for hardware nodes
    │   ├── hardware_interface.py        # Central hardware management
    │   ├── wheel_motor.py               # Simulated wheel motor
    │   ├── limb_motor.py                # Simulated limb motor
    │   ├── pneumatic_gripper.py         # Simulated pneumatic gripper
    │   ├── pos_sensor.py                # Simulated position sensor
    │   └── real_nodes.py                # Real hardware stubs (RPi)
    ├── sensors/                         # Sensor emulators
    │   ├── __init__.py
    │   ├── encoder_emulator.py          # Wheel encoder with noise/slip
    │   ├── imu_emulator.py              # IMU with drift and noise
    │   └── stereo_emulator.py           # Stereo camera emulator
    ├── navigation/                      # Navigation stack
    │   ├── __init__.py
    │   ├── slam/
    │   │   ├── __init__.py
    │   │   └── slam_module.py           # Graph-based SLAM with ICP
    │   └── planning/
    │       ├── __init__.py
    │       ├── astar.py                 # A* global path planner
    │       └── dwa.py                   # DWA local planner
    ├── perception/                      # Computer vision
    │   ├── __init__.py
    │   ├── stereo/
    │   │   ├── __init__.py
    │   │   └── stereo_module.py         # Stereo depth (SGBM)
    │   └── detection/
    │       ├── __init__.py
    │       ├── aruco_detector.py        # ArUco marker detection
    │       └── yolo_detector.py         # YOLO cargo detection
    ├── control/                         # Control systems
    │   ├── __init__.py
    │   ├── movement.py                  # Movement control with kinematics
    │   └── gripper.py                   # Gripper state machine
    ├── communication/                   # Communication
    │   ├── __init__.py
    │   └── zeromq_bus.py                # ZeroMQ pub/sub bus
    ├── server/                          # FastAPI dispatch server
    │   ├── __init__.py
    │   ├── main.py                      # FastAPI application
    │   └── app/
    │       ├── __init__.py
    │       ├── models/
    │       │   ├── __init__.py
    │       │   └── database.py          # SQLAlchemy models (PostgreSQL)
    │       ├── schemas/
    │       │   ├── __init__.py
    │       │   └── schemas.py           # Pydantic request/response schemas
    │       ├── routers/
    │       │   ├── __init__.py
    │       │   ├── auth.py              # JWT authentication
    │       │   ├── robots.py            # Robot CRUD
    │       │   ├── tasks.py             # Task management
    │       │   ├── maps.py              # Map storage
    │       │   └── logs.py              # System logs
    │       └── services/
    │           ├── __init__.py
    │           ├── websocket_manager.py # WebSocket connection manager
    │           └── dispatcher.py        # Automatic task dispatcher
    ├── web_ais/                         # React web dashboard
    │   ├── package.json
    │   ├── index.html
    │   ├── vite.config.ts
    │   ├── tsconfig.json
    │   └── src/
    │       ├── main.tsx
    │       ├── App.tsx
    │       ├── index.css
    │       ├── store.ts                 # Zustand state management
    │       ├── vite-env.d.ts
    │       ├── components/
    │       │   ├── Layout.tsx           # Sidebar layout
    │       │   └── RobotMap.tsx         # Leaflet map component
    │       ├── pages/
    │       │   ├── Dashboard.tsx        # Main dashboard
    │       │   ├── TaskManager.tsx      # Task CRUD
    │       │   ├── MapViewer.tsx        # Full-screen map
    │       │   ├── RobotDetails.tsx     # Robot detail view
    │       │   ├── LogsViewer.tsx       # Log viewer
    │       │   └── Settings.tsx         # Settings page
    │       └── hooks/
    │           └── useWebSocket.ts      # WebSocket hook
    ├── requirements.txt
    └── README.md
```

## Quick Start

### Robot Software
```bash
# Install dependencies
pip install -r requirements.txt

# Run in simulation mode (default)
python main.py --sim

# Run with real hardware
python main.py --real
```

### Server
```bash
# Setup PostgreSQL database
createdb genius_loci

# Start server
python server/main.py

# API documentation available at http://localhost:8000/docs
```

### Web Dashboard
```bash
cd web_ais
npm install
npm run dev
# Open http://localhost:3000
```

## Implemented Modules

### Robot Software (GenomeOS)
- [x] Hardware abstraction layer with simulation mode
- [x] PID controller with anti-windup
- [x] Balancer with center of mass compensation
- [x] Sensor emulators (encoder, IMU, stereo camera)
- [x] Stereo vision depth map generation (SGBM)
- [x] ArUco marker detection with pose estimation
- [x] YOLO cargo detection
- [x] Graph-based SLAM with scan matching
- [x] A* global path planner with costmap
- [x] DWA local planner for obstacle avoidance
- [x] Movement control with differential drive kinematics
- [x] Gripper control state machine
- [x] ZeroMQ communication bus

### Server
- [x] FastAPI with automatic OpenAPI docs
- [x] PostgreSQL database with SQLAlchemy ORM
- [x] JWT authentication with role-based access
- [x] Robot CRUD and state management
- [x] Task creation, assignment, and tracking
- [x] Map storage and retrieval
- [x] System logging
- [x] WebSocket real-time communication
- [x] Automatic task dispatcher

### Web Dashboard
- [x] React + TypeScript + Vite
- [x] Leaflet interactive map with robot markers
- [x] Real-time telemetry via WebSocket
- [x] Task creation and management
- [x] Robot status monitoring
- [x] System logs viewer
- [x] Responsive sidebar layout
