"""
Hardware and system configuration for Genius Loci GenomeOS.
Centralized configuration for all robot subsystems.
"""
import logging

# =============================================================================
# LOGGING CONFIGURATION
# =============================================================================
LOGGING_CONFIG = {
    "level": logging.DEBUG,
    "format": "%(asctime)s | %(name)-25s | %(levelname)-7s | %(message)s",
    "handlers": [logging.StreamHandler()]
}

# =============================================================================
# PHYSICAL ROBOT PARAMETERS
# =============================================================================
ROBOT_CONFIG = {
    "name": "Genius Loci",
    "version": "0.2.0",
    "mass_kg": 30.0,              # Robot mass without payload
    "max_payload_kg": 80.0,       # Maximum payload
    "wheelbase_m": 0.45,          # Distance between front and rear axles
    "track_width_m": 0.32,        # Distance between left and right wheels
    "wheel_diameter_m": 0.15,     # Wheel diameter
    "max_speed_mps": 1.2,         # Maximum linear speed
    "max_angular_speed_rps": 1.5, # Maximum angular speed
    "gripper_leverage_m": 0.25,   # Gripper moment arm
}

# =============================================================================
# MOTOR CONFIGURATIONS
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
        "max_rpm": 150.0,
        "inertia_factor": 0.1,
        "rolling_resistance": 0.02,
        "load_effect": 0.05,
        "encoder_ticks_per_rev": 1024
    },
    "pneumatic_gripper": {
        "max_pressure_bar": 6.0,
        "pump_rate": 2.0,
        "leak_rate": 0.1,
        "grip_force_per_bar": 15.0,
        "grip_width_m": 0.4,
        "max_grip_force_n": 200.0
    },
    "pos_sensor": {
        "noise_std_dev": 0.5,
        "update_delay_ms": 10,
        "encoder_noise_std": 2.0,
        "imu_drift_rate": 0.001,
        "imu_noise_std": 0.05
    }
}

# =============================================================================
# BALANCER / STABILITY CONTROL
# =============================================================================
BALANCER_CONFIG = {
    "pitch_kp": 15.0,
    "pitch_ki": 0.5,
    "pitch_kd": 8.0,
    "roll_kp": 10.0,
    "roll_ki": 0.3,
    "roll_kd": 5.0,
    "max_limb_angle": 30.0,
    "speed_to_angle_gain": 5.0,
    "stability_threshold": 0.85,
    "emergency_tilt_threshold_deg": 25.0
}

# =============================================================================
# STEREO VISION CONFIGURATION
# =============================================================================
STEREO_CONFIG = {
    "baseline_m": 0.12,           # Distance between cameras (B)
    "focal_length_px": 800.0,     # Focal length in pixels (f)
    "image_width": 1280,
    "image_height": 720,
    "fps": 15,
    "sgbm_window_size": 5,
    "sgbm_min_disparity": 0,
    "sgbm_num_disparities": 128,
    "sgbm_block_size": 5,
    "min_depth_m": 0.3,
    "max_depth_m": 10.0,
    "calibration_file": "config/stereo_calibration.yaml"
}

# =============================================================================
# ARUCO MARKER CONFIGURATION
# =============================================================================
ARUCO_CONFIG = {
    "dictionary": "DICT_4X4_50",
    "marker_length_m": 0.165,
    "detection_mode": "DETECT_MODE",
    "camera_matrix": None,        # Loaded from calibration
    "dist_coeffs": None
}

# =============================================================================
# SLAM CONFIGURATION
# =============================================================================
SLAM_CONFIG = {
    "map_resolution_m": 0.05,
    "map_size_m": 100.0,          # 100x100m max map
    "lidar_range_m": 12.0,
    "lidar_angles": 360,
    "scan_matching_max_iter": 20,
    "scan_matching_tolerance_m": 0.1,
    "loop_closure_threshold": 0.85,
    "loop_closure_min_distance_m": 5.0,
    "pose_graph_optimization": True,
    "local_map_size": 20,         # 20x20m local map window
    "odometry_weight": 0.7,
    "scan_weight": 0.3
}

# =============================================================================
# PATH PLANNING CONFIGURATION
# =============================================================================
PLANNING_CONFIG = {
    # A* Global Planner
    "astar_heuristic": "euclidean",
    "astar_inflation_radius_m": 0.3,
    "astar_max_iterations": 50000,
    "grid_resolution_m": 0.1,

    # DWA Local Planner
    "dwa_sim_time": 3.0,
    "dwa_dt": 0.1,
    "dwa_max_speed": 1.0,
    "dwa_max_angular_speed": 1.0,
    "dwa_acceleration_limit": 0.5,
    "dwa_angular_accel_limit": 0.8,
    "dwa_goal_distance_weight": 1.0,
    "dwa_speed_weight": 0.5,
    "dwa_obstacle_weight": 2.0,
    "dwa_heading_weight": 0.8,
    "dwa_num_speed_samples": 20,
    "dwa_num_angular_samples": 20,
    "dwa_obstacle_margin_m": 0.5,

    # Costmap
    "costmap_inflation_radius_m": 0.5,
    "costmap_obstacle_radius_m": 0.1
}

# =============================================================================
# COMMUNICATION CONFIGURATION
# =============================================================================
COMMS_CONFIG = {
    "robot_id": "genius_loci_001",
    "server_host": "localhost",
    "server_port": 8000,
    "websocket_port": 8001,
    "zeromq_pub_addr": "tcp://127.0.0.1:5555",
    "zeromq_sub_addr": "tcp://127.0.0.1:5556",
    "zeromq_cmd_addr": "tcp://127.0.0.1:5557",
    "telemetry_rate_hz": 5,
    "heartbeat_timeout_s": 10,
    "reconnect_interval_s": 5
}

# =============================================================================
# SERVER CONFIGURATION
# =============================================================================
SERVER_CONFIG = {
    "host": "0.0.0.0",
    "port": 8000,
    "database_url": "postgresql://genius:genius@localhost:5432/genius_loci",
    "jwt_secret": "genius-loci-secret-key-2026",
    "jwt_expiration_hours": 24,
    "cors_origins": ["http://localhost:3000", "http://localhost:5173"],
    "max_robots": 50,
    "max_operators": 20,
    "task_assignment_interval_s": 5
}
