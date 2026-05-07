import time
import logging
import matplotlib
import math
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from hw_abstraction.hardware_interface import HardwareInterface
from core.balancer import BalancerController

# Упрощенная функция рисования (оставил только самое важное)
def plot_balance(history):
    t = history["time"]
    fig, axs = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    fig.suptitle("Замкнутый контур балансировки с компенсацией груза", fontsize=14)

    axs[0].plot(t, history["pitch"], label='Реальный наклон (Pitch)', color='blue')
    axs[0].plot(t, history["roll"], label='Реальный крен (Roll)', color='orange')
    axs[0].axhline(0, color='black', linestyle='--', alpha=0.5)
    axs[0].set_ylabel('Угол (градусы)')
    axs[0].grid(True, alpha=0.3)
    axs[0].legend()
    axs[0].set_title('Показания "IMU" (Датчик положения платформы)')

    axs[1].plot(t, history["limb_0"], label='Перед-Лево', color='red')
    axs[1].plot(t, history["limb_1"], label='Перед-Право', color='green')
    axs[1].plot(t, history["limb_2"], label='Зад-Лево', color='blue')
    axs[1].plot(t, history["limb_3"], label='Зад-Право', color='purple')
    axs[1].axvline(x=2.0, color='black', linestyle=':', label='Взял 5кг груз')
    axs[1].axvline(x=5.0, color='grey', linestyle=':', label='Начал ехать')
    axs[1].axvline(x=8.0, color='grey', linestyle='--', label='Торможение')
    axs[1].set_ylabel('Угол мотора (град)')
    axs[1].set_xlabel('Время (сек)')
    axs[1].grid(True, alpha=0.3)
    axs[1].legend(loc='upper right')
    plt.tight_layout()
    fig.savefig("debug_balance_pid.png", dpi=150)
    plt.close()

def main():
    hw = HardwareInterface(use_simulation=True)
    hw.init_robot()
    
    balancer = BalancerController(hw.config["balancer"]) # Передаем конфиг балансира

    limbs = [hw.get_node(f"limb_motor_{i}") for i in range(4)]
    wheels = [hw.get_node(f"wheel_motor_{i}") for i in range(2)]
    gripper = hw.get_node("gripper_0")

    dt = 0.05
    history = {k: [] for k in ["time", "pitch", "roll", "limb_0", "limb_1", "limb_2", "limb_3"]}
    
    # Имитация физики (Упрощенный инвертированный маятник)
    sim_pitch = 0.0 
    sim_roll = 0.0
    payload_weight = 0.0
    payload_held = False
    target_speed = 0.0
    grip_cmd = "hold"

    print("--- Запуск симуляции балансировки (Closed Loop) ---")
    
    for step in range(int(10.0 / dt)):
        t = step * dt
        
        # --- Сценарий ---
        if 2.0 <= t < 2.5: grip_cmd = "grip"
        if 2.5 <= t < 9.0: 
            payload_held = True
            payload_weight = 5.0
        if 5.0 <= t < 8.0: target_speed = 60.0
        if 8.0 <= t: target_speed = 0.0
        if 9.0 <= t < 9.5: 
            grip_cmd = "release"
            payload_held = False
            payload_weight = 0.0

        # --- 1. Чтение датчиков (Имитация IMU) ---
        # В реальности берем из IMU. Здесь симулируем: 
        # Если моторы не компенсируют, робот заваливается (g = 9.81)
        # Балансируем на задних колесах, поэтому центр масс стремится упасть вперед/назад
        gravity_effect_pitch = 9.81 * math.sin(math.radians(sim_pitch)) * dt
        # Добавляем шум реального мира
        import random
        noise = random.gauss(0, 0.1)
        
        # Обновляем виртуальную физику платформы на основе РЕАЛЬНОГО угла моторов
        # (Упрощение: считаем что платформа следует за средним углом передних и задних моторов)
        actual_control_pitch = (limbs[0].current_angle + limbs[1].current_angle - limbs[2].current_angle - limbs[3].current_angle) / 2
        sim_pitch += gravity_effect_pitch + (actual_control_pitch - sim_pitch) * 0.2 + noise
        
        actual_control_roll = (limbs[0].current_angle - limbs[1].current_angle + limbs[2].current_angle - limbs[3].current_angle) / 2
        sim_roll += (actual_control_roll - sim_roll) * 0.3 + random.gauss(0, 0.05)

        imu_data = {"pitch": sim_pitch, "roll": sim_roll}

        # --- 2. Работа мозга (Balancer) ---
        target_angles = balancer.update(
            dt=dt,
            target_speed=target_speed,
            imu_data=imu_data,
            payload_state={"weight": payload_weight, "is_held": payload_held}
        )

        # --- 3. Отдача команд на моторы ---
        for i in range(4):
            limbs[i].update(dt, target_angle=target_angles[f"limb_motor_{i}"], payload_weight=payload_weight)
        
        for i in range(2):
            wheels[i].update(dt, target_rpm=target_speed, payload_weight=payload_weight)
            
        gripper.update(dt, command=grip_cmd)

        # Логирование
        history["time"].append(t)
        history["pitch"].append(sim_pitch)
        history["roll"].append(sim_roll)
        for i in range(4):
            history[f"limb_{i}"].append(limbs[i].current_angle)

    print("--- Построение графиков... ---")
    plot_balance(history)

if __name__ == "__main__":
    logging.getLogger().setLevel(logging.WARNING)

    main()