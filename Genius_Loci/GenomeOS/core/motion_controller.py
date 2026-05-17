import math
from core.logger import get_logger

class MotionController:
    def __init__(self, config: dict):
        self.config = config
        self.logger = get_logger("Core.Motion")
        
        self.wheel_radius = config["wheel_radius_m"]
        self.wheelbase = config["wheelbase_m"]
        self.mps_to_rpm_factor = 60.0 / (2 * math.pi * self.wheel_radius)
        self.logger.info(f"Инициализация. Радиус колеса: {self.wheel_radius}м, База: {self.wheelbase}м")


    def compute_drive(self, target_linear_speed_mps: float, target_angular_speed_radps: float) -> dict:
        """
        Кинематика дифференциального привода.
        На вход: линейная скорость (м/с) и угловая скорость (рад/с).
        На выход: RPM для левого и правого колеса.
        """
        # Расчет скоростей для левого и правого колеса (V = V_lin +- V_ang * L/2)
        v_left = target_linear_speed_mps - (target_angular_speed_radps * self.wheelbase / 2)
        v_right = target_linear_speed_mps + (target_angular_speed_radps * self.wheelbase / 2)
        
        # Ограничиваем максимальную скорость колес
        max_mps = self.config["max_wheel_mps"]
        v_left = max(-max_mps, min(max_mps, v_left))
        v_right = max(-max_mps, min(max_mps, v_right))
        
        rpm_left = v_left * self.mps_to_rpm_factor
        rpm_right = v_right * self.mps_to_rpm_factor
 
        if abs(rpm_left) > 0.1 or abs(rpm_right) > 0.1:
            self.logger.debug(f"Kinematics -> V_lin:{target_linear_speed_mps:.2f} V_ang:{target_angular_speed_radps:.2f} | Out L:{rpm_left:.1f} R:{rpm_right:.1f} RPM")
        

        return {
            "wheel_L_target_rpm": rpm_left,
            "wheel_R_target_rpm": rpm_right
        }