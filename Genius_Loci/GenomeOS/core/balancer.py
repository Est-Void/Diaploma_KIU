import math
from core.pid import PIDController
from core.logger import get_logger

class BalancerController:
    def __init__(self, config: dict):
        self.config = config
        self.logger = get_logger("Core.Balancer")

        # ИСПРАВЛЕНО: Было (max, -max), стало (-max, max). Иначе min > max и логика ломалась!
        self.pid_pitch = PIDController(
            kp=config["pitch_kp"], ki=config["pitch_ki"], kd=config["pitch_kd"],
            limits=(-config["max_limb_angle"], config["max_limb_angle"]) 
        )
        
        self.pid_roll = PIDController(
            kp=config["roll_kp"], ki=config["roll_ki"], kd=config["roll_kd"],
            limits=(-config["max_limb_angle"], config["max_limb_angle"])
        )

        # Физические параметры робота
        self.wheelbase = config["wheelbase_m"] # Расстояние между передней и задней осями
        self.track_width = config["track_width_m"] # Расстояние между левым и правым колесами
        self.gripper_leverage = config["gripper_leverage_m"] # Плечо силы груза

    def update(self, dt: float, target_speed: float, imu_data: dict, payload_state: dict) -> dict:
        """
        Вычисляет целевые углы для 4-х конечностей.
        imu_data: {'pitch': рад, 'roll': рад}
        payload_state: {'weight': кг, 'is_held': bool}
        """
        pitch = imu_data.get("pitch", 0.0)
        roll = imu_data.get("roll", 0.0)
        payload_weight = payload_state.get("weight", 0.0)
        is_held = payload_state.get("is_held", False)

        # 1. Трансформация скорости в целевой угол наклона (Feedforward по скорости)
        # Чтобы ехать вперед, нужно наклониться вперед
        speed_ff = target_speed * self.config["speed_to_angle_gain"]

        # 2. Компенсация массы груза (Feedforward по массе)
        # Момент силы груза: M = m * g * L. Компенсируем дополнительным наклоном назад.
        payload_ff = 0.0
        if is_held and payload_weight > 0:
            # Упрощенная формула: угол компенсации пропорционален весу и плечу
            payload_ff = -math.degrees(math.atan2(payload_weight * self.gripper_leverage, 
                                                  payload_weight * self.wheelbase * 0.5))
            self.logger.debug(f"Компенсация груза: {payload_ff:.2f} град")

        # Итоговая цель для Pitch ПИД-а
        target_pitch = speed_ff + payload_ff

        # 3. Работа ПИД регуляторов
        # ПИД возвращает требуемое ускорение/скорость изменения угла, 
        # но в нашем случае мы используем его для вычисления статического угла баланса.
        # Для инвертированного маятника ПИД управляет напрямую углом.
        pitch_correction = self.pid_pitch.compute(target_pitch, math.degrees(pitch), dt)
        roll_correction = self.pid_roll.compute(0.0, math.degrees(roll), dt) # Цель Roll = 0

        # 4. Распределение углов по 4 конечностям
        # Базовый угол от балансировки продольной оси
        base_pitch_angle = pitch_correction 
        base_roll_angle = roll_correction

        # Формула для 4 конечностей (кинематика плоской платформы):
        # Передние (0, 1) + базовый угол, Задние (2, 3) - базовый угол (инвертируются относительно колес)
        # Левые (0, 2) + угол крена, Правые (1, 3) - угол крена
        target_angles = {
            "limb_motor_0": base_pitch_angle + base_roll_angle,  # Перед-Лево
            "limb_motor_1": base_pitch_angle - base_roll_angle,  # Перед-Право
            "limb_motor_2": -base_pitch_angle + base_roll_angle, # Зад-Лево
            "limb_motor_3": -base_pitch_angle - base_roll_angle  # Зад-Право
        }

        return target_angles