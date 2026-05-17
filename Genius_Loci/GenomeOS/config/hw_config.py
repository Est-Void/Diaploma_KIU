"""
Hardware and system configuration for Genius Loci GenomeOS.

All configurable parameters for robot hardware, sensors, navigation,
planning, communication, server, and web AIS.
"""
import logging

# =============================================================================
# Logging Configuration
# =============================================================================
LOGGING_CONFIG = {
    "level": logging.DEBUG,  # Change to INFO for less verbosity
    "format": "%(asctime)s | %(name)-20s | %(levelname)-7s | %(message)s",
    "handlers": [logging.StreamHandler()]
}

# =============================================================================
# Hardware Nodes Configuration (used by HardwareInterface)
# =============================================================================
NODES_CONFIG = {
    "limb_motor": {
        "max_angle_deg": 45.0,
        "max_speed_deg_per_sec": 60.0,
        "inertia_factor": 0.15,
        "friction_coeff": 0.05,
        "gravity_effect": 0.2
    },
    "wheel_motor": {
        "max_rpm": 120.0,
        "inertia_factor": 0.1,
        "rolling_resistance": 0.02,
        "load_effect": 0.05,
        "encoder_ticks_per_rev": 2048
    },
    "pneumatic_gripper": {
        "max_pressure_bar": 6.0,
        "pump_rate": 2.0,
        "leak_rate": 0.1,
        "grip_force_per_bar": 15.0
    },
    "pos_sensor": {
        "noise_std_dev": 0.5,
        "update_delay_ms": 10,
        "encoder_noise_std": 0.02,
        "imu_drift_rate": 0.001,
        "imu_noise_std": 0.005
    },
    "indicator": {
        "hw_pins": {"r": 17, "g": 27, "b": 22, "buzzer": 18}
    }
}

# =============================================================================
# Balance / Stability Controller
# =============================================================================
BALANCER_CONFIG = {
    "pitch_kp": 15.0,
    "pitch_ki": 0.5,
    "pitch_kd": 8.0,
    "roll_kp": 10.0,
    "roll_ki": 0.1,
    "roll_kd": 5.0,
    "max_limb_angle": 25.0,
    "speed_to_angle_gain": 0.2,
    "wheelbase_m": 0.4,
    "track_width_m": 0.3,
    "gripper_leverage_m": 0.15,
    "emergency_tilt_threshold_deg": 25.0
}

# =============================================================================
# Robot Physical Parameters
# =============================================================================
ROBOT_CONFIG = {
    "wheelbase_m": 0.45,
    "track_width_m": 0.32,
    "wheel_diameter_m": 0.15,
    "max_speed_mps": 1.2,
    "max_angular_speed_rps": 1.5,
    "mass_kg": 30.0,
    "max_payload_kg": 80.0
}

# =============================================================================
# Stereo Vision Configuration
# =============================================================================
STEREO_CONFIG = {
    "baseline_m": 0.12,
    "focal_length_px": 800.0,
    "min_depth_m": 0.3,
    "max_depth_m": 10.0,
    "image_width": 1280,
    "image_height": 720,
    "sgbm_window_size": 5,
    "sgbm_min_disparity": 0,
    "sgbm_num_disparities": 128,
    "sgbm_block_size": 5
}

# =============================================================================
# ArUco Marker Detection
# =============================================================================
ARUCO_CONFIG = {
    "marker_length_m": 0.165,
    "dictionary": "DICT_4X4_50",
    "camera_matrix": None,
    "dist_coeffs": None
}

# =============================================================================
# SLAM (Simultaneous Localization and Mapping)
# =============================================================================
SLAM_CONFIG = {
    "map_resolution_m": 0.05,
    "map_size_m": 100.0,
    "lidar_range_m": 12.0,
    "loop_closure_threshold": 0.85,
    "loop_closure_min_distance_m": 5.0,
    "scan_matching_max_iter": 20,
    "scan_matching_tolerance_m": 0.1
}

# =============================================================================
# Path Planning (A* and DWA)
# =============================================================================
PLANNING_CONFIG = {
    # A* global planner
    "astar_heuristic": "euclidean",
    "astar_inflation_radius_m": 0.3,
    "astar_max_iterations": 50000,
    "grid_resolution_m": 0.1,
    # DWA local planner
    "dwa_sim_time": 3.0,
    "dwa_dt": 0.1,
    "dwa_max_speed": 1.0,
    "dwa_max_angular_speed": 1.0,
    "dwa_acceleration_limit": 0.5,
    "dwa_angular_accel_limit": 0.8,
    "dwa_obstacle_margin_m": 0.5,
    "dwa_goal_distance_weight": 1.0,
    "dwa_speed_weight": 0.5,
    "dwa_obstacle_weight": 2.0,
    "dwa_heading_weight": 0.8,
    "dwa_num_speed_samples": 20,
    "dwa_num_angular_samples": 20
}

# =============================================================================
# Communication (ZeroMQ)
# =============================================================================
COMMS_CONFIG = {
    "robot_id": "genius_loci_001",
    "zeromq_pub_addr": "tcp://127.0.0.1:5555",
    "zeromq_sub_addr": "tcp://127.0.0.1:5556",
    "zeromq_cmd_addr": "tcp://127.0.0.1:5557",
    "telemetry_rate_hz": 5
}

# =============================================================================
# MQTT (Legacy) — used by communication/robot_gateway.py
# =============================================================================
MQTT_CONFIG = {
    "broker_address": "127.0.0.1",
    "broker_port": 1883,
    "robot_id": "rover_01",
    "keepalive": 60,
    "qos": 1,
    "telemetry_interval_sec": 1.0
}

# =============================================================================
# Server Configuration (FastAPI + PostgreSQL)
# =============================================================================
SERVER_CONFIG = {
    "database_url": "sqlite:///./genius_loci.db",
    "host": "0.0.0.0",
    "port": 8000,
    "jwt_secret": "change-this-secret-in-production",
    "jwt_algorithm": "HS256",
    "jwt_expire_hours": 24,
    "cors_origins": ["http://localhost:5173"]
}