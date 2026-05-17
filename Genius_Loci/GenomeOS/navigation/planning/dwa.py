"""
Dynamic Window Approach (DWA) local planner for obstacle avoidance.
Real-time trajectory optimization with kinodynamic constraints.
"""
import numpy as np
import math
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass
from core.logger import get_logger


@dataclass
class RobotState:
    """Robot kinematic state."""
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0
    v: float = 0.0  # linear velocity
    w: float = 0.0  # angular velocity


@dataclass
class DWAConfig:
    """DWA configuration parameters."""
    sim_time: float = 3.0
    dt: float = 0.1
    max_speed: float = 1.0
    max_angular_speed: float = 1.0
    accel_limit: float = 0.5
    angular_accel_limit: float = 0.8
    obstacle_margin: float = 0.5
    goal_weight: float = 1.0
    speed_weight: float = 0.5
    obstacle_weight: float = 2.0
    heading_weight: float = 0.8
    num_v_samples: int = 20
    num_w_samples: int = 20


class DWAPlanner:
    """Dynamic Window Approach local trajectory planner."""

    def __init__(self, config: Dict[str, Any]):
        self.logger = get_logger("Planning.DWA")

        self.cfg = DWAConfig(
            sim_time=config.get("dwa_sim_time", 3.0),
            dt=config.get("dwa_dt", 0.1),
            max_speed=config.get("dwa_max_speed", 1.0),
            max_angular_speed=config.get("dwa_max_angular_speed", 1.0),
            accel_limit=config.get("dwa_acceleration_limit", 0.5),
            angular_accel_limit=config.get("dwa_angular_accel_limit", 0.8),
            obstacle_margin=config.get("dwa_obstacle_margin_m", 0.5),
            goal_weight=config.get("dwa_goal_distance_weight", 1.0),
            speed_weight=config.get("dwa_speed_weight", 0.5),
            obstacle_weight=config.get("dwa_obstacle_weight", 2.0),
            heading_weight=config.get("dwa_heading_weight", 0.8),
            num_v_samples=config.get("dwa_num_speed_samples", 20),
            num_w_samples=config.get("dwa_num_angular_samples", 20)
        )

        self._obstacles: List[Tuple[float, float]] = []
        self._trajectory: List[RobotState] = []
        self.logger.info("DWA planner initialized")

    def plan(self, current_state: RobotState, goal: Tuple[float, float],
             obstacles: List[Tuple[float, float]]) -> Tuple[float, float]:
        """
        Compute optimal velocity command using DWA.

        Args:
            current_state: Current robot state
            goal: (x, y) goal position
            obstacles: List of (x, y) obstacle positions

        Returns:
            (linear_velocity, angular_velocity) command
        """
        self._obstacles = obstacles

        # Calculate dynamic window
        dw = self._calculate_dynamic_window(current_state)

        # Sample trajectories
        best_score = -float('inf')
        best_command = (0.0, 0.0)
        best_trajectory = []

        v_samples = np.linspace(dw[0], dw[1], self.cfg.num_v_samples)
        w_samples = np.linspace(dw[2], dw[3], self.cfg.num_w_samples)

        for v in v_samples:
            for w in w_samples:
                trajectory = self._simulate_trajectory(current_state, v, w)
                score = self._evaluate_trajectory(trajectory, goal)

                if score > best_score:
                    best_score = score
                    best_command = (v, w)
                    best_trajectory = trajectory

        self._trajectory = best_trajectory

        # Slow down if approaching goal
        dist_to_goal = math.sqrt((goal[0]-current_state.x)**2 + (goal[1]-current_state.y)**2)
        if dist_to_goal < 0.5:
            best_command = (best_command[0] * dist_to_goal / 0.5, best_command[1])

        return best_command

    def _calculate_dynamic_window(self, state: RobotState) -> Tuple[float, float, float, float]:
        """
        Calculate dynamic window [v_min, v_max, w_min, w_max].
        """
        # Kinematic limits
        v_min = -self.cfg.max_speed
        v_max = self.cfg.max_speed
        w_min = -self.cfg.max_angular_speed
        w_max = self.cfg.max_angular_speed

        # Dynamic constraints (acceleration limits)
        v_low = state.v - self.cfg.accel_limit * self.cfg.dt
        v_high = state.v + self.cfg.accel_limit * self.cfg.dt
        w_low = state.w - self.cfg.angular_accel_limit * self.cfg.dt
        w_high = state.w + self.cfg.angular_accel_limit * self.cfg.dt

        return (max(v_min, v_low), min(v_max, v_high),
                max(w_min, w_low), min(w_max, w_high))

    def _simulate_trajectory(self, state: RobotState, v: float, 
                             w: float) -> List[RobotState]:
        """Simulate trajectory with constant velocity."""
        trajectory = [RobotState(state.x, state.y, state.theta, state.v, state.w)]

        sim_steps = int(self.cfg.sim_time / self.cfg.dt)
        x, y, theta = state.x, state.y, state.theta

        for _ in range(sim_steps):
            theta += w * self.cfg.dt
            x += v * math.cos(theta) * self.cfg.dt
            y += v * math.sin(theta) * self.cfg.dt
            trajectory.append(RobotState(x, y, theta, v, w))

        return trajectory

    def _evaluate_trajectory(self, trajectory: List[RobotState], 
                             goal: Tuple[float, float]) -> float:
        """Evaluate trajectory with weighted objective function."""
        final = trajectory[-1]

        # Goal distance score (higher = closer to goal)
        dist_to_goal = math.sqrt((final.x - goal[0])**2 + (final.y - goal[1])**2)
        goal_score = 1.0 / (1.0 + dist_to_goal)

        # Heading alignment
        dx = goal[0] - final.x
        dy = goal[1] - final.y
        goal_angle = math.atan2(dy, dx)
        angle_diff = abs(self._normalize_angle(goal_angle - final.theta))
        heading_score = 1.0 / (1.0 + angle_diff)

        # Speed score (prefer forward motion)
        speed_score = abs(final.v) / self.cfg.max_speed

        # Obstacle clearance
        min_obstacle_dist = float('inf')
        for obs in self._obstacles:
            for t in trajectory:
                dist = math.sqrt((t.x - obs[0])**2 + (t.y - obs[1])**2)
                min_obstacle_dist = min(min_obstacle_dist, dist)

        if min_obstacle_dist < self.cfg.obstacle_margin:
            obstacle_score = -1000  # Collision
        else:
            obstacle_score = min(1.0, min_obstacle_dist / 3.0)

        # Combined score
        score = (self.cfg.goal_weight * goal_score +
                 self.cfg.heading_weight * heading_score +
                 self.cfg.speed_weight * speed_score +
                 self.cfg.obstacle_weight * obstacle_score)

        return score

    @staticmethod
    def _normalize_angle(angle: float) -> float:
        """Normalize angle to [-pi, pi]."""
        while angle > math.pi:
            angle -= 2 * math.pi
        while angle < -math.pi:
            angle += 2 * math.pi
        return angle

    def get_best_trajectory(self) -> List[Tuple[float, float]]:
        """Get the best trajectory as list of (x, y) points."""
        return [(t.x, t.y) for t in self._trajectory]
