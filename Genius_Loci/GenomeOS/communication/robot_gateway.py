import json
import threading
import time
import paho.mqtt.client as mqtt
from core.logger import get_logger

class RobotGateway:
    def __init__(self, config: dict, mission_executor=None):
        self.config = config
        self.mission_executor = mission_executor
        self.logger = get_logger("Comm.Gateway")
        
        self.robot_id = config["robot_id"]
        
        # Формируем топики на основе ID робота
        self.topic_commands = f"warehouse/robots/{self.robot_id}/commands"
        self.topic_events = f"warehouse/robots/{self.robot_id}/events"
        self.topic_telemetry = f"warehouse/robots/{self.robot_id}/telemetry"
        
        self.client = mqtt.Client(client_id=self.robot_id)
        
        # Назначаем обработчики событий MQTT
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        
        # LWT (Last Will and Testament) - Сообщение, если робот внезапно выключится
        self.client.will_set(self.topic_telemetry, payload=json.dumps({"status": "offline"}), qos=1)

        self._is_connected = False

    def connect(self):
        """Запуск фонового потока подключения к брокеру"""
        threading.Thread(target=self._connect_thread, daemon=True).start()

    def _connect_thread(self):
        try:
            self.logger.info(f"Подключение к MQTT брокеру {self.config['broker_address']}...")
            self.client.connect(self.config["broker_address"], self.config["broker_port"], self.config["keepalive"])
            # Запускаем бесконечный цикл обработки сети в фоне
            self.client.loop_start()
        except Exception as e:
            self.logger.error(f"КРИТИЧЕСКОЕ: Не удалось подключиться к брокеру: {e}. Работаем автономно.")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._is_connected = True
            self.logger.info("Успешно подключен к серверу!")
            # Подписываемся на команды
            client.subscribe(self.topic_commands, qos=self.config["qos"])
            self.logger.info(f"Подписан на топик команд: {self.topic_commands}")
        else:
            self.logger.error(f"Ошибка подключения к MQTT. Код: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        self._is_connected = False
        self.logger.warning(f"Отключен от MQTT брокера. Код: {rc}. Попытка переподключения...")

    def _on_message(self, client, userdata, msg):
        """Обработчик входящих команд от Сервера Диспетчера"""
        try:
            payload = json.loads(msg.payload.decode())
            self.logger.info(f"<<< ПОЛУЧЕНА КОМАНДА С СЕРВЕРА: {payload.get('command_type')}")

            if not self.mission_executor:
                self.logger.error("MissionExecutor не привязан к шлюзу, команда проигнорирована!")
                return

            cmd_type = payload.get("command_type")

            if cmd_type == "assign_mission":
                route = payload.get("route", [])
                action = payload.get("action", "grab")
                self.mission_executor.set_mission(route=route, action=action)

            elif cmd_type == "emergency_stop":
                self.logger.warning("!!! ВНЕШНИЙ ЭКСТРЕННОЙ СТОП !!!")
                # Здесь должен быть вызов функции полного обесточивания моторов
                self.mission_executor.state = MissionState.IDLE # Импортировать Enum или использовать строку

            elif cmd_type == "cancel_mission":
                self.logger.info("Миссия отменена сервером.")
                self.mission_executor.state = MissionState.IDLE
                
        except json.JSONDecodeError:
            self.logger.error(f"Получен невалидный JSON: {msg.payload}")
        except Exception as e:
            self.logger.error(f"Ошибка обработки команды: {e}")

    def send_event(self, event_data: dict):
        """Метод, который будет выступать callback-ом для MissionExecutor"""
        if not self._is_connected:
            self.logger.debug("Сеть недоступна, событие не отправлено.")
            return
            
        try:
            payload_json = json.dumps(event_data)
            result = self.client.publish(self.topic_events, payload_json, qos=self.config["qos"])
            # В лог пишем только важные события (не спамим DEBUG от навигатора)
            if event_data.get("event") in ["checkpoint_reached", "mission_step_done", "blocked"]:
                self.logger.info(f">>> СОБЫТИЕ ОТПРАВЛЕНО НА СЕРВЕР: {event_data.get('event')}")
        except Exception as e:
            self.logger.error(f"Ошибка отправки события: {e}")

    def send_telemetry(self, telemetry_data: dict):
        """Периодическая рассылка состояния (координаты, батарея, состояние)"""
        if not self._is_connected:
            return
            
        try:
            payload_json = json.dumps(telemetry_data)
            self.client.publish(self.topic_telemetry, payload_json, qos=0) # QoS 0 для телеметрии (не критично если 1 пакет потеряется)
        except Exception as e:
            self.logger.error(f"Ошибка отправки телеметрии: {e}")