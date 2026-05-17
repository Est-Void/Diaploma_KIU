"""
Stereo camera emulator that generates synthetic images and depth maps.
"""
import numpy as np
from typing import Dict, Any, Tuple, Optional
from core.logger import get_logger


class StereoCameraEmulator:
    """Emulates stereo camera pair with configurable parameters."""

    def __init__(self, width: int = 1280, height: int = 720,
                 baseline_m: float = 0.12, focal_length_px: float = 800.0):
        self.logger = get_logger("Sensors.Stereo")
        self.width = width
        self.height = height
        self.baseline = baseline_m
        self.focal_length = focal_length_px
        self._frame_counter = 0

    def capture(self, scene_depth_map: Optional[np.ndarray] = None,
                noise_std: float = 0.5) -> Dict[str, Any]:
        """
        Generate synthetic stereo pair from a depth map.

        If no depth map provided, generates random test pattern.
        """
        if scene_depth_map is None:
            # Generate test pattern
            scene_depth_map = self._generate_test_pattern()

        # Ensure correct size
        if scene_depth_map.shape != (self.height, self.width):
            import cv2
            scene_depth_map = cv2.resize(scene_depth_map, (self.width, self.height))

        # Generate left image (simulated)
        left_image = self._simulate_image(scene_depth_map, noise_std)

        # Generate right image (shifted by disparity)
        disparity = (self.baseline * self.focal_length) / (scene_depth_map + 0.001)
        right_image = self._simulate_right_image(left_image, disparity, noise_std)

        self._frame_counter += 1

        return {
            "left": left_image,
            "right": right_image,
            "ground_truth_depth": scene_depth_map,
            "disparity": disparity,
            "frame_id": self._frame_counter,
            "timestamp": self._frame_counter / 15.0,  # 15 fps
            "camera_info": {
                "width": self.width,
                "height": self.height,
                "baseline_m": self.baseline,
                "focal_length_px": self.focal_length
            }
        }

    def _generate_test_pattern(self) -> np.ndarray:
        """Generate a test depth pattern with walls and objects."""
        depth = np.ones((self.height, self.width), dtype=np.float32) * 5.0

        # Floor gradient
        for y in range(self.height):
            depth[y, :] = 2.0 + (y / self.height) * 8.0

        # Add some boxes (obstacles)
        # Box 1: center-left
        x1, y1, w1, h1 = 200, 300, 150, 200
        depth[y1:y1+h1, x1:x1+w1] = 2.5

        # Box 2: center-right
        x2, y2, w2, h2 = 800, 250, 200, 250
        depth[y2:y2+h2, x2:x2+w2] = 3.0

        # Back wall
        depth[50:100, :] = 8.0

        return depth

    def _simulate_image(self, depth_map: np.ndarray, noise_std: float) -> np.ndarray:
        """Simulate a grayscale image from depth."""
        image = np.clip(255.0 / (depth_map + 0.5), 0, 255).astype(np.uint8)
        if noise_std > 0:
            noise = np.random.normal(0, noise_std, image.shape).astype(np.int16)
            image = np.clip(image.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        return image

    def _simulate_right_image(self, left: np.ndarray, disparity: np.ndarray, 
                               noise_std: float) -> np.ndarray:
        """Simulate right camera image by shifting based on disparity."""
        h, w = left.shape
        right = np.zeros_like(left)

        for y in range(h):
            for x in range(w):
                shift = int(disparity[y, x])
                new_x = x - shift
                if 0 <= new_x < w:
                    right[y, x] = left[y, new_x]

        # Add independent noise
        if noise_std > 0:
            noise = np.random.normal(0, noise_std, right.shape).astype(np.int16)
            right = np.clip(right.astype(np.int16) + noise, 0, 255).astype(np.uint8)

        return right

    def reset(self):
        self._frame_counter = 0
