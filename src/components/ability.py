"""Abilities component."""

from dataclasses import dataclass
from typing import List, Optional

from target_strategy import TargetStrategy
from effects import Effect
from unit_condition import UnitCondition

@dataclass
class Condition:
    """A condition that must be met for an ability to be used."""

@dataclass
class Cooldown(Condition):
    """Ability until the last time it triggered was `duration` seconds ago."""

    duration: float
    """The duration of the cooldown."""

@dataclass
class HasTarget(Condition):
    """Ability requires a target that satisfies the given condition."""

    unit_condition: UnitCondition
    """The condition that the target must satisfy."""

@dataclass
class SatisfiesUnitCondition(Condition):
    """Ability requires the unit using the ability to meet the given condition."""

    unit_condition: UnitCondition
    """The condition that must be met."""

@dataclass
class Ability:
    """An ability that a unit can use."""

    target_strategy: TargetStrategy
    """The targeting strategy for the ability."""

    trigger_conditions: List[Condition]
    """The conditions that must be met for the ability to be used."""

    persistent_conditions: List[Condition]
    """The conditions that must be met for the ability to remain active."""

    effects: dict[int, List[Effect]]
    """The effects of the ability, indexed by which frame they are activated on."""

    target: Optional[int] = None
    """The locked in target of the ability, if any.
    
    The targeting strategy is used to find the target, but once the ability starts,
    the current target is locked in until the ability ends.
    """

    last_used: float = float("-inf")
    """The timestamp of when the ability was last used."""

@dataclass
class Abilities:
    """A collection of abilities."""

    abilities: List[Ability]
    """The abilities of the unit, in priority order.
    
    The lower the index, the higher priority the ability.
    """
