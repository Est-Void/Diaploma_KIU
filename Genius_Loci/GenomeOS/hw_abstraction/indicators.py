import time
import threading
from core.logger import get_logger

try:
    import RPi.GPIO as GPIO
    HARDWARE_AVAILABLE = True
except ImportError:
    HARDWARE_AVAILABLE = False

class BaseIndicator:
    def __init__(self, pin: int, node_id: str):
        self.pin = pin
        self.node_id = node_id

class MockLED(BaseIndicator):
    def __init__(self, pin: int, node_id: str):
        super().__init__(pin, node_id)
        self.logger = get_logger(f"HW.MockLED_{node_id}")

    def set_pwm(self, r: float, g: float, b: float):
        # r, g, b от 0.0 до 1.0
        r_c = int(r * 255); g_c = int(g * 255); b_c = int(b * 255)
        self.logger.debug(f"Color: RGB({r_c},{g_c},{b_c})")

class MockBuzzer(BaseIndicator):
    def __init__(self, pin: int, node_id: str):
        super().__init__(pin, node_id)
        self.logger = get_logger(f"HW.MockBuzzer_{node_id}")

    def beep(self, frequency: int, duration_ms: int):
        self.logger.info(f"SOUND: {frequency}Hz for {duration_ms}ms")

# --- Реальные классы (работают через RPi.GPIO PWM) ---
class RealLED(BaseIndicator):
    def __init__(self, pin_r: int, pin_g: int, pin_b: int, node_id: str):

        super().__init__(pin_r, node_id)
        if not HARDWARE_AVAILABLE: raise Exception("RPi.GPIO not found")
        GPIO.setup(pin_r, GPIO.OUT); GPIO.setup(pin_g, GPIO.OUT); GPIO.setup(pin_b, GPIO.OUT)
        self.pwm_r = GPIO.PWM(pin_r, 1000); self.pwm_g = GPIO.PWM(pin_g, 1000); self.pwm_b = GPIO.PWM(pin_b, 1000)
        self.pwm_r.start(0); self.pwm_g.start(0); self.pwm_b.start(0)

    def set_pwm(self, r: float, g: float, b: float):
        self.pwm_r.ChangeDutyCycle(r * 100)
        self.pwm_g.ChangeDutyCycle(g * 100)
        self.pwm_b.ChangeDutyCycle(b * 100)

class RealBuzzer(BaseIndicator):
    def __init__(self, pin: int, node_id: str):
        super().__init__(pin, node_id)
        if not HARDWARE_AVAILABLE: raise Exception("RPi.GPIO not found")
        GPIO.setup(pin, GPIO.OUT)

    def beep(self, frequency: int, duration_ms: int):
        # Для пьезодинамика нужна генерация прямоугольного импульса
        # Упрощенная реализация в отдельном потоке
        def _beep_thread():
            p = GPIO.PWM(self.pin, frequency)
            p.start(50)
            time.sleep(duration_ms / 1000.0)
            p.stop()
        threading.Thread(target=_beep_thread, daemon=True).start()