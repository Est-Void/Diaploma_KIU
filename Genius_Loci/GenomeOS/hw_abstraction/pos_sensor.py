import random
from hw_abstraction.base_node import BaseNode

class PositionSensor(BaseNode):
    def __init__(self, node_id: str, config: dict, target_node: BaseNode):
        super().__init__(node_id, config)
        self.target_node = target_node
        self.noise_std = config["noise_std_dev"]

    def update(self, dt: float, **kwargs):
        pass # Датчик сам по себе не обновляется, он только читает

    def read(self) -> dict:
        # Берем реальное состояние узла и искажаем шумом
        real_state = self.target_node.get_state()
        noisy_state = {}
        
        for key, val in real_state.items():
            if isinstance(val, (int, float)) and key != "node_id" and key != "type":
                noisy_state[key] = round(val + random.gauss(0, self.noise_std), 2)
            else:
                noisy_state[key] = val
                
        self.logger.debug(f"Read noisy state: {noisy_state}")
        return noisy_state

    def get_state(self) -> dict:
        return self.read()