from hw_abstraction.base_node import BaseNode

class PneumaticGripper(BaseNode):
    def __init__(self, node_id: str, config: dict):
        super().__init__(node_id, config)
        self.current_pressure = 0.0
        self.is_gripping = False

    def update(self, dt: float, command: str = "hold", **kwargs):
        if not self.is_active: return

        pump_rate = self.config["pump_rate"]
        leak_rate = self.config["leak_rate"]

        if command == "grip":
            self.is_gripping = True
            self.current_pressure += pump_rate * dt
        elif command == "release":
            self.is_gripping = False
            self.current_pressure -= pump_rate * dt * 1.5 # Стравливает быстрее
        else: # hold
            self.current_pressure -= leak_rate * dt

        self.current_pressure = max(0.0, min(self.config["max_pressure_bar"], self.current_pressure))
        
        force = self.current_pressure * self.config["grip_force_per_bar"]
        self.logger.debug(f"Pressure: {self.current_pressure:.2f} bar | Force: {force:.1f} N | Cmd: {command}")

    def get_state(self) -> dict:
        force = self.current_pressure * self.config["grip_force_per_bar"]
        return {
            "node_id": self.node_id, "type": "gripper", 
            "pressure_bar": round(self.current_pressure, 2),
            "grip_force_N": round(force, 1),
            "is_holding": self.current_pressure > 1.0
        }