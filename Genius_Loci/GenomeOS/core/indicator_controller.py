import math
import time
import enum
from hw_abstraction.indicators import MockLED, MockBuzzer
from core.logger import get_logger

class RobotStatus(enum.Enum):
    IDLE = "idle"
    NAVIGATE = "navigate"
    SEARCHING = "searching"
    GRABBING = "grabbing"
    LOW_BATTERY = "low_battery"
    BLOCKED = "blocked"
    ERROR = "error"           # Некритичная ошибка (потеря груза, ошибка камеры)
    CRASH_EMERGENCY = "crash" # Авария (упал, перегрев мотора)

class IndicatorController:
    def __init__(self, config: dict, use_mock: bool = True):
        self.config = config
        self.logger = get_logger("Core.Indicators")
        
        # Инициализация железа
        if use_mock:
            self.led = MockLED(0, "face")
            self.buzzer = MockBuzzer(0, "buzzer")
        else:
            pins = config["hw_pins"]
            self.led = RealLED(pins["r"], pins["g"], pins["b"], "face")
            self.buzzer = RealBuzzer(pins["buzzer"], "buzzer")

        self.current_status = RobotStatus.IDLE
        self.internal_timer = 0.0
        self.last_sound_time = 0.0
        self.prev_status = None

        # Цвета (R, G, B от 0 до 1)
        self.COLORS = {
            "white": (1.0, 1.0, 1.0),
            "orange": (1.0, 0.5, 0.0),
            "yellow": (1.0, 1.0, 0.0),
            "red": (1.0, 0.0, 0.0),
            "off": (0.0, 0.0, 0.0)
        }

    def set_status(self, status: RobotStatus, force_sound: bool = False):
        """Вызывается из MissionExecutor или системы мониторинга"""
        if status != self.current_status:
            self.logger.info(f"Смена статуса индикации: {self.current_status.name} -> {status.name}")
            self.prev_status = self.current_status
            self.current_status = status
            self.last_sound_time = 0.0 # Сброс таймера звука для проигрывания при смене
            if force_sound:
                self._trigger_sound()

    def update(self, dt: float):
        """Вызывать в главном цикле для плавной анимации LED"""
        self.internal_timer += dt
        r, g, b = 0, 0, 0

        if self.current_status == RobotStatus.IDLE:
            r, g, b = self._pulse(self.COLORS["white"], period=3.0, min_val=0.2)
            
        elif self.current_status == RobotStatus.NAVIGATE or self.current_status == RobotStatus.SEARCHING:
            r, g, b = self._pulse(self.COLORS["white"], period=1.0, min_val=0.4)
            
        elif self.current_status == RobotStatus.GRABBING:
            r, g, b = self._pulse(self.COLORS["orange"], period=1.5, min_val=0.3)
            
        elif self.current_status == RobotStatus.LOW_BATTERY:
            r, g, b = self._blink(self.COLORS["yellow"], period=2.0)
            self._periodic_sound(freq=1000, duration=100, period_sec=4.0)
            
        elif self.current_status == RobotStatus.BLOCKED:
            r, g, b = self._blink(self.COLORS["yellow"], period=0.5)
            self._periodic_sound(freq=1500, duration=100, period_sec=0.8) # Двойной писк
            
        elif self.current_status == RobotStatus.ERROR:
            r, g, b = self._blink(self.COLORS["red"], period=1.0)
            self._periodic_sound(freq=800, duration=300, period_sec=2.0)
            
        elif self.current_status == RobotStatus.CRASH_EMERGENCY:
            r, g, b = self._blink(self.COLORS["red"], period=0.2) # Быстрое стробирование
            self._periodic_sound(freq=400, duration=500, period_sec=0.7) # Низкий тревожный писк

        self.led.set_pwm(r, g, b)

    # --- Внутренние функции анимации ---
    def _pulse(self, color: tuple, period: float, min_val: float) -> tuple:
        """Плавная пульсация (синусоида)"""
        val = (math.sin(self.internal_timer * (2 * math.pi / period)) + 1) / 2 
        val = min_val + val * (1.0 - min_val)
        return (color[0] * val, color[1] * val, color[2] * val)

    def _blink(self, color: tuple, period: float) -> tuple:
        """Резкое мигание (меандр 50/50)"""
        state = (self.internal_timer % period) > (period / 2)
        return color if state else self.COLORS["off"]

    def _periodic_sound(self, freq: int, duration: int, period_sec: float):
        """Издает звук с заданной периодичностью"""
        if self.internal_timer - self.last_sound_time >= period_sec:
            self.buzzer.beep(freq, duration)
            self.last_sound_time = self.internal_timer

    def _trigger_sound(self):
        """Одноразовый звук при смене состояния"""
        sounds = {
            RobotStatus.GRABBING: (1200, 150),
            RobotStatus.CRASH_EMERGENCY: (200, 1000)
        }
        if self.current_status in sounds:
            self.buzzer.beep(*sounds[self.current_status])