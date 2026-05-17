"""
Stereo vision module for depth map generation using SGBM.
Calibrates stereo pair and computes real-time depth maps.
"""
import numpy as np
import cv2
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass
from core.logger import get_logger


@dataclass
class StereoCalibration:
    """Stereo camera calibration parameters."""
    camera_matrix_l: np.ndarray
    dist_coeffs_l: np.ndarray
    camera_matrix_r: np.ndarray
    dist_coeffs_r: np.ndarray
    R: np.ndarray  # Rotation between cameras
    T: np.ndarray  # Translation between cameras
    image_size: Tuple[int, int]


class StereoVisionModule:
    """Stereo depth estimation using OpenCV SGBM."""

    def __init__(self, config: Dict[str, Any]):
        self.logger = get_logger("Perception.Stereo")

        self.baseline = config.get("baseline_m", 0.12)
        self.focal_length = config.get("focal_length_px", 800.0)
        self.min_depth = config.get("min_depth_m", 0.3)
        self.max_depth = config.get("max_depth_m", 10.0)

        # SGBM parameters
        window_size = config.get("sgbm_window_size", 5)
        min_disp = config.get("sgbm_min_disparity", 0)
        num_disp = config.get("sgbm_num_disparities", 128)
        block_size = config.get("sgbm_block_size", 5)

        self.stereo_matcher = cv2.StereoSGBM_create(
            minDisparity=min_disp,
            numDisparities=num_disp,
            blockSize=block_size,
            P1=8 * 3 * window_size ** 2,
            P2=32 * 3 * window_size ** 2,
            disp12MaxDiff=1,
            uniquenessRatio=10,
            speckleWindowSize=100,
            speckleRange=32,
            mode=cv2.STEREO_SGBM_MODE_SGBM_3WAY
        )

        self.calibration: Optional[StereoCalibration] = None
        self.map1_l = self.map2_l = None
        self.map1_r = self.map2_r = None
        self.Q = None  # Disparity-to-depth reprojection matrix

        self.logger.info("Stereo vision module initialized")

    def load_calibration(self, calib_data: Dict[str, Any]) -> bool:
        """Load stereo calibration from dict or file."""
        try:
            self.calibration = StereoCalibration(
                camera_matrix_l=np.array(calib_data["camera_matrix_l"]),
                dist_coeffs_l=np.array(calib_data["dist_coeffs_l"]),
                camera_matrix_r=np.array(calib_data["camera_matrix_r"]),
                dist_coeffs_r=np.array(calib_data["dist_coeffs_r"]),
                R=np.array(calib_data["R"]),
                T=np.array(calib_data["T"]),
                image_size=tuple(calib_data["image_size"])
            )

            # Compute rectification maps
            R1, R2, P1, P2, self.Q, roi1, roi2 = cv2.stereoRectify(
                self.calibration.camera_matrix_l, self.calibration.dist_coeffs_l,
                self.calibration.camera_matrix_r, self.calibration.dist_coeffs_r,
                self.calibration.image_size, self.calibration.R, self.calibration.T,
                flags=cv2.CALIB_ZERO_DISPARITY, alpha=0
            )

            self.map1_l, self.map2_l = cv2.initUndistortRectifyMap(
                self.calibration.camera_matrix_l, self.calibration.dist_coeffs_l,
                R1, P1, self.calibration.image_size, cv2.CV_16SC2
            )
            self.map1_r, self.map2_r = cv2.initUndistortRectifyMap(
                self.calibration.camera_matrix_r, self.calibration.dist_coeffs_r,
                R2, P2, self.calibration.image_size, cv2.CV_16SC2
            )

            self.logger.info("Calibration loaded successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load calibration: {e}")
            return False

    def set_calibration_from_params(self, focal_length: float, baseline: float):
        """Set simplified calibration from known parameters."""
        self.focal_length = focal_length
        self.baseline = baseline
        self.logger.info(f"Calibration set: f={focal_length}px, B={baseline}m")

    def compute_depth(self, left_image: np.ndarray, 
                      right_image: np.ndarray) -> Dict[str, Any]:
        """
        Compute depth map from stereo pair.

        Returns dict with depth_map, disparity, and processing info.
        """
        # Rectify if calibration available
        if self.map1_l is not None:
            left_rect = cv2.remap(left_image, self.map1_l, self.map2_l, cv2.INTER_LINEAR)
            right_rect = cv2.remap(right_image, self.map1_r, self.map2_r, cv2.INTER_LINEAR)
        else:
            left_rect = left_image
            right_rect = right_image

        # Ensure grayscale
        if len(left_rect.shape) == 3:
            left_gray = cv2.cvtColor(left_rect, cv2.COLOR_BGR2GRAY)
        else:
            left_gray = left_rect

        if len(right_rect.shape) == 3:
            right_gray = cv2.cvtColor(right_rect, cv2.COLOR_BGR2GRAY)
        else:
            right_gray = right_rect

        # Compute disparity
        disparity = self.stereo_matcher.compute(left_gray, right_gray).astype(np.float32) / 16.0

        # Compute depth: Z = (B * f) / d
        with np.errstate(divide='ignore', invalid='ignore'):
            depth = (self.baseline * self.focal_length) / (disparity + 0.001)

        # Clamp depth range
        depth = np.clip(depth, self.min_depth, self.max_depth)

        # Inpaint invalid disparities
        depth = cv2.medianBlur(depth.astype(np.float32), 5)

        return {
            "depth_map": depth,
            "disparity": disparity,
            "left_rectified": left_rect,
            "right_rectified": right_rect,
            "min_depth_m": float(np.min(depth[depth > 0])),
            "max_depth_m": float(np.max(depth)),
            "mean_depth_m": float(np.mean(depth[depth > 0]))
        }

    def detect_obstacles_from_depth(self, depth_map: np.ndarray,
                                    robot_height: float = 0.5,
                                    floor_depth_range: float = 0.5) -> list:
        """
        Detect obstacles from depth map.
        Returns list of (angle, distance) tuples.
        """
        h, w = depth_map.shape
        center_y = int(h * 0.6)  # Look at middle-lower part

        # Sample depth across width
        sample_depths = depth_map[center_y, :]

        obstacles = []
        for x in range(0, w, 20):  # Sample every 20 pixels
            if sample_depths[x] > 0 and sample_depths[x] < self.max_depth:
                angle = (x - w/2) / w * 90  # Rough FOV estimate
                obstacles.append({
                    "angle_deg": round(angle, 1),
                    "distance_m": round(float(sample_depths[x]), 2),
                    "pixel_x": x
                })

        return obstacles
