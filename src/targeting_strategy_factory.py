"""Factory for creating targeting strategies based on type."""

import esper
from typing import Optional
from components.team import Team, TeamType
from components.destination import Destination
from components.ability import Abilities
from target_strategy import TargetStrategy, ByDistance, ByCurrentHealth, WeightedRanking, TargetingGroup
from targeting_strategy_types import TargetingStrategyType


def create_targeting_strategy(
    strategy_type: TargetingStrategyType,
    entity: int,
    team: TeamType,
    y_bias: Optional[float] = None
) -> TargetStrategy:
    """Create a targeting strategy of the specified type for the given entity."""
    
    if strategy_type == TargetingStrategyType.FOLLOWER:
        # Follower units follow nearby friendly non-follower units
        return TargetStrategy(
            rankings=[
                ByDistance(entity=entity, y_bias=y_bias or 2, ascending=True),
            ],
            unit_condition=None,
            targetting_group=TargetingGroup.TEAM1_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM2_LIVING_VISIBLE
        )
    
    elif strategy_type == TargetingStrategyType.DEFAULT:
        # Default: nearest enemy
        return TargetStrategy(
            rankings=[
                ByDistance(entity=entity, y_bias=y_bias or 2, ascending=True),
            ],
            unit_condition=None,
            targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
        )
    
    elif strategy_type == TargetingStrategyType.HUNTER:
        # Hunter: prioritizes low health enemies
        return TargetStrategy(
            rankings=[
                WeightedRanking(
                    rankings={
                        ByDistance(entity=entity, y_bias=y_bias, ascending=True): 1,
                        ByCurrentHealth(ascending=False): -0.6,  # Negative weight = prefer low health
                    },
                ),
            ],
            unit_condition=None,
            targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
        )
    
    elif strategy_type == TargetingStrategyType.CORPSES:
        # Corpses: targets usable corpses
        return TargetStrategy(
            rankings=[
                ByDistance(entity=entity, y_bias=y_bias or 2, ascending=True),
            ],
            unit_condition=None,
            targetting_group=TargetingGroup.USABLE_CORPSES
        )
    
    else:
        raise ValueError(f"Unknown targeting strategy type: {strategy_type}")


def get_targeting_strategy_type(strategy: TargetStrategy) -> TargetingStrategyType:
    """Determine the type of a targeting strategy by analyzing its rankings."""
    
    # Check if it's a follower (targets own team)
    if strategy.targetting_group in [TargetingGroup.TEAM1_LIVING_VISIBLE, TargetingGroup.TEAM2_LIVING_VISIBLE]:
        # Check if it has the hunter pattern (WeightedRanking with ByCurrentHealth)
        if len(strategy.rankings) == 1 and isinstance(strategy.rankings[0], WeightedRanking):
            weighted_ranking = strategy.rankings[0]
            if ByCurrentHealth in [type(r) for r in weighted_ranking.rankings.keys()]:
                return TargetingStrategyType.HUNTER
        
        # Check if it's a follower (targets own team)
        # This is a bit tricky - we'd need to know the entity's team to determine this
        # For now, we'll assume it's DEFAULT if it targets enemy team
        return TargetingStrategyType.DEFAULT
    
    elif strategy.targetting_group == TargetingGroup.USABLE_CORPSES:
        return TargetingStrategyType.CORPSES
    
    else:
        return TargetingStrategyType.DEFAULT


def replace_targeting_strategies(
    entity: int,
    from_type: TargetingStrategyType,
    to_type: TargetingStrategyType,
    y_bias: Optional[float] = None
) -> None:
    """Replace all targeting strategies of the given type on an entity with a new type."""
    
    team = esper.component_for_entity(entity, Team).type
    new_strategy = create_targeting_strategy(to_type, entity, team, y_bias)
    
    # Replace destination targeting strategy
    if esper.has_component(entity, Destination):
        destination = esper.component_for_entity(entity, Destination)
        if get_targeting_strategy_type(destination.target_strategy) == from_type:
            destination.target_strategy = new_strategy
    
    # Replace all ability targeting strategies
    if esper.has_component(entity, Abilities):
        abilities = esper.component_for_entity(entity, Abilities)
        for ability in abilities.abilities:
            if get_targeting_strategy_type(ability.target_strategy) == from_type:
                ability.target_strategy = new_strategy
