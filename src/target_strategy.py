"""Targetting strategy logic for Battle Swap."""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple

import esper

from CONSTANTS import TARGETTING_SWITCH_BIAS
from components.health import Health
from components.position import Position
from components.team import Team
from unit_condition import Alive, UnitCondition

class Ranking(ABC):

    def __init__(self, ascending: bool):
        self.ascending = ascending

    def key(self, ent: int) -> float:
        if self.ascending:
            return self._key(ent)
        return -self._key(ent)

    @abstractmethod
    def _key(self, ent: int) -> float:
        ...

class ByDistance(Ranking):

    def __init__(self, entity: int, y_bias: Optional[float], ascending: bool):
        self.entity = entity
        self.y_bias = y_bias
        super().__init__(ascending)

    def _key(self, ent: int) -> float:
        e_pos = esper.component_for_entity(self.entity, Position)
        a_pos = esper.component_for_entity(ent, Position)
        return e_pos.distance(a_pos, self.y_bias)

class ByMissingHealth(Ranking):

    def _key(self, ent: int) -> float:
        health = esper.component_for_entity(ent, Health)
        return (health.maximum - health.current)

class ByMaxHealth(Ranking):

    def _key(self, ent: int) -> float:
        health = esper.component_for_entity(ent, Health)
        return health.maximum


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
