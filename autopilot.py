import time
import threading
from typing import Optional

import config
from exceptions import FCConnectionError
from flight_controller import FlightController
from models import AutopilotMode, RCCommand, Target


class Autopilot:
    """Модуль автопилота в отдельном потоке"""

    def __init__(self, flight_controller: FlightController):
        self._fc = flight_controller
        self._mode: AutopilotMode = AutopilotMode.DISABLED
        self._target: Optional[Target] = None
        self._lock = threading.Lock()
        
        self._kp_roll: float = config.KP_ROLL
        self._kp_pitch: float = config.KP_PITCH
        
        self._is_running: bool = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """Запускает фоновый поток логики автопилота"""
        self._is_running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Останавливает фоновый поток при выходе из программы"""
        self._is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def enable(self):
        """Включает автопилот (переводит в SEARCH или FAILSAFE)"""
        with self._lock:
            if not self._fc.is_connected():
                self._mode = AutopilotMode.FAILSAFE
            else:
                self._mode = AutopilotMode.SEARCH

    def disable(self):
        """Выключает автопилот"""
        with self._lock:
            self._mode = AutopilotMode.DISABLED
            self._target = None

    def set_coefficients(self, kp_roll: float, kp_pitch: float):
        """Позволяет настраивать коэффициенты управления"""
        with self._lock:
            self._kp_roll = float(kp_roll)
            self._kp_pitch = float(kp_pitch)

    def set_target(self, x: int, y: int):
        """Устанавливает или обновляет координаты цели"""
        with self._lock:
            self._target = Target(x=x, y=y, last_updated=time.time())
            if self._mode == AutopilotMode.SEARCH:
                self._mode = AutopilotMode.ACTIVE

    def lose_target(self):
        """Имитирует мгновенную потерю цели"""
        with self._lock:
            self._target = None
            if self._mode == AutopilotMode.ACTIVE:
                self._mode = AutopilotMode.SEARCH

    def get_status(self) -> dict:
        """Возвращает информацию о текущем состоянии автопилота"""
        with self._lock:
            dx, dy = None, None
            if self._target:
                dx = self._target.x - config.CENTER_X
                dy = self._target.y - config.CENTER_Y

            return {
                "mode": self._mode,
                "target": self._target,
                "dx": dx,
                "dy": dy,
                "kp_roll": self._kp_roll,  
                "kp_pitch": self._kp_pitch
            }

    def _run_loop(self):
        """Основной цикл автопилота (выполняется в фоновом потоке 20 раз в секунду)"""
        while self._is_running:
            self._update_logic()
            time.sleep(0.05)  # 1/0.05 20 Гц

    def _update_logic(self):
        """Проверка состояний, таймаутов и формирование RC-команд"""
        with self._lock:
            # Проверка связи с Flight Controller
            if not self._fc.is_connected():
                self._mode = AutopilotMode.FAILSAFE
            elif self._mode == AutopilotMode.FAILSAFE and self._fc.is_connected():
                # Автовосстановление связи
                self._mode = AutopilotMode.SEARCH if self._target is None else AutopilotMode.ACTIVE

            # Если выключен
            if self._mode == AutopilotMode.DISABLED:
                return

            # Если в режиме FAILSAFE — отправляем аварийную RC-команду
            if self._mode == AutopilotMode.FAILSAFE:
                self._send_failsafe_command()
                return

            # Проверка таймаута цели (ACTIVE -> SEARCH)
            if self._mode == AutopilotMode.ACTIVE and self._target:
                if time.time() - self._target.last_updated > config.TARGET_TIMEOUT:
                    self._target = None
                    self._mode = AutopilotMode.SEARCH

            # Расчёт и отправка управления
            if self._mode == AutopilotMode.ACTIVE and self._target:
                command = self._calculate_rc(self._target)
                try:
                    self._fc.send_rc(command)
                except FCConnectionError:
                    self._mode = AutopilotMode.FAILSAFE
            elif self._mode == AutopilotMode.SEARCH:
                # В режиме поиска удерживаем нейтральные каналы
                try:
                    self._fc.send_rc(RCCommand())
                except FCConnectionError:
                    self._mode = AutopilotMode.FAILSAFE

    def _calculate_rc(self, target: Target) -> RCCommand:
        """Вычисляет RC-команды на основе отклонения цели от центра кадра"""
        dx = target.x - config.CENTER_X
        dy = target.y - config.CENTER_Y

        # ROLL (Ось X) 
        if abs(dx) <= config.DEADZONE:
            roll = config.RC_NEUTRAL
        else:
            # Используем настраиваемый коэффициент self._kp_roll
            roll = int(config.RC_NEUTRAL + self._kp_roll * dx)

        # PITCH (Ось Y) 
        if abs(dy) <= config.DEADZONE:
            pitch = config.RC_NEUTRAL
        else:
            # Настраиваемый коэффициент self._kp_pitch
            pitch = int(config.RC_NEUTRAL + self._kp_pitch * dy)

        roll = max(config.RC_MIN, min(config.RC_MAX, roll))
        pitch = max(config.RC_MIN, min(config.RC_MAX, pitch))

        return RCCommand(
            roll=roll,
            pitch=pitch,
            yaw=config.RC_NEUTRAL,
            throttle=1200 
        )

    def _send_failsafe_command(self):
        """Отправляет нейтрально-аварийные команды при FAILSAFE"""
        try:
            self._fc.send_rc(RCCommand(
                roll=config.RC_NEUTRAL,
                pitch=config.RC_NEUTRAL,
                yaw=config.RC_NEUTRAL,
                throttle=config.RC_MIN  # Сброс газа при аварии
            ))
        except FCConnectionError:
            pass  # FC полностью отключен, игнорируем ошибку