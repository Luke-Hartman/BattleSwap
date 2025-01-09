from typing import List

from dataclasses import dataclass

from components.ability import Condition
from target_strategy import TargetStrategy
from effects import Effect

@dataclass
class InstantAbility():
    """An ability that can be used without an animation."""

    target_strategy: TargetStrategy
    trigger_conditions: List[Condition]
    effects: List[Effect]
    time_since_last_use: float = float("inf")

@dataclass
class InstantAbilities():
    """A collection of instant abilities."""

    abilities: List[InstantAbility]
