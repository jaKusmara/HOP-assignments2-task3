# src/models.py
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Component:
    """
    Jeden fyzický kus súčiastky.
    width/height už obsahujú +10 cm kvôli izolácii (podľa utils._biggestDimensions).
    """
    sn: str
    width: int
    height: int
    weight: float
    timestamp: datetime
    square: float          # plocha vrátane izolácie
    stress_square: float   # weight / square

    @property
    def dims(self):
        return self.width, self.height
