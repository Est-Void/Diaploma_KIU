"""
ArUco marker detection for precise positioning and docking.
Supports multiple dictionaries and pose estimation.
"""
import numpy as np
import cv2
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from core.logger import get_logger


@dataclass
class ArucoMarker:
    """Detected ArUco marker data."""
    marker_id: int
    corners: np.ndarray
    center: Tuple[float, float]
    rvec: np.ndarray
    tvec: np.ndarray
    distance_m: float
    angle_deg: float


class ArucoDetector:
    """ArUco fiducial marker detector with pose estimation."""

    def __init__(self, config: Dict[str, Any]):
        self.logger = get_logger("Perception.ArUco")

        self.marker_length = config.get("marker_length_m", 0.165)
        dict_name = config.get("dictionary", "DICT_4X4_50")

        # Get dictionary
        dict_map = {
            "DICT_4X4_50": cv2.aruco.DICT_4X4_50,
            "DICT_4X4_100": cv2.aruco.DICT_4X4_100,
            "DICT_4X4_250": cv2.aruco.DICT_4X4_250,
            "DICT_5X5_50": cv2.aruco.DICT_5X5_50,
            "DICT_6X6_50": cv2.aruco.DICT_6X6_50,
        }
        aruco_dict_id = dict_map.get(dict_name, cv2.aruco.DICT_4X4_50)

        self.aruco_dict = cv2.aruco.getPredefinedDictionary(aruco_dict_id)
        self.detector = cv2.aruco.ArucoDetector(self.aruco_dict)

        # Camera parameters
        self.camera_matrix = config.get("camera_matrix")
        self.dist_coeffs = config.get("dist_coeffs", np.zeros(5))

        if self.camera_matrix is None:
            # Default approximate calibration
            self.camera_matrix = np.array([
                [800, 0, 640],
                [0, 800, 360],
                [0, 0, 1]
            ], dtype=np.float32)
        else:
            self.camera_matrix = np.array(self.camera_matrix, dtype=np.float32)

        self.dist_coeffs = np.array(self.dist_coeffs, dtype=np.float32)
        self.logger.info(f"ArUco detector initialized with dictionary {dict_name}")

    def detect(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Detect ArUco markers in image.

        Returns:
            Dict with markers list, visualization image, and detection info.
        """
        gray = image if len(image.shape) == 2 else cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Detect markers
        corners, ids, rejected = self.detector.detectMarkers(gray)

        markers: List[ArucoMarker] = []
        viz_image = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR) if len(image.shape) == 2 else image.copy()

        if ids is not None and len(ids) > 0:
            # Draw detected markers
            cv2.aruco.drawDetectedMarkers(viz_image, corners, ids)

            # Estimate pose for each marker
            for i, marker_id in enumerate(ids.flatten()):
                marker_corners = corners[i]

                # Pose estimation using PnP
                success, rvec, tvec = cv2.solvePnP(
                    self._get_object_points(),
                    marker_corners.reshape(-1, 2),
                    self.camera_matrix,
                    self.dist_coeffs
                )

                if success:
                    # Draw axis
                    cv2.drawFrameAxes(viz_image, self.camera_matrix, 
                                     self.dist_coeffs, rvec, tvec, self.marker_length * 0.5)

                    # Calculate center
                    center = np.mean(marker_corners.reshape(4, 2), axis=0)

                    # Calculate distance and angle
                    distance = float(np.linalg.norm(tvec))
                    angle = float(np.degrees(np.arctan2(tvec[0], tvec[2])))

                    marker = ArucoMarker(
                        marker_id=int(marker_id),
                        corners=marker_corners,
                        center=tuple(center.tolist()),
                        rvec=rvec,
                        tvec=tvec,
                        distance_m=round(distance, 3),
                        angle_deg=round(angle, 2)
                    )
                    markers.append(marker)

        return {
            "markers": [
                {
                    "id": m.marker_id,
                    "distance_m": m.distance_m,
                    "angle_deg": m.angle_deg,
                    "tvec": m.tvec.flatten().tolist(),
                    "center": m.center
                } for m in markers
            ],
            "count": len(markers),
            "image_with_markers": viz_image,
            "all_ids": ids.flatten().tolist() if ids is not None else []
        }

    def detect_for_docking(self, image: np.ndarray, 
                           target_id: int) -> Optional[Dict[str, Any]]:
        """
        Detect specific marker for docking maneuver.
        Returns detailed pose info for approach.
        """
        result = self.detect(image)

        for marker_data in result["markers"]:
            if marker_data["id"] == target_id:
                distance = marker_data["distance_m"]
                angle = marker_data["angle_deg"]

                # Calculate approach trajectory
                if distance > 0.5:
                    approach_speed = min(0.3, distance * 0.1)
                    lateral_correction = -angle * 0.02
                else:
                    approach_speed = 0.1
                    lateral_correction = 0.0

                return {
                    "found": True,
                    "marker": marker_data,
                    "approach_speed_mps": round(approach_speed, 3),
                    "lateral_correction_mps": round(lateral_correction, 3),
                    "is_aligned": abs(angle) < 5 and distance > 0.3,
                    "can_dock": distance < 0.5 and abs(angle) < 5
                }

        return {"found": False}

    def _get_object_points(self) -> np.ndarray:
        """Get 3D object points for marker corners."""
        half = self.marker_length / 2.0
        return np.array([
            [-half, half, 0],
            [half, half, 0],
            [half, -half, 0],
            [-half, -half, 0]
        ], dtype=np.float32)

    def generate_marker(self, marker_id: int, size_px: int = 200) -> np.ndarray:
        """Generate printable marker image."""
        return cv2.aruco.generateImageMarker(self.aruco_dict, marker_id, size_px)
