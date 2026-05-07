from hw_abstraction.base_node import BaseNode

class WheelMotor(BaseNode):
    def __init__(self, node_id: str, config: dict):
        super().__init__(node_id, config)
        self.current_rpm = 0.0

    def update(self, dt: float, target_rpm: float, payload_weight: float = 0.0, **kwargs):
        if not self.is_active: return

        k = self.config["inertia_factor"]
        resistance = self.config["rolling_resistance"]
        load_drop = self.config["load_effect"] * payload_weight

        # Экспоненциальное приближение к целевому RPM с учетом сопротивления и груза
        effective_target = target_rpm - load_drop
        self.current_rpm += (effective_target - self.current_rpm) * k
        self.current_rpm -= resistance * self.current_rpm # трение качения
        self.current_rpm = max(-self.config["max_rpm"], min(self.config["max_rpm"], self.current_rpm))

        self.logger.debug(f"RPM: {self.current_rpm:.2f} | Target: {target_rpm:.2f}")

    def get_state(self) -> dict:
        return {"node_id": self.node_id, "type": "wheel_motor", "rpm": round(self.current_rpm, 2)}