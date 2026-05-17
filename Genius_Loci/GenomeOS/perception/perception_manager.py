import numpy as np
from core.logger import get_logger
# Импортируем твой класс (предполагаем, что он лежит в perception/stereo.py)
# from perception.stereo import StereoProcessor 
from perception.yolo_detector import YOLODetector

class PerceptionManager:
    def __init__(self, config: dict, use_simulation: bool = True):
        self.config = config
        self.logger = get_logger("Perception.Manager")
        self.use_simulation = use_simulation

        # Инициализация стерео (пока заглушка, чтобы код не упал без калибровочного файла)
        self.stereo = None
        if not use_simulation:
            pass # self.stereo = StereoProcessor("calib.json")
        
        self.yolo = YOLODetector(model_path=None if use_simulation else "yolov8n.pt")

        # Зоны интереса (ROI) на изображении (в процентах от ширины/высоты)
        # Нам не нужно смотреть на потолок, только на пол впереди и на стеллажи
        self.obstacle_roi = {
            "x_min": 0.2, "x_max": 0.8, # Центральная треть кадра
            "y_min": 0.5, "y_max": 1.0   # Нижняя половина (где пол и препятствия)
        }

    def process_frame(self, frame, run_yolo: bool = False) -> dict:
        """
        Добавлен флаг run_yolo. Запускаем детектор только если ищем груз.
        """
        result = {
            "obstacle_ahead": False, "obstacle_distance_m": 10.0,
            "cargo_detected": False, "cargo_distance_m": None, "cargo_center_offset": 0.0
        }

        disparity_map = np.zeros((frame.shape[0], frame.shape[1]), dtype=np.float32) if self.stereo is None else self._get_real_disparity(frame)

        # Обнаружение препятствий работаем ВСЕГДА (безопасность)
        result["obstacle_ahead"], result["obstacle_distance_m"] = self._check_obstacles(disparity_map, frame.shape)
        if result["obstacle_ahead"]:
            self.logger.warning(f"ОБНАРУЖЕНО ПРЕПЯТСТВИЕ! Дистанс: {result['obstacle_distance_m']:.2f}м")

        # YOLO запускаем ТОЛЬКО по требованию Mission Executor-а
        if run_yolo:
            detections = self.yolo.detect(frame)
            for det in detections:
                if det['class'] == 'cargo':
                    result["cargo_detected"] = True
                    bbox = det['bbox']
                    cx = int((bbox[0] + bbox[2]) / 2)
                    cy = int(bbox[3])
                    img_center_x = frame.shape[1] / 2
                    result["cargo_center_offset"] = (cx - img_center_x) / img_center_x 
                    result["cargo_distance_m"] = self._get_depth_at_point(disparity_map, cx, cy)
                    
                    self.logger.info(f"ГРУЖУ ВИЖУ: Дистанс={result['cargo_distance_m']:.2f}м, Смещение={result['cargo_center_offset']:.2f}")
                    break

        return result

    def _check_obstacles(self, disparity_map: np.ndarray, frame_shape: tuple) -> tuple:
        """Проверяет нижнюю центральную зону на наличие близких объектов"""
        h, w = frame_shape[:2]
        
        # Вырезаем ROI (Region of Interest)
        y1 = int(h * self.obstacle_roi["y_min"])
        y2 = int(h * self.obstacle_roi["y_max"])
        x1 = int(w * self.obstacle_roi["x_min"])
        x2 = int(w * self.obstacle_roi["x_max"])
        
        roi_disparity = disparity_map[y1:y2, x1:x2]
        
        # В симуляции: иногда случайно "видим" стену
        if self.use_simulation:
            if np.random.random() < 0.02: # 2% шанс
                return True, 0.5 # Препятствие в 0.5 метрах
            return False, 10.0

        # Реальная логика: чем больше disparity, тем ближе объект.
        # Если средний disparity в зоне превышает порог - стоп!
        # Формула перевода disparity в метры: Distance = (Baseline * FocalLength) / Disparity
        # (Внутри StereoProcessor есть матрица Q, через нее делается cv2.reprojectImageTo3D)
        
        mean_disparity = np.mean(roi_disparity[roi_disparity > 0]) # Исключаем нули (где не нашлось совпадений)
        if mean_disparity > self.config["obstacle_disparity_threshold"]:
            # Конвертируем в метры (заглушка формулы)
            distance_m = (0.05 * 500) / mean_disparity # 5 см база, 500 фокусное (примерно)
            return True, distance_m
            
        return False, 10.0

    def _get_depth_at_point(self, disparity_map: np.ndarray, x: int, y: int) -> float:
        """Получает дистанцию до конкретной точки (например, до груза)"""
        if self.use_simulation:
            return 0.6 # Симуляция: груз всегда в 60 см
        
        d = disparity_map[y, x]
        if d > 0:
            return (0.05 * 500) / d
        return -1.0 # Ошибка измерения

    def _get_real_disparity(self, frame):
        # Разрезаем стерео-кадр пополам и скармливаем твоему классу
        half = frame.shape[1] // 2
        left = frame[:, :half]
        right = frame[:, half:]
        _, _, disp = self.stereo.process_pair(left, right)
        return disp