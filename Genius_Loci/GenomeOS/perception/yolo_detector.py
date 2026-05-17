import random
from core.logger import get_logger

class YOLODetector:
    def __init__(self, model_path: str = None, conf_threshold: float = 0.5):
        self.logger = get_logger("Perception.YOLO")
        self.conf_threshold = conf_threshold
        self.model_loaded = False
        
        if model_path:
            self.model_loaded = True
            self.logger.info(f"Модель {model_path} загружена")
        else:
            self.logger.warning("YOLO работает в режиме SIMULATION (генерация фейковых боксов)")

    def detect(self, frame) -> list:
        if not self.model_loaded:
            if random.random() < 0.3:
                h, w = frame.shape[:2]
                fake_box = [w//4, h//4, 3*w//4, 3*h//4]
                self.logger.debug("SIM: Сгенерирован фейковый бокс груза")
                return [{'class': 'cargo', 'conf': 0.85, 'bbox': fake_box}]
            return []

        # Реальный код для железа будет здесь
        # self.logger.debug(f"Обработано. Найдено 0 объектов.")
        return []