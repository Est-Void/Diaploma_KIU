import numpy as np
import cv2
import json
from typing import Union, Optional, Generator, Tuple, Dict, Any

class StereoProcessor:
    def __init__(self, calib_file: str, scale_factor: float = 0.5,
                 stereo_params: Optional[Dict[str, Any]] = None) -> None:
        self.scale_factor = scale_factor
        self._load_calibration(calib_file)
        self._init_rectification_maps()
        self._init_stereo_matcher(stereo_params)

    def _load_calibration(self, calib_file: str) -> None:
        with open(calib_file) as fp:
            cp = json.load(fp)
        self.Kl = np.array(cp["Kl"]) * self.scale_factor
        self.Kr = np.array(cp["Kr"]) * self.scale_factor
        self.Dl = np.array(cp["Dl"])
        self.Dr = np.array(cp["Dr"])
        self.R = np.array(cp["R"])
        self.T = np.array(cp["T"])
        self.imSize = (np.array(cp["imSize"]) * self.scale_factor).astype(int)

    def _init_rectification_maps(self) -> None:
        R1, R2, P1, P2, Q, _, _ = cv2.stereoRectify(
            self.Kl, self.Dl, self.Kr, self.Dr, self.imSize, self.R, self.T
        )
        self.xmap1, self.ymap1 = cv2.initUndistortRectifyMap(
            self.Kl, self.Dl, R1, P1, self.imSize, cv2.CV_32FC1
        )
        self.xmap2, self.ymap2 = cv2.initUndistortRectifyMap(
            self.Kr, self.Dr, R2, P2, self.imSize, cv2.CV_32FC1
        )

    def _init_stereo_matcher(self, stereo_params: Optional[Dict[str, Any]] = None) -> None:
        if stereo_params is None:
            stereo_params = {}
        default_params = {
            'numDisparities': 160,
            'blockSize': 15,
            'minDisparity': 2,
            'textureThreshold': 100,
            'uniquenessRatio': 3,
            'preFilterCap': 31,
            'preFilterSize': 23,
            'preFilterType': 0,
            'speckleRange': 10,
            'speckleWindowSize': 200,
            'disp12MaxDiff': 1
        }
        default_params.update(stereo_params)
        self.stereo = cv2.StereoBM_create(
            numDisparities=default_params['numDisparities'],
            blockSize=default_params['blockSize']
        )
        for key, value in default_params.items():
            if key not in ('numDisparities', 'blockSize'):
                setter = getattr(self.stereo, f'set{key}', None)
                if setter:
                    setter(value)
        self.min_disparity = default_params['minDisparity']
        self.num_disparities = default_params['numDisparities']

    def rectify(self, left_img: np.ndarray, right_img: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        left_rect = cv2.remap(left_img, self.xmap1, self.ymap1, cv2.INTER_LINEAR)
        right_rect = cv2.remap(right_img, self.xmap2, self.ymap2, cv2.INTER_LINEAR)
        return left_rect, right_rect

    def compute_disparity(self, left_gray: np.ndarray, right_gray: np.ndarray) -> np.ndarray:
        disp = self.stereo.compute(left_gray, right_gray).astype(np.float32) / 16.0
        return disp

    def normalize_disparity(self, disparity: np.ndarray) -> np.ndarray:
        normalized = (disparity - self.min_disparity) / self.num_disparities
        return np.clip(normalized, 0, 1)

    def process_pair(self, left_img: np.ndarray, right_img: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        left_rect, right_rect = self.rectify(left_img, right_img)
        left_gray = cv2.cvtColor(left_rect, cv2.COLOR_BGR2GRAY)
        right_gray = cv2.cvtColor(right_rect, cv2.COLOR_BGR2GRAY)
        disparity = self.compute_disparity(left_gray, right_gray)
        return left_rect, right_rect, disparity

