import math
from hw_abstraction.base_node import BaseNode

class LimbMotor(BaseNode):
    def __init__(self, node_id: str, config: dict):
        super().__init__(node_id, config)
        self.current_angle = 0.0 # Относительно корпуса

    def update(self, dt: float, target_angle: float, payload_weight: float = 0.0, **kwargs):
        if not self.is_active: return
        
        k = self.config["inertia_factor"]
        friction = self.config["friction_coeff"]
        max_spd = self.config["max_speed_deg_per_sec"]
        gravity = self.config["gravity_effect"]

        # Гравитация мешает поднимать груз (если угол положительный - подъем)
        gravity_drag = gravity * payload_weight * math.sin(math.radians(self.current_angle))
        
        # Расчет скорости с ограничением
        error = target_angle - self.current_angle
        desired_speed = error * k * 10 - (friction * self.current_angle) - gravity_drag
        actual_speed = max(-max_spd, min(max_spd, desired_speed))
        
        self.current_angle += actual_speed * dt
        self.current_angle = max(-self.config["max_angle_deg"], 
                                 min(self.config["max_angle_deg"], self.current_angle))
                                 
        self.logger.debug(f"Angle: {self.current_angle:.2f}° | Target: {target_angle:.2f}°")

    def get_state(self) -> dict:
        return {"node_id": self.node_id, "type": "limb_motor", "angle_deg": round(self.current_angle, 2)}