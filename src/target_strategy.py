"""Targetting strategy logic for Battle Swap."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

import esper

from components.health import Health
from components.position import Position
from components.team import TeamType
from unit_condition import UnitCondition, All, OnTeam, Alive, Grounded
from unit_sets import UnitSetType, unit_set_manager

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
        rankings: List[Ranking],
        unit_set_type: Optional[UnitSetType] = None
    ):
        self._target = None
        self.unit_condition = unit_condition
        self.rankings = rankings
        self.unit_set_type = unit_set_type

    def find_target(self) -> Optional[int]:
        """Find the target for the given entity."""
        self.target = None
        best_target = None
        best_scores = None
        
        # Use pre-filtered unit set if specified, otherwise use all positioned entities
        if self.unit_set_type is not None:
            # Request the unit set to be computed
            unit_set_manager.request_unit_set(self.unit_set_type)
            # We'll get the actual set in the processor after compute_sets() is called
            entities_to_check = unit_set_manager.get_unit_set(self.unit_set_type)
        else:
            # Fallback to original behavior
            entities_to_check = [entity for entity, (_,) in esper.get_components(Position)]
        
        for other_entity in entities_to_check:
            if not self.unit_condition.check(other_entity):
                continue

            # Calculate scores for this entity
            current_scores = tuple(ranking.key(other_entity) for ranking in self.rankings)
            
            # If this is the first valid target or it's better than the current best
            if best_scores is None or current_scores < best_scores:
                best_target = other_entity
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


def create_enemy_targeting_strategy(
    team: TeamType,
    rankings: List[Ranking],
    grounded_only: bool = False,
    additional_conditions: Optional[List[UnitCondition]] = None
) -> TargetStrategy:
    """Create a targeting strategy for enemy units with optimized unit sets.
    
    Args:
        team: The team of the entity doing the targeting (enemies will be the other team)
        rankings: The ranking criteria for target selection
        grounded_only: Whether to target only grounded units
        additional_conditions: Additional unit conditions to apply beyond team/alive/grounded
    
    Returns:
        A TargetStrategy configured with the appropriate unit set
    """
    enemy_team = team.other()
    
    # Choose the appropriate pre-filtered unit set
    if grounded_only:
        if enemy_team == TeamType.TEAM1:
            unit_set_type = UnitSetType.TEAM1_LIVING_GROUNDED
        else:
            unit_set_type = UnitSetType.TEAM2_LIVING_GROUNDED
        base_conditions = [OnTeam(team=enemy_team), Alive(), Grounded()]
    else:
        if enemy_team == TeamType.TEAM1:
            unit_set_type = UnitSetType.TEAM1_LIVING
        else:
            unit_set_type = UnitSetType.TEAM2_LIVING
        base_conditions = [OnTeam(team=enemy_team), Alive()]
    
    # Add any additional conditions
    if additional_conditions:
        all_conditions = base_conditions + additional_conditions
    else:
        all_conditions = base_conditions
    
    return TargetStrategy(
        unit_condition=All(all_conditions),
        rankings=rankings,
        unit_set_type=unit_set_type
    )


def create_friendly_targeting_strategy(
    team: TeamType,
    rankings: List[Ranking],
    grounded_only: bool = False,
    additional_conditions: Optional[List[UnitCondition]] = None
) -> TargetStrategy:
    """Create a targeting strategy for friendly units with optimized unit sets.
    
    Args:
        team: The team to target
        rankings: The ranking criteria for target selection
        grounded_only: Whether to target only grounded units
        additional_conditions: Additional unit conditions to apply beyond team/alive/grounded
    
    Returns:
        A TargetStrategy configured with the appropriate unit set
    """
    # Choose the appropriate pre-filtered unit set
    if grounded_only:
        if team == TeamType.TEAM1:
            unit_set_type = UnitSetType.TEAM1_LIVING_GROUNDED
        else:
            unit_set_type = UnitSetType.TEAM2_LIVING_GROUNDED
        base_conditions = [OnTeam(team=team), Alive(), Grounded()]
    else:
        if team == TeamType.TEAM1:
            unit_set_type = UnitSetType.TEAM1_LIVING
        else:
            unit_set_type = UnitSetType.TEAM2_LIVING
        base_conditions = [OnTeam(team=team), Alive()]
    
    # Add any additional conditions
    if additional_conditions:
        all_conditions = base_conditions + additional_conditions
    else:
        all_conditions = base_conditions
    
    return TargetStrategy(
        unit_condition=All(all_conditions),
        rankings=rankings,
        unit_set_type=unit_set_type
    )


def create_any_living_targeting_strategy(
    rankings: List[Ranking],
    grounded_only: bool = False,
    additional_conditions: Optional[List[UnitCondition]] = None
) -> TargetStrategy:
    """Create a targeting strategy for any living units with optimized unit sets.
    
    Args:
        rankings: The ranking criteria for target selection
        grounded_only: Whether to target only grounded units
        additional_conditions: Additional unit conditions to apply beyond alive/grounded
    
    Returns:
        A TargetStrategy configured with the appropriate unit set
    """
    # Choose the appropriate pre-filtered unit set
    if grounded_only:
        unit_set_type = UnitSetType.ALL_LIVING_GROUNDED
        base_conditions = [Alive(), Grounded()]
    else:
        unit_set_type = UnitSetType.ALL_LIVING
        base_conditions = [Alive()]
    
    # Add any additional conditions
    if additional_conditions:
        all_conditions = base_conditions + additional_conditions
    else:
        all_conditions = base_conditions
    
    return TargetStrategy(
        unit_condition=All(all_conditions),
        rankings=rankings,
        unit_set_type=unit_set_type
    )
