from dataclasses import dataclass

@dataclass
class IncreasedMovementSpeedComponent:
    increase_percent: float

@dataclass
class IncreasedAbilitySpeedComponent:
    increase_percent: float

@dataclass
class IncreasedDamageComponent:
    increase_percent: float
    
    