"""Targetting strategy logic for Battle Swap."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

import esper

from components.health import Health
from components.position import Position
from unit_condition import UnitCondition

from enum import Enum, auto

class TargetingGroup(Enum):
    """Enum for different pre-filtered unit sets."""

    TEAM1_LIVING = auto()
    TEAM2_LIVING = auto()
    EMPTY = auto()


class Ranking(ABC):

    def __init__(self, ascending: bool, unit_condition: Optional[UnitCondition] = None):
        self.ascending = ascending
        self.unit_condition = unit_condition

    def key(self, ent: int) -> float:
        if self.unit_condition is not None and not self.unit_condition.check(ent):
            return float('inf')
        if self.ascending:
            return self._key(ent)
        return -self._key(ent)

    @abstractmethod
    def _key(self, ent: int) -> float:
        ...

class WeightedRanking(Ranking):

    def __init__(self, rankings: Dict[Ranking, float], unit_condition: Optional[UnitCondition] = None, ascending: bool = True):
        self.rankings = rankings
        super().__init__(
            ascending=ascending,
            unit_condition=unit_condition
        )

    def _key(self, ent: int) -> float:
        return sum(ranking.key(ent) * weight for ranking, weight in self.rankings.items())

class ByDistance(Ranking):

    def __init__(
        self,
        entity: int,
        y_bias: Optional[float] = None,
        unit_condition: Optional[UnitCondition] = None,
        ascending: bool = True
    ):
        self.entity = entity
        self.y_bias = y_bias
        super().__init__(
            unit_condition=unit_condition,
            ascending=ascending
        )

    def _key(self, ent: int) -> float:
        e_pos = esper.component_for_entity(self.entity, Position)
        a_pos = esper.component_for_entity(ent, Position)
        return e_pos.distance(a_pos, self.y_bias)

class ByMissingHealth(Ranking):

    def _key(self, ent: int) -> float:
        if self.unit_condition is not None and not self.unit_condition.check(ent):
            return float('inf')
        health = esper.component_for_entity(ent, Health)
        return (health.maximum - health.current)

class ByMaxHealth(Ranking):

    def _key(self, ent: int) -> float:
        health = esper.component_for_entity(ent, Health)
        return health.maximum

class ByCurrentHealth(Ranking):

    def _key(self, ent: int) -> float:
        health = esper.component_for_entity(ent, Health)
        return health.current

class ConditionPenalty(Ranking):

    def __init__(self, condition_to_check: UnitCondition, value: float, ascending: bool = True):
        # Note that self.unit_condition means something else
        self.condition_to_check = condition_to_check
        self.value = value
        super().__init__(ascending=ascending)

    def _key(self, ent: int) -> float:
        return self.value if self.condition_to_check.check(ent) else 0

class TargetStrategy:
    """Represents a target strategy."""

    def __init__(
        self,
        unit_condition: Optional[UnitCondition],
        rankings: List[Ranking],
        targetting_group: TargetingGroup
    ):
        self._target = None
        self.unit_condition = unit_condition
        self.rankings = rankings
        self.targetting_group = targetting_group

    def find_target(self, targetting_groups: Dict[TargetingGroup, Set[int]]) -> Optional[int]:
        """Find the target for the given entity."""
        self.target = None
        best_target = None
        best_scores = None
        
        for entity in targetting_groups[self.targetting_group]:
            if self.unit_condition is not None and not self.unit_condition.check(entity):
                continue

            # Calculate scores for this entity
            current_scores = tuple(ranking.key(entity) for ranking in self.rankings)
            
            # If this is the first valid target or it's better than the current best
            if best_scores is None or current_scores < best_scores:
                best_target = entity
                best_scores = current_scores
        
        self.target = best_target
        return self.target

    @property
    def target(self) -> Optional[int]:
        """Get the target for the given entity."""
        return self._target

    @target.setter
    def target(self, target: Optional[int]):
        self._target = target
