# Размеры кадра
FRAME_WIDTH: int = 640
FRAME_HEIGHT: int = 480
CENTER_X: int = FRAME_WIDTH // 2
CENTER_Y: int = FRAME_HEIGHT // 2

# Границы и нейтраль RC-каналов
RC_MIN: int = 1000
RC_MAX: int = 2000
RC_NEUTRAL: int = 1500

# Таймауты (в секундах)
TARGET_TIMEOUT: float = 2.0  # Макс. время жизни цели без обновлений
FC_TIMEOUT: float = 2.0      # Макс. время отсутствия ответа от FC

# Настройки пропорционального регулятора (P-controller)
DEADZONE: int = 15     # Мёртвая зона вокруг центра кадра (в px)
KP_ROLL: float = 0.8   # Коэффициент управления по оси Roll (X)
KP_PITCH: float = 0.8  # Коэффициент управления по оси Pitch (Y)