from dataclasses import dataclass
from typing import List

@dataclass
class Point3D:
    x: float
    y: float
    z: float

@dataclass
class FaceLandmarks:
    points: List[Point3D]
