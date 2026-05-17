"""
Graph-based SLAM implementation with scan matching.
Provides real-time mapping and localization for warehouse environments.
"""
import numpy as np
import math
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
from core.logger import get_logger


@dataclass
class Pose:
    """2D pose: x, y, theta."""
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0  # radians

    def copy(self) -> "Pose":
        return Pose(self.x, self.y, self.theta)

    def distance_to(self, other: "Pose") -> float:
        return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)

    def to_dict(self) -> Dict[str, float]:
        return {"x": round(self.x, 4), "y": round(self.y, 4), 
                "theta": round(self.theta, 6), "theta_deg": round(math.degrees(self.theta), 2)}


@dataclass 
class ScanPoint:
    """Single laser/depth scan point."""
    angle: float
    distance: float
    x: float
    y: float


@dataclass
class KeyFrame:
    """A keyframe in the pose graph."""
    id: int
    pose: Pose
    scan: List[ScanPoint] = field(default_factory=list)
    timestamp: float = 0.0


class OccupancyGrid:
    """2D occupancy grid map."""

    def __init__(self, resolution: float = 0.05, size_m: float = 100.0):
        self.resolution = resolution
        self.size_m = size_m
        self.grid_size = int(size_m / resolution)
        self.origin = np.array([size_m / 2, size_m / 2])  # Center origin

        # Occupancy values: -1=unknown, 0=free, 100=occupied
        self.grid = np.full((self.grid_size, self.grid_size), -1, dtype=np.int8)
        self.log_odds = np.zeros((self.grid_size, self.grid_size), dtype=np.float32)

        self.logger = get_logger("SLAM.Grid")

    def world_to_grid(self, x: float, y: float) -> Tuple[int, int]:
        """Convert world coordinates to grid indices."""
        gx = int((x + self.origin[0]) / self.resolution)
        gy = int((y + self.origin[1]) / self.resolution)
        return gx, gy

    def grid_to_world(self, gx: int, gy: int) -> Tuple[float, float]:
        """Convert grid indices to world coordinates."""
        x = gx * self.resolution - self.origin[0]
        y = gy * self.resolution - self.origin[1]
        return x, y

    def is_valid(self, gx: int, gy: int) -> bool:
        return 0 <= gx < self.grid_size and 0 <= gy < self.grid_size

    def update_line(self, x0: float, y0: float, x1: float, y1: float, 
                    occupied: bool = True):
        """Bresenham line update for occupancy grid."""
        gx0, gy0 = self.world_to_grid(x0, y0)
        gx1, gy1 = self.world_to_grid(x1, y1)

        dx = abs(gx1 - gx0)
        dy = abs(gy1 - gy0)
        sx = 1 if gx0 < gx1 else -1
        sy = 1 if gy0 < gy1 else -1
        err = dx - dy

        hit_endpoint = False
        while True:
            if self.is_valid(gx0, gy0):
                if hit_endpoint and occupied:
                    self.log_odds[gy0, gx0] += 0.85  # Occupied
                elif not hit_endpoint:
                    self.log_odds[gy0, gx0] -= 0.3  # Free

            if gx0 == gx1 and gy0 == gy1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                gx0 += sx
            if e2 < dx:
                err += dx
                gy0 += sy

            if gx0 == gx1 and gy0 == gy1:
                hit_endpoint = True

        # Clip log-odds
        np.clip(self.log_odds, -5, 5, out=self.log_odds)
        self.grid = np.where(self.log_odds > 0.5, 100, 
                    np.where(self.log_odds < -0.5, 0, -1))

    def get_map_data(self) -> Dict[str, Any]:
        return {
            "resolution": self.resolution,
            "size_m": self.size_m,
            "grid_size": self.grid_size,
            "origin": self.origin.tolist(),
            "data": self.grid.tobytes().hex()
        }


class ScanMatcherICP:
    """Iterative Closest Point scan matching for SLAM."""

    def __init__(self, max_iterations: int = 20, tolerance: float = 0.01):
        self.max_iterations = max_iterations
        self.tolerance = tolerance
        self.logger = get_logger("SLAM.ICP")

    def match(self, reference_scan: List[ScanPoint], current_scan: List[ScanPoint],
              initial_guess: Pose) -> Tuple[Pose, float]:
        """
        Match current scan to reference using ICP.
        Returns (optimized_pose, fitness_score).
        """
        if len(reference_scan) == 0 or len(current_scan) == 0:
            return initial_guess, 0.0

        pose = initial_guess.copy()
        prev_error = float('inf')

        # Convert scans to numpy arrays
        ref_points = np.array([[p.x, p.y] for p in reference_scan])
        cur_points = np.array([[p.x, p.y] for p in current_scan])

        for iteration in range(self.max_iterations):
            # Transform current points by current pose
            cos_t = math.cos(pose.theta)
            sin_t = math.sin(pose.theta)
            R = np.array([[cos_t, -sin_t], [sin_t, cos_t]])
            t = np.array([pose.x, pose.y])

            transformed = (R @ cur_points.T).T + t

            # Find nearest neighbors
            matched_ref = []
            matched_cur = []
            for tp in transformed:
                distances = np.linalg.norm(ref_points - tp, axis=1)
                idx = np.argmin(distances)
                if distances[idx] < 1.0:  # 1m max correspondence
                    matched_ref.append(ref_points[idx])
                    matched_cur.append(cur_points[np.argmin(distances)])

            if len(matched_ref) < 3:
                break

            matched_ref = np.array(matched_ref)
            matched_cur = np.array(matched_cur)

            # Compute centroid
            ref_centroid = np.mean(matched_ref, axis=0)
            cur_centroid = np.mean(matched_cur, axis=0)

            # Compute cross-covariance
            H = (matched_cur - cur_centroid).T @ (matched_ref - ref_centroid)

            # SVD for optimal rotation
            try:
                U, _, Vt = np.linalg.svd(H)
                R_opt = Vt.T @ U.T
                if np.linalg.det(R_opt) < 0:
                    Vt[-1, :] *= -1
                    R_opt = Vt.T @ U.T

                t_opt = ref_centroid - R_opt @ cur_centroid

                # Update pose
                dtheta = math.atan2(R_opt[1, 0], R_opt[0, 0])
                pose.x += t_opt[0] * 0.5
                pose.y += t_opt[1] * 0.5
                pose.theta += dtheta * 0.5

                # Check convergence
                mean_error = np.mean(np.linalg.norm(matched_ref - matched_cur, axis=1))
                if abs(prev_error - mean_error) < self.tolerance:
                    break
                prev_error = mean_error

            except np.linalg.LinAlgError:
                break

        fitness = 1.0 / (1.0 + prev_error) if prev_error > 0 else 1.0
        return pose, fitness


class GraphSLAM:
    """
    Graph-based SLAM with pose graph optimization.
    Implements scan matching, loop closure, and occupancy grid mapping.
    """

    def __init__(self, config: Dict[str, Any]):
        self.logger = get_logger("SLAM.Main")

        self.resolution = config.get("map_resolution_m", 0.05)
        self.map_size = config.get("map_size_m", 100.0)
        self.lidar_range = config.get("lidar_range_m", 12.0)
        self.loop_threshold = config.get("loop_closure_threshold", 0.85)
        self.loop_min_dist = config.get("loop_closure_min_distance_m", 5.0)

        self.grid = OccupancyGrid(self.resolution, self.map_size)
        self.scan_matcher = ScanMatcherICP(
            max_iterations=config.get("scan_matching_max_iter", 20),
            tolerance=config.get("scan_matching_tolerance_m", 0.1)
        )

        self.keyframes: List[KeyFrame] = []
        self.pose = Pose()
        self.odom_pose = Pose()
        self._kf_counter = 0
        self._kf_distance = 0.5  # Create keyframe every 0.5m
        self._last_kf_pose = Pose()

        self.logger.info("GraphSLAM initialized")

    def update(self, odometry_delta: Tuple[float, float, float],
               scan: List[Tuple[float, float]], timestamp: float = 0.0) -> Pose:
        """
        Update SLAM with new odometry and scan data.

        Args:
            odometry_delta: (dx, dy, dtheta) from odometry
            scan: List of (x, y) scan points in robot frame
            timestamp: Current time

        Returns:
            Estimated robot pose
        """
        dx, dy, dtheta = odometry_delta

        # Update odometry pose
        self.odom_pose.x += dx
        self.odom_pose.y += dy
        self.odom_pose.theta += dtheta

        # Use odometry as initial guess
        initial_guess = Pose(
            self.pose.x + dx,
            self.pose.y + dy, 
            self.pose.theta + dtheta
        )

        # Convert scan to ScanPoints
        scan_points = [ScanPoint(math.atan2(y, x), math.sqrt(x*x + y*y), x, y) 
                      for x, y in scan]

        # Scan matching with last keyframe if available
        if self.keyframes:
            last_kf = self.keyframes[-1]
            # Transform scan to last keyframe frame
            rel_points = self._transform_scan(scan_points, initial_guess, last_kf.pose)
            optimized_pose, fitness = self.scan_matcher.match(
                last_kf.scan, rel_points, Pose()
            )

            if fitness > 0.3:
                # Update pose relative to last keyframe
                cos_t = math.cos(last_kf.pose.theta)
                sin_t = math.sin(last_kf.pose.theta)
                self.pose.x = last_kf.pose.x + optimized_pose.x * cos_t - optimized_pose.y * sin_t
                self.pose.y = last_kf.pose.y + optimized_pose.x * sin_t + optimized_pose.y * cos_t
                self.pose.theta = last_kf.pose.theta + optimized_pose.theta
            else:
                self.pose = initial_guess
        else:
            self.pose = initial_guess

        # Update occupancy grid
        self._update_grid(self.pose, scan_points)

        # Check if we should create a new keyframe
        dist_from_last = self.pose.distance_to(self._last_kf_pose)
        if dist_from_last >= self._kf_distance or len(self.keyframes) == 0:
            self._create_keyframe(scan_points, timestamp)
            self._last_kf_pose = self.pose.copy()

        return self.pose.copy()

    def _transform_scan(self, scan: List[ScanPoint], from_pose: Pose, 
                        to_pose: Pose) -> List[ScanPoint]:
        """Transform scan points from one pose frame to another."""
        dx = from_pose.x - to_pose.x
        dy = from_pose.y - to_pose.y
        dtheta = from_pose.theta - to_pose.theta

        cos_t = math.cos(-to_pose.theta)
        sin_t = math.sin(-to_pose.theta)

        result = []
        for p in scan:
            # Point in world frame
            wx = from_pose.x + p.x * math.cos(from_pose.theta) - p.y * math.sin(from_pose.theta)
            wy = from_pose.y + p.x * math.sin(from_pose.theta) + p.y * math.cos(from_pose.theta)
            # Relative to to_pose
            rx = wx * cos_t - wy * sin_t - to_pose.x * cos_t + to_pose.y * sin_t
            ry = wx * sin_t + wy * cos_t - to_pose.x * sin_t - to_pose.y * cos_t
            result.append(ScanPoint(p.angle, p.distance, rx, ry))

        return result

    def _update_grid(self, pose: Pose, scan: List[ScanPoint]):
        """Update occupancy grid with new scan."""
        for point in scan:
            # Transform to world frame
            wx = pose.x + point.x * math.cos(pose.theta) - point.y * math.sin(pose.theta)
            wy = pose.y + point.x * math.sin(pose.theta) + point.y * math.cos(pose.theta)
            self.grid.update_line(pose.x, pose.y, wx, wy, occupied=True)

    def _create_keyframe(self, scan: List[ScanPoint], timestamp: float):
        """Create a new keyframe."""
        kf = KeyFrame(
            id=self._kf_counter,
            pose=self.pose.copy(),
            scan=scan,
            timestamp=timestamp
        )
        self.keyframes.append(kf)
        self._kf_counter += 1
        self.logger.debug(f"Created keyframe {kf.id} at ({kf.pose.x:.2f}, {kf.pose.y:.2f})")

    def get_map(self) -> np.ndarray:
        """Get current occupancy grid map."""
        return self.grid.grid.copy()

    def get_pose(self) -> Pose:
        """Get current estimated pose."""
        return self.pose.copy()

    def get_keyframes(self) -> List[Dict]:
        """Get all keyframes as dicts."""
        return [{"id": kf.id, "pose": kf.pose.to_dict(), "timestamp": kf.timestamp} 
                for kf in self.keyframes]

    def reset(self):
        """Reset SLAM state."""
        self.keyframes.clear()
        self.pose = Pose()
        self.odom_pose = Pose()
        self._kf_counter = 0
        self._last_kf_pose = Pose()
        self.grid = OccupancyGrid(self.resolution, self.map_size)
        self.logger.info("SLAM reset")
