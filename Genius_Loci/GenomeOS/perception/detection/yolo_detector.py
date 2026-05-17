"""
YOLO cargo detection module for identifying transportable objects.
Supports YOLOv8/v11 with ONNX Runtime for embedded inference.
"""
import numpy as np
import cv2
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
from core.logger import get_logger


@dataclass
class DetectedObject:
    """A detected cargo object."""
    class_id: int
    class_name: str
    confidence: float
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    center: Tuple[int, int]
    area: int
    depth_estimate: float = 0.0


class CargoDetector:
    """Cargo detection using YOLO with optional ONNX acceleration."""

    # Warehouse cargo class names
    CARGO_CLASSES = [
        "box", "crate", "pallet", "container",
        "bag", "barrel", "carton", "package"
    ]

    def __init__(self, model_path: Optional[str] = None, 
                 confidence_threshold: float = 0.5,
                 use_onnx: bool = True):
        self.logger = get_logger("Perception.YOLO")
        self.conf_threshold = confidence_threshold
        self.use_onnx = use_onnx
        self.model = None
        self.session = None
        self.input_size = (640, 640)
        self._use_dummy = True

        if model_path and Path(model_path).exists():
            self._load_model(model_path)
        else:
            self.logger.warning(f"Model not found at {model_path}, using dummy detector")

    def _load_model(self, model_path: str):
        """Load YOLO model or ONNX session."""
        try:
            if self.use_onnx and model_path.endswith(".onnx"):
                import onnxruntime as ort
                self.session = ort.InferenceSession(
                    model_path,
                    providers=["CPUExecutionProvider"]
                )
                self.input_size = (640, 640)
                self._use_dummy = False
                self.logger.info("ONNX model loaded")
            else:
                from ultralytics import YOLO
                self.model = YOLO(model_path)
                self._use_dummy = False
                self.logger.info("YOLO model loaded")
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            self._use_dummy = True

    def detect(self, image: np.ndarray, depth_map: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        Detect cargo objects in image.

        Args:
            image: Input image (BGR or grayscale)
            depth_map: Optional depth map for 3D position estimation

        Returns:
            Dict with detections list and visualization
        """
        if self._use_dummy:
            return self._dummy_detect(image, depth_map)

        # Preprocess
        input_tensor = self._preprocess(image)

        # Run inference
        if self.session:
            outputs = self.session.run(None, {self.session.get_inputs()[0].name: input_tensor})
            detections = self._parse_onnx_output(outputs[0], image.shape)
        else:
            results = self.model(input_tensor)
            detections = self._parse_yolo_output(results, image.shape)

        # Add depth estimates if available
        if depth_map is not None:
            for det in detections:
                cx, cy = det.center
                if 0 <= cy < depth_map.shape[0] and 0 <= cx < depth_map.shape[1]:
                    det.depth_estimate = float(depth_map[cy, cx])

        # Draw detections
        viz = image.copy()
        for det in detections:
            x1, y1, x2, y2 = det.bbox
            cv2.rectangle(viz, (x1, y1), (x2, y2), (0, 255, 0), 2)
            label = f"{det.class_name}: {det.confidence:.2f}"
            if det.depth_estimate > 0:
                label += f" @ {det.depth_estimate:.1f}m"
            cv2.putText(viz, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        return {
            "objects": [
                {
                    "class_id": d.class_id,
                    "class_name": d.class_name,
                    "confidence": round(d.confidence, 3),
                    "bbox": d.bbox,
                    "center": d.center,
                    "depth_m": round(d.depth_estimate, 2)
                }
                for d in detections
            ],
            "count": len(detections),
            "image_with_detections": viz,
            "has_target": len(detections) > 0
        }

    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for inference."""
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

        # Resize
        resized = cv2.resize(image, self.input_size)

        # Normalize
        normalized = resized.astype(np.float32) / 255.0

        # CHW format
        tensor = np.transpose(normalized, (2, 0, 1))
        tensor = np.expand_dims(tensor, axis=0)

        return tensor

    def _parse_onnx_output(self, output: np.ndarray, 
                           original_shape: Tuple) -> List[DetectedObject]:
        """Parse ONNX model output."""
        detections = []
        # YOLOv8 output format: [batch, 84, 8400] -> [x, y, w, h, conf, class_probs...]
        preds = np.squeeze(output).T

        # Filter by confidence
        scores = np.max(preds[:, 4:], axis=1)
        mask = scores > self.conf_threshold
        preds = preds[mask]
        scores = scores[mask]

        # Get class IDs
        class_ids = np.argmax(preds[:, 4:], axis=1)

        # Convert to bounding boxes
        scale_x = original_shape[1] / self.input_size[0]
        scale_y = original_shape[0] / self.input_size[1]

        for i, pred in enumerate(preds[:10]):  # Max 10 detections
            cx, cy, w, h = pred[:4]
            x1 = int((cx - w/2) * scale_x)
            y1 = int((cy - h/2) * scale_y)
            x2 = int((cx + w/2) * scale_x)
            y2 = int((cy + h/2) * scale_y)

            class_id = int(class_ids[i])
            class_name = self.CARGO_CLASSES[class_id % len(self.CARGO_CLASSES)]

            detections.append(DetectedObject(
                class_id=class_id,
                class_name=class_name,
                confidence=float(scores[i]),
                bbox=(x1, y1, x2, y2),
                center=(int(cx * scale_x), int(cy * scale_y)),
                area=int(w * h * scale_x * scale_y)
            ))

        return detections

    def _parse_yolo_output(self, results, original_shape: Tuple) -> List[DetectedObject]:
        """Parse ultralytics YOLO output."""
        detections = []
        for result in results:
            if result.boxes is None:
                continue
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                cls_id = int(box.cls[0])

                if conf < self.conf_threshold:
                    continue

                class_name = self.CARGO_CLASSES[cls_id % len(self.CARGO_CLASSES)]

                detections.append(DetectedObject(
                    class_id=cls_id,
                    class_name=class_name,
                    confidence=conf,
                    bbox=(x1, y1, x2, y2),
                    center=((x1+x2)//2, (y1+y2)//2),
                    area=(x2-x1)*(y2-y1)
                ))
        return detections

    def _dummy_detect(self, image: np.ndarray, 
                      depth_map: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """Dummy detection for testing without model."""
        h, w = image.shape[:2]

        # Simulate detection in center
        cx, cy = w // 2, int(h * 0.6)
        bw, bh = int(w * 0.15), int(h * 0.2)

        x1, y1 = cx - bw//2, cy - bh//2
        x2, y2 = cx + bw//2, cy + bh//2

        depth_est = 2.5
        if depth_map is not None and 0 <= cy < depth_map.shape[0] and 0 <= cx < depth_map.shape[1]:
            depth_est = float(depth_map[cy, cx])

        viz = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR) if len(image.shape) == 2 else image.copy()
        cv2.rectangle(viz, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(viz, f"box: 0.92 @ {depth_est:.1f}m", (x1, y1 - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        return {
            "objects": [{
                "class_id": 0,
                "class_name": "box",
                "confidence": 0.92,
                "bbox": (x1, y1, x2, y2),
                "center": (cx, cy),
                "depth_m": round(depth_est, 2)
            }],
            "count": 1,
            "image_with_detections": viz,
            "has_target": True,
            "mode": "dummy"
        }
