"""Targetting strategy logic for Battle Swap."""

from abc import ABC, abstractmethod
from typing import Optional

import esper

from CONSTANTS import TARGETTING_SWITCH_BIAS
from components.health import Health
from components.position import Position
from components.team import Team
from unit_condition import Alive, UnitCondition


class TargetStrategy(ABC):
    """Represents a target strategy."""

    def __init__(
        self,
        targeting_range: Optional[float],
        y_bias: Optional[float],
        unit_condition: UnitCondition
    ):
        self.targeting_range = targeting_range
        self.y_bias = y_bias
        self._target = None
        self.unit_condition = unit_condition

    @abstractmethod
    def find_target(self, entity: int) -> Optional[int]:
        """Find the target for the given entity."""

    @property
    def target(self) -> Optional[int]:
        """Get the target for the given entity."""
        return self._target

    @target.setter
    def target(self, target: Optional[int]):
        self._target = target

class FindMostDamaged(TargetStrategy):
    """The most damaged target strategy."""

    def find_target(self, entity: int) -> Optional[int]:
        """Find the most damaged target nearby self for the given entity."""
        pos = esper.component_for_entity(entity, Position)
        self.target = None
        max_missing_health = 0
        max_missing_health_distance = float('inf')  # tie breaker
        for other_entity, (other_pos,) in esper.get_components(Position):
            if not self.unit_condition.check(other_entity):
                continue
            distance = pos.distance(other_pos, self.y_bias)
            if self.targeting_range is not None and distance > self.targeting_range:
                continue
            health = esper.component_for_entity(other_entity, Health)
            missing_health = health.maximum - health.current
            if missing_health == 0:
                continue
            if missing_health == max_missing_health:
                if distance < max_missing_health_distance:
                    max_missing_health_distance = distance
                    self.target = other_entity
            elif missing_health > max_missing_health:
                max_missing_health = missing_health
                max_missing_health_distance = distance
                self.target = other_entity
        return self.target

class FindNearest(TargetStrategy):
    """The nearest target strategy."""

    def find_target(self, entity: int) -> Optional[int]:
        """Find the nearest enemy target for the given entity."""
        pos = esper.component_for_entity(entity, Position)
        # Prefer targeting the same entity
        bias_towards = set() if self.target is None else {self.target}
        self.target = None
        min_distance = float('inf')
        for other_entity, (other_pos,) in esper.get_components(Position):
            if not self.unit_condition.check(other_entity):
                continue
            distance = pos.distance(other_pos, self.y_bias)
            if self.targeting_range is not None and distance > self.targeting_range:
                continue
            if other_entity in bias_towards:
                if distance < min_distance + TARGETTING_SWITCH_BIAS:
                    min_distance = distance
                    self.target = other_entity
            else:
                if distance < min_distance:
                    min_distance = distance
                    self.target = other_entity
        return self.target

class FindStrongest(TargetStrategy):
    """The strongest target strategy."""

    def find_target(self, entity: int) -> Optional[int]:
        """Find the strongest ally target for the given entity."""
        team = esper.component_for_entity(entity, Team)
        pos = esper.component_for_entity(entity, Position)
        # Prefer targeting the same entity
        bias_towards = set() if self.target is None else {self.target}
        self.target = None
        highest_max_health = 0
        highest_max_health_distance = float('inf')  # tie breaker
        for other_entity, (other_pos,) in esper.get_components(Position):
            if not self.unit_condition.check(other_entity):
                continue
            distance = pos.distance(other_pos, self.y_bias)
            if self.targeting_range is not None and distance > self.targeting_range:
                continue
            health = esper.component_for_entity(other_entity, Health)
            if health.maximum == highest_max_health:
                if other_entity in bias_towards:
                    if distance < highest_max_health_distance + TARGETTING_SWITCH_BIAS:
                        highest_max_health_distance = distance
                        self.target = other_entity
                else:
                    if distance < highest_max_health_distance:
                        highest_max_health_distance = distance
                        self.target = other_entity
            elif health.maximum > highest_max_health:
                highest_max_health = health.maximum
                highest_max_health_distance = distance
                self.target = other_entity
        return self.target

class FindNothing(TargetStrategy):
    """The no target strategy."""

    def __init__(self):
        super().__init__(None, None, Alive())

    def find_target(self, entity: int) -> Optional[int]:
        """Find no target for the given entity."""
        return None
