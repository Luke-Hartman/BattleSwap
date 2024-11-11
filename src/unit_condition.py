"""Conditions that a unit may or may not meet."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional

import esper

from components.health import Health
from components.position import Position
from components.team import Team, TeamType
from components.unit_state import State, UnitState

class UnitCondition(ABC):
    """A condition that a unit may or may not meet."""

    @abstractmethod
    def check(self, entity: int) -> bool:
        """Check if the condition is met for the given entity."""

@dataclass
class Not(UnitCondition):
    """The negation of the given condition."""

    condition: UnitCondition
    """The condition to negate."""

    def check(self, entity: int) -> bool:
        return not self.condition.check(entity)

@dataclass
class All(UnitCondition):
    """The conjunction of the given conditions."""

    conditions: List[UnitCondition]
    """The conditions to check."""

    def check(self, entity: int) -> bool:
        return all(condition.check(entity) for condition in self.conditions)

@dataclass
class Any(UnitCondition):
    """The disjunction of the given conditions."""

    conditions: List[UnitCondition]
    """The conditions to check."""

    def check(self, entity: int) -> bool:
        return any(condition.check(entity) for condition in self.conditions)

@dataclass
class Alive(UnitCondition):
    """The unit is alive."""

    def check(self, entity: int) -> bool:
        unit_state = esper.try_component(entity, UnitState)
        return unit_state is not None and unit_state.state != State.DEAD

@dataclass
class NotEntity(UnitCondition):
    """The unit is not the given entity."""

    entity: int
    """The entity to check against."""

    def check(self, entity: int) -> bool:
        return entity != self.entity

@dataclass
class OnTeam(UnitCondition):
    """The unit is on the given team."""

    team: TeamType
    """The team to check against."""

    def check(self, entity: int) -> bool:
        team = esper.try_component(entity, Team)
        return team is not None and team.type == self.team


@dataclass
class HealthBelowPercent(UnitCondition):
    """The unit has less than `percent` health."""

    percent: float
    """The percent of health below which the condition is met."""

    def check(self, entity: int) -> bool:
        health = esper.try_component(entity, Health)
        return health is not None and health.current / health.maximum < self.percent

@dataclass
class MaximumDistanceFromEntity(UnitCondition):
    """The unit is within a certain distance from the given entity."""

    entity: int
    """The entity to check against."""

    distance: float
    """The maximum distance within which the condition is met."""

    y_bias: Optional[float]
    """The y-bias to apply to the distance check."""

    def check(self, entity: int) -> bool:
        position = esper.try_component(self.entity, Position)
        other_position = esper.try_component(entity, Position)
        if position is None or other_position is None:
            return False
        return position.distance(other_position, self.y_bias) <= self.distance

@dataclass
class MinimumDistanceFromEntity(UnitCondition):
    """The unit is at least  a certain distance from the given entity."""

    entity: int
    """The entity to check against."""

    distance: float
    """The minimum distance within which the condition is met."""

    y_bias: Optional[float]
    """The y-bias to apply to the distance check."""

    def check(self, entity: int) -> bool:
        position = esper.try_component(self.entity, Position)
        other_position = esper.try_component(entity, Position)
        if position is None or other_position is None:
            return False
        return position.distance(other_position, self.y_bias) >= self.distance
