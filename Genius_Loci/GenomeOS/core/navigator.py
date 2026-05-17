import math
from core.motion_controller import MotionController
from core.logger import get_logger

class NavigatorState:
    IDLE = "idle"
    ROTATING = "rotating"
    DRIVING = "driving"
    WAITING_SERVER = "waiting_server"

class Navigator:
    def __init__(self, motion_ctrl: MotionController, config: dict):
        self.motion_ctrl = motion_ctrl
        self.config = config
        self.logger = get_logger("Core.Navigator")
        
        self.state = NavigatorState.IDLE
        self.route_queue = []
        self.local_map = {}
        self.current_x = 0.0
        self.current_y = 0.0
        self.current_yaw = 0.0
        self.logger.info("Навигатор инициализирован. Состояние: IDLE")

    def load_map(self, map_data: dict):
        self.local_map = map_data
        self.logger.info(f"Загружена топологическая карта. Узлов: {len(map_data)}")

    def set_route(self, route_array: list):
        if not route_array:
            self.logger.warning("Получен пустой маршрут, игнорирую.")
            return
            
        self.route_queue = route_array
        if self.route_queue:
            self.state = NavigatorState.ROTATING
            self.logger.info(f"НОВЫЙ МАРШРУТ установлен: {' -> '.join(self.route_queue)}")

    def update(self, dt: float, imu_yaw: float) -> dict:
        if self.state == NavigatorState.IDLE or not self.route_queue:
            return self.motion_ctrl.compute_drive(0.0, 0.0)

        self.current_yaw = imu_yaw 
        target_node_id = self.route_queue[0]
        target_node = self.local_map.get(target_node_id)

        if not target_node:
            self.logger.error(f"Узел '{target_node_id}' отсутствует в локальной карте!")
            self.route_queue.pop(0)
            return self.motion_ctrl.compute_drive(0.0, 0.0)

        dx = target_node["x"] - self.current_x
        dy = target_node["y"] - self.current_y
        distance_to_target = math.hypot(dx, dy)
        target_yaw = math.atan2(dy, dx)

        angle_error = math.atan2(math.sin(target_yaw - self.current_yaw), math.cos(target_yaw - self.current_yaw))

        # --- Конечный автомат ---
        if self.state == NavigatorState.ROTATING:
            if abs(angle_error) > self.config["yaw_tolerance_rad"]:
                turn_speed = self.config["turn_speed_radps"] if angle_error > 0 else -self.config["turn_speed_radps"]
                self.logger.debug(f"[{target_node_id}] Разворот. Ошибка угла: {math.degrees(angle_error):.1f}°")
                return self.motion_ctrl.compute_drive(0.0, turn_speed)
            else:
                self.state = NavigatorState.DRIVING
                self.logger.info(f"[{target_node_id}] Цель зафиксирована (ошибка {math.degrees(angle_error):.1f}°). Переход к DRIVING.")

        if self.state == NavigatorState.DRIVING:
            self.logger.debug(f"[{target_node_id}] Движение. Осталось: {distance_to_target:.2f}м")
            if distance_to_target > self.config["reach_tolerance_m"]:
                speed_factor = min(1.0, distance_to_target / 1.0)
                linear_speed = self.config["max_linear_mps"] * speed_factor
                correction_speed = angle_error * 2.0 
                return self.motion_ctrl.compute_drive(linear_speed, correction_speed)
            else:
                self.logger.info(f">>> ДОСТИГНУТ ЧЕКПОИНТ: {target_node_id}. Остановка.")
                self.route_queue.pop(0)
                self.state = NavigatorState.WAITING_SERVER
                
                cmd = self.motion_ctrl.compute_drive(0.0, 0.0)
                cmd["server_report"] = {
                    "event": "checkpoint_reached",
                    "node_id": target_node_id,
                    "route_left": self.route_queue
                }
                return cmd

        if self.state == NavigatorState.WAITING_SERVER:
            # Логируем раз в секунду (примерно), чтобы не спамить
            if int(dt * 1000) % 1000 == 0:
                 self.logger.debug(f"Ожидаю указаний от сервера. В очереди: {len(self.route_queue)} точек")
            return self.motion_ctrl.compute_drive(0.0, 0.0)
            
        return self.motion_ctrl.compute_drive(0.0, 0.0)