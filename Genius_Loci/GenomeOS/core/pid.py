class PIDController:
    def __init__(self, kp: float, ki: float, kd: float, limits: tuple = (-100.0, 100.0)):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.min_out, self.max_out = limits

        self.integral = 0.0
        self.prev_error = 0.0
        self.first_run = True

    def compute(self, setpoint: float, current_value: float, dt: float) -> float:
        error = setpoint - current_value
        
        # Пропорциональная часть
        p_out = self.kp * error
        
        # Интегральная часть с Anti-windup
        self.integral += error * dt
        if self.integral > self.max_out: self.integral = self.max_out
        elif self.integral < self.min_out: self.integral = self.min_out
        i_out = self.ki * self.integral
        
        # Дифференциальная часть
        if self.first_run:
            self.prev_error = error
            self.first_run = False
        derivative = (error - self.prev_error) / dt if dt > 0 else 0.0
        d_out = self.kd * derivative
        
        self.prev_error = error
        
        output = p_out + i_out + d_out
        return max(self.min_out, min(self.max_out, output))

    def reset(self):
        self.integral = 0.0
        self.prev_error = 0.0
        self.first_run = True