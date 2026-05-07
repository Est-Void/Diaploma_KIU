import time
import math
import random
import logging
import threading
from collections import deque

import matplotlib
try:
    matplotlib.use('TkAgg')
except:
    pass 

import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button

from hw_abstraction.hardware_interface import HardwareInterface
from core.balancer import BalancerController

logging.getLogger().setLevel(logging.ERROR)

# ==========================================
# 1. ОБЩЕЕ СОСТОЯНИЕ (Thread-Safe)
# ==========================================
class SimState:
    def __init__(self, max_points=600):
        self.max_points = max_points
        self.time = deque(maxlen=max_points)
        
        self.pitch = deque(maxlen=max_points)
        self.roll = deque(maxlen=max_points)
        self.limbs = [deque(maxlen=max_points) for _ in range(4)]
        
        self.grip_L_pressure = deque(maxlen=max_points)
        self.grip_R_pressure = deque(maxlen=max_points)
        
        self.wheel_target = deque(maxlen=max_points)
        self.wheel_actual_L = deque(maxlen=max_points)
        self.wheel_actual_R = deque(maxlen=max_points)
        
        self.kp = 15.0
        self.ki = 0.5
        self.kd = 8.0
        self.target_speed = 0.0
        self.payload_held = False
        self.payload_weight = 0.0
        self.grip_cmd = "hold"
        self.external_kick = False
        
        self.is_running = True
        self.lock = threading.Lock()

state = SimState()

def set_grip_cmd_safe(cmd):
    with state.lock:
        state.grip_cmd = cmd

# ==========================================
# 2. ФОНОВЫЙ ПОТОК СИМУЛЯЦИИ (СТАБИЛЬНАЯ ФИЗИКА)
# ==========================================
def simulation_thread_func():
    hw = HardwareInterface(use_simulation=True)
    hw.init_robot()
    
    balancer = BalancerController(hw.config["balancer"])

    limbs = [hw.get_node(f"limb_motor_{i}") for i in range(4)]
    wheels = [hw.get_node(f"wheel_motor_{i}") for i in range(2)]
    l_gripper = hw.get_node("gripper_0")
    r_gripper = hw.get_node("gripper_1")

    dt = 0.05 
    sim_pitch = 0.0 
    sim_roll = 0.0
    sim_vel_pitch = 0.0 # Добавили скорость для реалистичного падения
    start_time = time.time()

    print("[Симуляция] Фоновый поток запущен.")

    while state.is_running:
        t_start = time.time()
        elapsed_time = t_start - start_time
        
        with state.lock:
            balancer.pid_pitch.kp = state.kp
            balancer.pid_pitch.ki = state.ki
            balancer.pid_pitch.kd = state.kd
            target_speed = state.target_speed
            payload_weight = state.payload_weight
            payload_held = state.payload_held
            grip_cmd = state.grip_cmd
            
            if state.external_kick:
                sim_vel_pitch += 150.0 # Импульс скорости от удара
                state.external_kick = False

        # --- Стабильная физика инвертированного маятника ---
        # Ускорение от гравитации (стремится уронить)
        gravity_acc = 15.0 * math.sin(math.radians(sim_pitch))
        
        # Ускорение от моторов (стремится выровнять)
        actual_control_pitch = (limbs[0].current_angle + limbs[1].current_angle - limbs[2].current_angle - limbs[3].current_angle) / 2
        control_acc = 5.0 * (actual_control_pitch - sim_pitch)
        
        # Демпфирование (трение в шарнирах / воздуха)
        damping_acc = -2.0 * sim_vel_pitch
        
        # Интеграция скорости и угла
        sim_vel_pitch += (gravity_acc + control_acc + damping_acc) * dt
        sim_pitch += sim_vel_pitch * dt
        sim_pitch += random.gauss(0, 0.1) # Шум датчика
        
        # "ПОЛ" - если робот упал, он не проваливается сквозь землю
        FALL_LIMIT = 28.0 
        if abs(sim_pitch) > FALL_LIMIT:
            sim_pitch = FALL_LIMIT * (1 if sim_pitch > 0 else -1)
            sim_vel_pitch = 0 

        # Roll (поперечный) делаем проще, он менее критичен
        actual_control_roll = (limbs[0].current_angle - limbs[1].current_angle + limbs[2].current_angle - limbs[3].current_angle) / 2
        sim_roll += (actual_control_roll - sim_roll) * 0.3 + random.gauss(0, 0.05)

        imu_data = {"pitch": sim_pitch, "roll": sim_roll}

        # Мозг
        target_angles = balancer.update(
            dt=dt, target_speed=target_speed, imu_data=imu_data,
            payload_state={"weight": payload_weight, "is_held": payload_held}
        )

        # Мускулы
        for i in range(4):
            limbs[i].update(dt, target_angle=target_angles[f"limb_motor_{i}"], payload_weight=payload_weight)
        
        wheels[0].update(dt, target_rpm=target_speed, payload_weight=payload_weight)
        wheels[1].update(dt, target_rpm=target_speed, payload_weight=payload_weight)
        
        l_gripper.update(dt, command=grip_cmd)
        r_gripper.update(dt, command=grip_cmd)

        # Запись в буфер
        with state.lock:
            state.time.append(elapsed_time)
            state.pitch.append(sim_pitch)
            state.roll.append(sim_roll)
            for i in range(4):
                state.limbs[i].append(limbs[i].current_angle)
                
            state.grip_L_pressure.append(l_gripper.current_pressure)
            state.grip_R_pressure.append(r_gripper.current_pressure)
            
            state.wheel_target.append(target_speed)
            state.wheel_actual_L.append(wheels[0].current_rpm)
            state.wheel_actual_R.append(wheels[1].current_rpm)

        elapsed_loop = time.time() - t_start
        sleep_time = dt - elapsed_loop
        if sleep_time > 0:
            time.sleep(sleep_time)

# ==========================================
# 3. ПОТОК ИНТЕРФЕЙСА (DASHBOARD 2x2)
# ==========================================
def run_gui():
    plt.ion() 
    fig, ((ax_imu, ax_limbs), (ax_grip, ax_wheels)) = plt.subplots(2, 2, figsize=(14, 8))
    plt.subplots_adjust(bottom=0.25, hspace=0.4, wspace=0.3) 
    fig.suptitle("LIVE Отладка: Телеметрия робота-складовщика", fontsize=14, fontweight='bold')

    WINDOW_SIZE = 15.0

    # --- 1. IMU (Верх-лево) --- РАСШИРИЛИ ОСИ Y
    ax_imu.set_ylim(-35, 35) 
    ax_imu.set_xlim(0, WINDOW_SIZE)
    ax_imu.set_title("IMU (Платформа)", fontsize=10)
    ax_imu.grid(True, alpha=0.3)
    line_pitch, = ax_imu.plot([], [], 'b-', label='Pitch', linewidth=1.5)
    line_roll, = ax_imu.plot([], [], 'orange', label='Roll', linewidth=1.5)
    ax_imu.axhline(0, color='black', linestyle='--', alpha=0.3)
    ax_imu.axhline(28, color='red', linestyle=':', alpha=0.5, label='Падение') # Показываем уровень пола
    ax_imu.axhline(-28, color='red', linestyle=':', alpha=0.5)
    ax_imu.legend(loc='upper right')

    # --- 2. Моторы конечностей (Верх-право) --- РАСШИРИЛИ ОСИ Y
    ax_limbs.set_ylim(-45, 45) 
    ax_limbs.set_xlim(0, WINDOW_SIZE)
    ax_limbs.set_title("Углы моторов конечностей (град)", fontsize=10)
    ax_limbs.grid(True, alpha=0.3)
    colors_limbs = ['red', 'green', 'blue', 'purple']
    lines_limbs = []
    for i in range(4):
        line, = ax_limbs.plot([], [], color=colors_limbs[i], label=f'Мотор {i}', linewidth=1.5)
        lines_limbs.append(line)
    ax_limbs.axhline(0, color='black', linestyle='--', alpha=0.3)
    ax_limbs.legend(loc='upper right', fontsize=8)

    # --- 3. Пневматика (Низ-лево) ---
    ax_grip.set_ylim(-0.5, 7.0)
    ax_grip.set_xlim(0, WINDOW_SIZE)
    ax_grip.set_title("Давление в пневмо-подушках (Бар)", fontsize=10)
    ax_grip.grid(True, alpha=0.3)
    line_grip_L, = ax_grip.plot([], [], 'm-', label='Левый хват', linewidth=2)
    line_grip_R, = ax_grip.plot([], [], 'c-', label='Правый хват', linewidth=2)
    ax_grip.axhline(1.0, color='black', linestyle=':', linewidth=2, label='Порог (1.0)')
    ax_grip.legend(loc='upper right')

    # --- 4. Колеса (Низ-право) ---
    ax_wheels.set_ylim(-110, 110)
    ax_wheels.set_xlim(0, WINDOW_SIZE)
    ax_wheels.set_title("Колеса: Цель vs Реальность", fontsize=10)
    ax_wheels.grid(True, alpha=0.3)
    line_w_target, = ax_wheels.plot([], [], 'k--', label='Цель RPM', linewidth=2)
    line_w_L, = ax_wheels.plot([], [], 'r-', label='Реальн. Лев.', linewidth=2)
    line_w_R, = ax_wheels.plot([], [], 'b-', label='Реальн. Прав.', linewidth=2)
    ax_wheels.axhline(0, color='grey', linestyle='-', alpha=0.3)
    ax_wheels.legend(loc='upper right', fontsize=8)

    # --- Виджеты ---
    ax_kp = plt.axes([0.15, 0.13, 0.3, 0.03])
    ax_ki = plt.axes([0.15, 0.09, 0.3, 0.03])
    ax_kd = plt.axes([0.15, 0.05, 0.3, 0.03])
    ax_speed = plt.axes([0.6, 0.13, 0.3, 0.03])
    
    ax_btn_grab = plt.axes([0.6, 0.05, 0.13, 0.04])
    ax_btn_drop = plt.axes([0.75, 0.05, 0.13, 0.04])
    ax_btn_kick = plt.axes([0.6, 0.005, 0.28, 0.04])

    s_kp = Slider(ax_kp, 'Kp', 0.0, 50.0, valinit=state.kp)
    s_ki = Slider(ax_ki, 'Ki', 0.0, 5.0, valinit=state.ki)
    s_kd = Slider(ax_kd, 'Kd', 0.0, 20.0, valinit=state.kd)
    s_speed = Slider(ax_speed, 'RPM', -100.0, 100.0, valinit=0.0)
    
    btn_grab = Button(ax_btn_grab, 'Взять 5 кг')
    btn_drop = Button(ax_btn_drop, 'Бросить')
    btn_kick = Button(ax_btn_kick, 'УДАР (Возмущение)')

    def update_sliders(val):
        with state.lock:
            state.kp = s_kp.val
            state.ki = s_ki.val
            state.kd = s_kd.val
            state.target_speed = s_speed.val

    s_kp.on_changed(update_sliders)
    s_ki.on_changed(update_sliders)
    s_kd.on_changed(update_sliders)
    s_speed.on_changed(update_sliders)

    def grab(event):
        with state.lock:
            state.grip_cmd = "grip"
            state.payload_held = True
            state.payload_weight = 5.0
        threading.Timer(0.5, set_grip_cmd_safe, args=["hold"]).start()

    def drop(event):
        with state.lock:
            state.grip_cmd = "release"
            state.payload_held = False
            state.payload_weight = 0.0
        threading.Timer(0.5, set_grip_cmd_safe, args=["hold"]).start()

    def kick(event):
        with state.lock:
            state.external_kick = True

    btn_grab.on_clicked(grab)
    btn_drop.on_clicked(drop)
    btn_kick.on_clicked(kick)

    time.sleep(0.1)
    fig.canvas.draw()

    print("[GUI] Дашборд запущен.")
    
    while state.is_running and plt.get_fignums():
        with state.lock:
            t_data = list(state.time)
            pitch_data = list(state.pitch)
            roll_data = list(state.roll)
            limbs_data = [list(l) for l in state.limbs]
            grip_L_data = list(state.grip_L_pressure)
            grip_R_data = list(state.grip_R_pressure)
            w_target_data = list(state.wheel_target)
            w_L_data = list(state.wheel_actual_L)
            w_R_data = list(state.wheel_actual_R)

        if len(t_data) > 1:
            line_pitch.set_data(t_data, pitch_data)
            line_roll.set_data(t_data, roll_data)
            for i in range(4):
                lines_limbs[i].set_data(t_data, limbs_data[i])
                
            line_grip_L.set_data(t_data, grip_L_data)
            line_grip_R.set_data(t_data, grip_R_data)
            
            line_w_target.set_data(t_data, w_target_data)
            line_w_L.set_data(t_data, w_L_data)
            line_w_R.set_data(t_data, w_R_data)

            current_t = t_data[-1]
            if current_t <= WINDOW_SIZE:
                for ax in [ax_imu, ax_limbs, ax_grip, ax_wheels]:
                    ax.set_xlim(0, WINDOW_SIZE)
            else:
                for ax in [ax_imu, ax_limbs, ax_grip, ax_wheels]:
                    ax.set_xlim(current_t - WINDOW_SIZE, current_t + 0.5)

            fig.canvas.draw()
            fig.canvas.flush_events()
            
        time.sleep(0.03)

    state.is_running = False

# ==========================================
# ЗАПУСК
# ==========================================
if __name__ == "__main__":
    sim_thread = threading.Thread(target=simulation_thread_func, daemon=True)
    sim_thread.start()

    try:
        run_gui()
    except KeyboardInterrupt:
        state.is_running = False
    
    sim_thread.join()