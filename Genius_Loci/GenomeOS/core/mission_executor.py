import time
import enum
from core.logger import get_logger
from typing import Callable, Dict, Any, Optional

class MissionState(enum.Enum):
    IDLE = "idle"
    NAVIGATE_TO_TARGET = "navigate"
    OBSTACLE_BLOCKED = "obstacle_blocked"
    SEARCHING_CARGO = "searching"
    APPROACHING_CARGO = "approaching"
    GRABBING = "grabbing"
    MISSION_COMPLETE = "complete"

class MissionExecutor:
    def __init__(self, navigator, perception, grippers: list, motion_ctrl, config: dict):
        self.navigator = navigator
        self.perception = perception
        self.grippers = grippers
        self.motion_ctrl = motion_ctrl
        self.config = config
        self.logger = get_logger("Core.MissionExecutor")

        self.state = MissionState.IDLE
        self.server_callback: Optional[Callable] = None
        
        self.state_timer = 0.0
        self.obstacle_wait_timer = 0.0
        self.logger.info("Исполнитель миссий инициализирован. Ожидаю задачи...")

    def set_server_callback(self, func: Callable):
        self.server_callback = func
        self.logger.info("Зарегистрирован callback для отправки отчетов на сервер")

    def set_mission(self, route: list, action: str = "grab"):
        if self.state not in [MissionState.IDLE, MissionState.MISSION_COMPLETE]:
            self.logger.error(f"Попытка начать миссию из состояния {self.state.name}! Отклонено.")
            return
            
        self.logger.info(f"=== НАЧАЛО МИССИИ === Маршрут: {' -> '.join(route)}, Финальное действие: {action}")
        self.navigator.set_route(route)
        self.state = MissionState.NAVIGATE_TO_TARGET
        self.state_timer = 0.0

    def update(self, dt: float, frame, imu_data: Dict[str, float]) -> Dict[str, Any]:
        self.state_timer += dt
        
        # Запускаем тяжелую нейросеть только если мы находимся в режимах поиска
        need_vision = self.state in [MissionState.SEARCHING_CARGO, MissionState.APPROACHING_CARGO]
        scene_data = self.perception.process_frame(frame, run_yolo=need_vision)
        
        drive_cmd = self.motion_ctrl.compute_drive(0.0, 0.0)
        

        if self.state == MissionState.IDLE:
            pass

        elif self.state == MissionState.NAVIGATE_TO_TARGET:
            if scene_data["obstacle_ahead"] and scene_data["obstacle_distance_m"] < 0.4:
                self.state = MissionState.OBSTACLE_BLOCKED
                self.obstacle_wait_timer = 0.0
                self.logger.warning(">>> ПЕРЕХОД В СОСТОЯНИЕ: BLOCKED (Препятствие на пути)")
            else:
                drive_cmd = self.navigator.update(dt, imu_data["yaw"])
                if "server_report" in drive_cmd:
                    report = drive_cmd.pop("server_report")
                    self._send_to_server(report)
                    if not self.navigator.route_queue:
                        self.logger.info(">>> ПЕРЕХОД В СОСТОЯНИЕ: SEARCHING_CARGO (Маршрут завершен)")
                        self.state = MissionState.SEARCHING_CARGO
                        self.state_timer = 0.0

        elif self.state == MissionState.OBSTACLE_BLOCKED:
            self.obstacle_wait_timer += dt
            if not scene_data["obstacle_ahead"]:
                self.logger.info(">>> ПЕРЕХОД В СОСТОЯНИЕ: NAVIGATE (Путь свободен)")
                self.state = MissionState.NAVIGATE_TO_TARGET
            elif self.obstacle_wait_timer > 5.0:
                self.logger.error("Таймаут ожидания (5с)! Препятствие не убрано.")
                self._send_to_server({"event": "blocked", "reason": "obstacle_timeout"})

        elif self.state == MissionState.SEARCHING_CARGO:
            drive_cmd = self.motion_ctrl.compute_drive(0.0, self.config["search_turn_speed"])
            if scene_data["cargo_detected"]:
                self.logger.info(">>> ПЕРЕХОД В СОСТОЯНИЕ: APPROACHING_CARGO (YOLO сработал)")
                self.state = MissionState.APPROACHING_CARGO
                self.state_timer = 0.0
            elif self.state_timer > 10.0:
                self.logger.error(">>> ПЕРЕХОД В СОСТОЯНИЕ: IDLE (Таймаут поиска 10с)")
                self._send_to_server({"event": "error", "reason": "cargo_not_found"})
                self.state = MissionState.IDLE

        elif self.state == MissionState.APPROACHING_CARGO:
            if not scene_data["cargo_detected"]:
                self.logger.warning(">>> ПЕРЕХОД НАЗАД В: SEARCHING_CARGO (Груз потерян из вида)")
                self.state = MissionState.SEARCHING_CARGO
            else:
                dist = scene_data["cargo_distance_m"]
                offset = scene_data["cargo_center_offset"]
                turn_speed = offset * self.config["approach_turn_gain"]
                linear_speed = min(dist * self.config["approach_speed_gain"], self.config["approach_max_speed"])
                drive_cmd = self.motion_ctrl.compute_drive(linear_speed, turn_speed)
                
                self.logger.debug(f"[APPROACH] Дист: {dist:.2f}м, Смещение: {offset:.2f}, V: {linear_speed:.2f}")

                if dist <= self.config["grab_allowed_distance_m"] and abs(offset) < self.config["grab_alignment_tolerance"]:
                    self.logger.info(">>> ПЕРЕХОД В СОСТОЯНИЕ: GRABBING (Груз в зоне захвата)")
                    drive_cmd = self.motion_ctrl.compute_drive(0.0, 0.0)
                    self.state = MissionState.GRABBING
                    self.state_timer = 0.0

        elif self.state == MissionState.GRABBING:
            for g in self.grippers:
                g.update(dt, command="grip")
            
            self.logger.debug(f"Накачка пневматики... ({self.state_timer:.2f}/1.5с)")
            if self.state_timer > 1.5:
                self.logger.info("=== МИССИЯ ВЫПОЛНЕНА УСПЕШНО ===")
                self._send_to_server({"event": "mission_step_done", "status": "cargo_secured"})
                self.state = MissionState.MISSION_COMPLETE

        elif self.state == MissionState.MISSION_COMPLETE:
            pass

        return drive_cmd

    def _send_to_server(self, payload: dict):
        if self.server_callback:
            try:
                self.server_callback(payload)
            except Exception as e:
                self.logger.error(f"КРИТИЧЕСКАЯ ОШИБКА сети при отправке на сервер: {e}")
        else:
            self.logger.info(f"[СЕТЬ (MOCK) -> SERVER] Отправлен пакет: {payload}")