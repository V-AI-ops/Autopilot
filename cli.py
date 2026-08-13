from autopilot import Autopilot
from flight_controller import FlightController


class CLIHandler:
    """Обработчик пользовательских команд консоли"""

    def __init__(self, fc: FlightController, autopilot: Autopilot):
        self._fc = fc
        self._autopilot = autopilot

    def process_command(self, user_input: str) -> bool:
        """Возвращает False, если введена команда 'exit', иначе True"""
        tokens = user_input.strip().split()
        if not tokens:
            return True

        cmd = tokens[0].lower()

        try:
            if cmd == "exit":
                return False

            elif cmd == "enable":
                self._autopilot.enable()
                print("Автопилот включён")

            elif cmd == "disable":
                self._autopilot.disable()
                print("Автопилот выключен")

            elif cmd == "target":
                self._handle_target_command(tokens[1:])

            elif cmd == "coef":
                if len(tokens) == 3:
                    kp_r = float(tokens[1])
                    kp_p = float(tokens[2])
                    self._autopilot.set_coefficients(kp_r, kp_p)
                    print(f"Коэффициенты управления изменены: KP_ROLL={kp_r}, KP_PITCH={kp_p}")
                else:
                    print("Ошибка: используйте формат 'coef <kp_roll> <kp_pitch>', например 'coef 0.5 0.6'")
            
            elif cmd == "altitude":
                if len(tokens) == 2:
                    alt = float(tokens[1])
                    self._fc.send_altitude(alt)
                    print(f"Высота изменена на {alt:.2f} м")
                else:
                    print("Ошибка: используйте формат 'altitude <число>'")

            elif cmd == "fc":
                self._handle_fc_command(tokens[1:])

            elif cmd == "status":
                self._print_status()

            else:
                print(f"Неизвестная команда: '{cmd}'. Доступные: enable, disable, target, altitude, fc, status, exit")

        except ValueError:
            print("Ошибка: передан неверный тип аргумента (ожидалось число)")
        except Exception as e:
            print(f"Ошибка при выполнения команды: {e}")

        return True

    def _handle_target_command(self, args: list[str]):
        """Обрабатывает варианты команды 'target'"""
        if len(args) == 1 and args[0].lower() == "lost":
            self._autopilot.lose_target()
            print("Сигнал цели потерян.")
        elif len(args) == 2:
            x = int(args[0])
            y = int(args[1])
            self._autopilot.set_target(x, y)
            print(f"Координаты цели установлены: X={x}, Y={y}")
        else:
            print("Ошибка: используйте 'target <x> <y>' или 'target lost'")

    def _handle_fc_command(self, args: list[str]):
        """Обрабатывает варианты команды 'fc'."""
        if len(args) == 1 and args[0].lower() == "disconnect":
            self._fc.disconnect()
            print("Flight Controller отключён.")
        elif len(args) == 1 and args[0].lower() == "connect":
            self._fc.connect()
            print("Flight Controller подключён")
        else:
            print("Ошибка: используйте 'fc connect' или 'fc disconnect'")

    def _print_status(self):
        """Форматированный вывод текущего состояния системы"""
        fc_state = self._fc.get_state()
        ap_status = self._autopilot.get_status()

        conn_str = "CONNECTED" if fc_state.is_connected else "DISCONNECTED"
        target = ap_status["target"]
        dx = ap_status["dx"]
        dy = ap_status["dy"]

        print("\n" + "=" * 30)
        print("FLIGHT CONTROLLER")
        print(f"Connection: {conn_str}")
        print(f"Altitude: {fc_state.altitude:.2f} m")
        print(f"MODE: {ap_status['mode'].value}")
        print(f"COEFS: Roll={ap_status['kp_roll']:.2f}, Pitch={ap_status['kp_pitch']:.2f}")
        
        print("TARGET:")
        if target:
            print(f"  X: {target.x}")
            print(f"  Y: {target.y}")
            print(f"  DX: {dx:+d}")
            print(f"  DY: {dy:+d}")
        else:
            print("  NONE")

        rc = fc_state.rc
        print("RC:")
        print(f"  Roll: {rc.roll}")
        print(f"  Pitch: {rc.pitch}")
        print(f"  Yaw: {rc.yaw}")
        print(f"  Throttle: {rc.throttle}")
        print("=" * 30 + "\n")