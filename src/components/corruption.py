from dataclasses import dataclass

@dataclass
class IncreasedMovementSpeedComponent:
    increase_percent: float

@dataclass
class IncreasedAttackSpeedComponent:
    increase_percent: float

@dataclass
class IncreasedDamageComponent:
    increase_percent: float
    
    