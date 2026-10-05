from dataclasses import dataclass
from typing import Tuple

@dataclass
class FeaturesResult:
    ear: float
    mar: float
    pitch: float
    yaw: float
    roll: float
