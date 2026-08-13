import threading
from exceptions import FCConnectionError
from models import FCState, RCCommand


class FlightController:
    """Эмулятор полётного контроллера с защитой потоков"""

    def __init__(self):
        self._lock = threading.Lock()
        self._is_connected: bool = True
        self._altitude: float = 0.0
        self._rc: RCCommand = RCCommand()

    def _check_connection(self):
        """Вспомогательный приватный метод для проверки связи"""
        if not self._is_connected:
            raise FCConnectionError("Flight Controller отключён")

    def is_connected(self) -> bool:
        """Проверяет статус подключения"""
        with self._lock:
            return self._is_connected

    def disconnect(self):
        """Отключает Flight Controller"""
        with self._lock:
            self._is_connected = False

    def connect(self):
        """Восстанавливает подключение"""
        with self._lock:
            self._is_connected = True

    def get_rc(self) -> RCCommand:
        """Возвращает текущее состояние RC-каналов"""
        with self._lock:
            self._check_connection()
            # Возвращаем копию объекта для защиты данных
            return RCCommand(
                roll=self._rc.roll,
                pitch=self._rc.pitch,
                yaw=self._rc.yaw,
                throttle=self._rc.throttle
            )

    def send_rc(self, command: RCCommand):
        """Принимает и сохраняет новую RC-команду"""
        with self._lock:
            self._check_connection()
            self._rc = command

    def get_altitude(self) -> float:
        """Возвращает текущую высоту"""
        with self._lock:
            self._check_connection()
            return self._altitude

    def send_altitude(self, altitude: float):
        """Устанавливает новую высоту симулятора"""
        with self._lock:
            self._check_connection()
            self._altitude = float(altitude)

    def get_state(self) -> FCState:
        """Безопасно снимет snapshot состояния FC без выброса ошибок."""
        with self._lock:
            return FCState(
                is_connected=self._is_connected,
                altitude=self._altitude,
                rc=RCCommand(
                    roll=self._rc.roll,
                    pitch=self._rc.pitch,
                    yaw=self._rc.yaw,
                    throttle=self._rc.throttle
                )
            )