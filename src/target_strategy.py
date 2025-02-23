"""Targetting strategy logic for Battle Swap."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

import esper

from components.health import Health
from components.position import Position
from unit_condition import UnitCondition

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
        unit_condition: UnitCondition,
        rankings: List[Ranking]
    ):
        self._target = None
        self.unit_condition = unit_condition
        self.rankings = rankings

    def find_target(self) -> Optional[int]:
        """Find the target for the given entity."""
        self.target = None
        eligible_targets: List[Tuple[int, Tuple[float, ...]]] = []
        for other_entity, (_,) in esper.get_components(Position):
            if not self.unit_condition.check(other_entity):
                continue
            eligible_targets.append((other_entity, tuple(ranking.key(other_entity) for ranking in self.rankings)))
        eligible_targets.sort(key=lambda x: x[1])
        if eligible_targets:
            self.target = eligible_targets[0][0]
        return self.target

    @property
    def target(self) -> Optional[int]:
        """Get the target for the given entity."""
        return self._target

    @target.setter
    def target(self, target: Optional[int]):
        self._target = target
