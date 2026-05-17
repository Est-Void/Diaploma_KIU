"""
PID controller implementation with anti-windup and output limiting.
"""
import time
from typing import Tuple, Optional


class PIDController:
    """
    PID controller with configurable limits and anti-windup.

    Args:
        kp: Proportional gain
        ki: Integral gain
        kd: Derivative gain
        limits: Output limits as (min, max)
        integral_limits: Integral term limits for anti-windup
        derivative_filter: Low-pass filter coefficient for D term (0-1)
    """

    def __init__(
        self,
        kp: float = 1.0,
        ki: float = 0.0,
        kd: float = 0.0,
        limits: Optional[Tuple[float, float]] = None,
        integral_limits: Optional[Tuple[float, float]] = None,
        derivative_filter: float = 0.1
    ):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.limits = limits
        self.integral_limits = integral_limits
        self.derivative_filter = derivative_filter

        self._integral = 0.0
        self._last_error = 0.0
        self._filtered_derivative = 0.0
        self._last_time: Optional[float] = None
        self._output = 0.0

    def compute(self, setpoint: float, measurement: float, dt: Optional[float] = None) -> float:
        """Compute PID output."""
        now = time.monotonic()
        if dt is None:
            if self._last_time is None:
                self._last_time = now
                return 0.0
            dt = now - self._last_time

        if dt <= 0:
            return self._output

        error = setpoint - measurement

        # Proportional term
        p_term = self.kp * error

        # Integral term with anti-windup
        self._integral += error * dt
        if self.integral_limits:
            self._integral = max(self.integral_limits[0], 
                                min(self.integral_limits[1], self._integral))
        i_term = self.ki * self._integral

        # Derivative term with low-pass filter
        raw_derivative = (error - self._last_error) / dt
        self._filtered_derivative = (
            self.derivative_filter * raw_derivative + 
            (1 - self.derivative_filter) * self._filtered_derivative
        )
        d_term = self.kd * self._filtered_derivative

        # Compute output
        output = p_term + i_term + d_term

        # Apply output limits
        if self.limits:
            output = max(self.limits[0], min(self.limits[1], output))

        self._last_error = error
        self._last_time = now
        self._output = output

        return output

    def reset(self):
        """Reset controller state."""
        self._integral = 0.0
        self._last_error = 0.0
        self._filtered_derivative = 0.0
        self._last_time = None
        self._output = 0.0

    @property
    def components(self) -> Tuple[float, float, float]:
        """Return current P, I, D components."""
        error = self._last_error
        return (
            self.kp * error,
            self.ki * self._integral,
            self.kd * self._filtered_derivative
        )
