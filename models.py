from dataclasses import dataclass
from enum import Enum
from typing import Optional


class AutopilotMode(Enum):
    DISABLED = "DISABLED"
    SEARCH = "SEARCH"
    ACTIVE = "ACTIVE"
    FAILSAFE = "FAILSAFE"


@dataclass
class RCCommand:
    roll: int = 1500
    pitch: int = 1500
    yaw: int = 1500
    throttle: int = 1000


@dataclass
class Target:
    x: int
    y: int
    last_updated: float


@dataclass
class FCState:
    is_connected: bool
    altitude: float
    rc: RCCommand