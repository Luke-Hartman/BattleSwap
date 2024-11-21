from dataclasses import dataclass

@dataclass
class RangeIndicator:
    range: int
    enabled: bool = False
