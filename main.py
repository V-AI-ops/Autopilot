import sys
from autopilot import Autopilot
from cli import CLIHandler
from flight_controller import FlightController


def main():
    print("-= Запуск Эмулятора Автопилота Дрона =-")
    
    fc = FlightController()
    autopilot = Autopilot(flight_controller=fc)

    autopilot.start()

    cli = CLIHandler(fc=fc, autopilot=autopilot)
    print("Система готова. Введите команду (например, 'status' или 'enable'):\n")

    try:
        while True:
            user_input = input("> ")
            should_continue = cli.process_command(user_input)
            if not should_continue:
                break
    except (KeyboardInterrupt, EOFError):
        print("\nПолучен сигнал прерывания...")
    finally:
        print("Завершение фоновых потоков...")
        autopilot.stop()
        print("Программа успешно завершена")


if __name__ == "__main__":
    main()