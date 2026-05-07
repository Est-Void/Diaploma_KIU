from abc import ABC, abstractmethod
from core.logger import get_logger

class BaseNode(ABC):
    def __init__(self, node_id: str, config: dict):
        self.node_id = node_id
        self.config = config
        self.logger = get_logger(f"HW.{self.__class__.__name__}_{node_id}")
        self.is_active = False

    @abstractmethod
    def update(self, dt: float, target_value, **kwargs):
        """Обновление состояния симуляции. dt - время в секундах."""
        pass

    @abstractmethod
    def get_state(self) -> dict:
        """Возвращает текущее состояние узла."""
        pass