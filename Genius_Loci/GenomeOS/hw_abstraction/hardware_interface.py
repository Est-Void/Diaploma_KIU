from hw_abstraction.limb_motor import LimbMotor
from hw_abstraction.wheel_motor import WheelMotor
from hw_abstraction.pneumatic_gripper import PneumaticGripper
from hw_abstraction.pos_sensor import PositionSensor
from hw_abstraction.real_nodes import (
    RealLimbMotor, RealWheelMotor, RealPneumaticGripper, RealPositionSensor,
    HardwareInitializationError
)
from config.hw_config import NODES_CONFIG

# Заглушки для реального железа (пока просто бросают ошибку)
class RealLimbMotor: 
    def __init__(self, *args, **kwargs): raise NotImplementedError("Real HW not connected")
class RealWheelMotor: 
    def __init__(self, *args, **kwargs): raise NotImplementedError("Real HW not connected")

class HardwareInterface:
    def __init__(self, use_simulation: bool = True):
        self.use_simulation = use_simulation
        self.nodes = {}
        self.config = NODES_CONFIG

    def init_robot(self):
        if self.use_simulation:
            self._init_simulation()
        else:
            self._init_real_hardware()

    def _init_simulation(self):
        cfg = self.config
        # Инициализация 4 конечностей
        for i in range(4):
            motor = LimbMotor(f"limb_{i}", cfg["limb_motor"])
            motor.is_active = True
            self.nodes[f"limb_motor_{i}"] = motor
            self.nodes[f"limb_sensor_{i}"] = PositionSensor(f"limb_sens_{i}", cfg["pos_sensor"], motor)

        # Инициализация 2 колес (привязаны к задним конечностям 2 и 3)
        for i in range(2):
            motor = WheelMotor(f"wheel_{i}", cfg["wheel_motor"])
            motor.is_active = True
            self.nodes[f"wheel_motor_{i}"] = motor
            self.nodes[f"wheel_sensor_{i}"] = PositionSensor(f"wheel_sens_{i}", cfg["pos_sensor"], motor)

        # Инициализация 2 пневмо-хватов (на передних конечностях 0 и 1)
        for i in range(2):
            gripper = PneumaticGripper(f"gripper_{i}", cfg["pneumatic_gripper"])
            gripper.is_active = True
            self.nodes[f"gripper_{i}"] = gripper

    def _init_real_hardware(self):
        # Пытаемся запустить реальное железо
        try:
            cfg = NODES_CONFIG
            self.logger.warning("Попытка инициализации РЕАЛЬНОГО ЖЕЛЕЗА (Raspberry Pi)...")
            
            # Если код запущен не на RPi, сюда упадет HardwareInitializationError
            for i in range(4):
                motor = RealLimbMotor(f"limb_{i}", cfg["limb_motor"])
                self.nodes[f"limb_motor_{i}"] = motor
                self.nodes[f"limb_sensor_{i}"] = RealPositionSensor(f"limb_sens_{i}", cfg["pos_sensor"], motor)

            for i in range(2):
                motor = RealWheelMotor(f"wheel_{i}", cfg["wheel_motor"])
                self.nodes[f"wheel_motor_{i}"] = motor
                self.nodes[f"wheel_sensor_{i}"] = RealPositionSensor(f"wheel_sens_{i}", cfg["pos_sensor"], motor)

            for i in range(2):
                gripper = RealPneumaticGripper(f"gripper_{i}", cfg["pneumatic_gripper"])
                self.nodes[f"gripper_{i}"] = gripper
                
            self.logger.warning("Реальное железо успешно инициализировано!")

        except HardwareInitializationError as e:
            self.logger.error(f"ОШИБКА ЖЕЛЕЗА: {e}")
            self.logger.warning("ВНИМАНИЕ: Произведен автоматический откат (Fallback) на SIMULATION режим.")
            self.use_simulation = True # Меняем флаг
            self._init_simulation()   # Запускаем заглушки

    def get_node(self, name: str):
        return self.nodes.get(name)