import logging

# Настройки логгера
LOGGING_CONFIG = {
    "level": logging.DEBUG, # Измени на INFO, чтобы убрать подробный лог
    "format": "%(asctime)s | %(name)-20s | %(levelname)-7s | %(message)s",
    "handlers": [logging.StreamHandler()]
}

# Физические константы и параметры узлов
NODES_CONFIG = {
    "limb_motor": {
        "max_angle_deg": 45.0,       # Макс. угол наклона конечности
        "max_speed_deg_per_sec": 60.0,
        "inertia_factor": 0.15,      # Чем меньше, тем инерционнее (0-1)
        "friction_coeff": 0.05,      # Потеря скорости из-за трения
        "gravity_effect": 0.2        # Влияние гравитации при подъеме
    },
    "wheel_motor": {
        "max_rpm": 120.0,
        "inertia_factor": 0.1,
        "rolling_resistance": 0.02,  # Сопротивление качению
        "load_effect": 0.05          # Просадка RPM от веса груза
    },
    "pneumatic_gripper": {
        "max_pressure_bar": 6.0,
        "pump_rate": 2.0,            # Бар в секунду (скорость накачки)
        "leak_rate": 0.1,            # Утечки воздуха
        "grip_force_per_bar": 15.0   # Ньютонов на 1 бар
    },
    "pos_sensor": {
        "noise_std_dev": 0.5,        # Стандартное отклонение шума (градусы/RPM)
        "update_delay_ms": 10        # Задержка опроса
    },


    "balancer": {
        "pitch_kp": 15.0,    # Сильно реагирует на отклонение вперед/назад
        "pitch_ki": 0.5,     # Медленно убирает статическую ошибку
        "pitch_kd": 8.0,     # Гасит раскачку (демпфирование)
        
        "roll_kp": 10.0,
        "roll_ki": 0.1,
        "roll_kd": 5.0,
        
        "max_limb_angle": 25.0, # Ограничение баланса (не выворачивать руки)
        "speed_to_angle_gain": 0.2, # На сколько градусов наклоняться на 1 RPM скорости
        
        "wheelbase_m": 0.4,   # 40 см между осями
        "track_width_m": 0.3, # 30 см между колесами
        "gripper_leverage_m": 0.15 # 15 см вылет груза вперед от оси передних моторов
    }
}