"""
A* path planner with costmap and obstacle inflation.
Implements global path planning on occupancy grids.
"""
import numpy as np
import math
import heapq
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, field
from core.logger import get_logger


@dataclass(order=True)
class Node:
    """A* search node."""
    f_score: float = 0.0
    g_score: float = 0.0
    position: Tuple[int, int] = field(default_factory=tuple, compare=False)
    parent: Optional["Node"] = field(default=None, compare=False)

    def __hash__(self):
        return hash(self.position)

    def __eq__(self, other):
        return isinstance(other, Node) and self.position == other.position


class CostMap:
    """Cost map with obstacle inflation for path planning."""

    def __init__(self, occupancy_grid: np.ndarray, resolution: float = 0.1,
                 inflation_radius_m: float = 0.5, obstacle_radius_m: float = 0.1):
        self.logger = get_logger("Planning.CostMap")
        self.resolution = resolution
        self.inflation_radius = int(inflation_radius_m / resolution)
        self.obstacle_radius = int(obstacle_radius_m / resolution)

        # Downsample occupancy grid to costmap resolution
        h, w = occupancy_grid.shape
        self.width = w
        self.height = h
        self.costmap = self._create_costmap(occupancy_grid)

    def _create_costmap(self, grid: np.ndarray) -> np.ndarray:
        """Create cost map with inflated obstacles."""
        costmap = np.zeros((self.height, self.width), dtype=np.float32)

        # Mark occupied cells
        occupied = (grid == 100)
        costmap[occupied] = 100.0

        # Inflate obstacles
        for y in range(self.height):
            for x in range(self.width):
                if costmap[y, x] >= 100:
                    self._inflate(costmap, x, y)

        return costmap

    def _inflate(self, costmap: np.ndarray, ox: int, oy: int):
        """Inflate obstacle at (ox, oy)."""
        for dy in range(-self.inflation_radius, self.inflation_radius + 1):
            for dx in range(-self.inflation_radius, self.inflation_radius + 1):
                dist = math.sqrt(dx*dx + dy*dy)
                if dist <= self.inflation_radius:
                    nx, ny = ox + dx, oy + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        cost = 100.0 * (1.0 - dist / self.inflation_radius)
                        costmap[ny, nx] = max(costmap[ny, nx], cost)

    def get_cost(self, x: int, y: int) -> float:
        if 0 <= x < self.width and 0 <= y < self.height:
            return self.costmap[y, x]
        return 1000.0  # Out of bounds = high cost

    def is_free(self, x: int, y: int) -> bool:
        return self.get_cost(x, y) < 50.0


class AStarPlanner:
    """A* global path planner."""

    def __init__(self, config: Dict[str, Any]):
        self.logger = get_logger("Planning.AStar")
        self.heuristic_type = config.get("astar_heuristic", "euclidean")
        self.inflation_radius = config.get("astar_inflation_radius_m", 0.3)
        self.max_iterations = config.get("astar_max_iterations", 50000)
        self.resolution = config.get("grid_resolution_m", 0.1)

        self.costmap: Optional[CostMap] = None
        self._path: List[Tuple[float, float]] = []
        self._waypoints: List[Tuple[float, float]] = []

    def set_map(self, occupancy_grid: np.ndarray):
        """Set the occupancy grid for planning."""
        self.costmap = CostMap(
            occupancy_grid, 
            resolution=self.resolution,
            inflation_radius_m=self.inflation_radius
        )
        self.logger.info("Costmap updated")

    def plan(self, start: Tuple[float, float], 
             goal: Tuple[float, float]) -> List[Tuple[float, float]]:
        """
        Plan path from start to goal.

        Args:
            start: (x, y) in world coordinates (meters)
            goal: (x, y) in world coordinates (meters)

        Returns:
            List of (x, y) waypoints in world coordinates
        """
        if self.costmap is None:
            self.logger.error("No costmap set!")
            return []

        # Convert to grid coordinates
        sx = int(start[0] / self.resolution)
        sy = int(start[1] / self.resolution)
        gx = int(goal[0] / self.resolution)
        gy = int(goal[1] / self.resolution)

        # Check bounds and validity
        if not self.costmap.is_free(sx, sy):
            self.logger.warning("Start position is in obstacle!")
        if not self.costmap.is_free(gx, gy):
            self.logger.warning("Goal position is in obstacle!")
            return []

        # A* search
        start_node = Node(position=(sx, sy), g_score=0.0)
        start_node.f_score = self._heuristic(sx, sy, gx, gy)

        open_set = [start_node]
        open_dict = {(sx, sy): start_node}
        closed_set = set()

        iterations = 0
        while open_set and iterations < self.max_iterations:
            iterations += 1
            current = heapq.heappop(open_set)
            del open_dict[current.position]

            if current.position == (gx, gy):
                path = self._reconstruct_path(current)
                self._path = path
                self._waypoints = self._simplify_path(path)
                self.logger.info(f"Path found: {len(path)} points, {len(self._waypoints)} waypoints")
                return self._waypoints

            closed_set.add(current.position)

            # Expand neighbors (8-connected)
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
                nx, ny = current.position[0] + dx, current.position[1] + dy

                if (nx, ny) in closed_set:
                    continue

                if not self.costmap.is_free(nx, ny):
                    continue

                move_cost = math.sqrt(dx*dx + dy*dy) * self.resolution
                cell_cost = self.costmap.get_cost(nx, ny) / 100.0 * self.resolution
                tentative_g = current.g_score + move_cost + cell_cost * 0.5

                neighbor = open_dict.get((nx, ny))
                if neighbor is None or tentative_g < neighbor.g_score:
                    if neighbor is None:
                        neighbor = Node(position=(nx, ny))
                        open_dict[(nx, ny)] = neighbor

                    neighbor.parent = current
                    neighbor.g_score = tentative_g
                    neighbor.f_score = tentative_g + self._heuristic(nx, ny, gx, gy)

                    if neighbor not in open_set:
                        heapq.heappush(open_set, neighbor)

        self.logger.warning(f"No path found after {iterations} iterations")
        return []

    def _heuristic(self, x1: int, y1: int, x2: int, y2: int) -> float:
        """Heuristic function for A*."""
        dx = abs(x2 - x1) * self.resolution
        dy = abs(y2 - y1) * self.resolution

        if self.heuristic_type == "manhattan":
            return dx + dy
        elif self.heuristic_type == "euclidean":
            return math.sqrt(dx*dx + dy*dy)
        elif self.heuristic_type == "diagonal":
            return max(dx, dy) + (math.sqrt(2) - 1) * min(dx, dy)
        return math.sqrt(dx*dx + dy*dy)

    def _reconstruct_path(self, node: Node) -> List[Tuple[float, float]]:
        """Reconstruct path from goal node."""
        path = []
        while node:
            wx = node.position[0] * self.resolution
            wy = node.position[1] * self.resolution
            path.append((wx, wy))
            node = node.parent
        return path[::-1]

    def _simplify_path(self, path: List[Tuple[float, float]], 
                       epsilon: float = 0.3) -> List[Tuple[float, float]]:
        """Simplify path using Ramer-Douglas-Peucker algorithm."""
        if len(path) <= 2:
            return path

        def point_line_distance(p, a, b):
            if a == b:
                return math.dist(p, a)
            num = abs((b[1]-a[1])*p[0] - (b[0]-a[0])*p[1] + b[0]*a[1] - b[1]*a[0])
            den = math.sqrt((b[1]-a[1])**2 + (b[0]-a[0])**2)
            return num / den if den > 0 else 0

        def rdp(points, epsilon):
            if len(points) <= 2:
                return points

            max_dist = 0
            max_idx = 0
            for i in range(1, len(points) - 1):
                dist = point_line_distance(points[i], points[0], points[-1])
                if dist > max_dist:
                    max_dist = dist
                    max_idx = i

            if max_dist > epsilon:
                left = rdp(points[:max_idx+1], epsilon)
                right = rdp(points[max_idx:], epsilon)
                return left[:-1] + right
            else:
                return [points[0], points[-1]]

        return rdp(path, epsilon)

    def get_last_path(self) -> List[Tuple[float, float]]:
        return self._path

    def get_waypoints(self) -> List[Tuple[float, float]]:
        return self._waypoints
