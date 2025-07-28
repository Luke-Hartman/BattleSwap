"""Processor responsible for targetting."""


import esper
from components.ability import Abilities
from components.destination import Destination
from components.instant_ability import InstantAbilities
from components.unit_state import State, UnitState
from target_strategy import TargetingGroup


class TargettingProcessor(esper.Processor):
    """Processor responsible for targetting."""

    def process(self, dt: float):
        targetting_groups = defaultdict(set)

        for ent, (position, team) in esper.get_components(Position, Team):
            if team.team_type == TeamType.TEAM1:
                targetting_groups[TargetingGroup.TEAM1_LIVING].add(ent)
            else:
                targetting_groups[TargetingGroup.TEAM2_LIVING].add(ent)

        target_strategies = set()
        for ent, (unit_state, destination) in esper.get_components(UnitState, Destination):
            target_strategies.add((ent, unit_state.state, destination.target_strategy))
        for ent, (unit_state, instant_abilities) in esper.get_components(UnitState, InstantAbilities):
            for ability in instant_abilities.abilities:
                target_strategies.add((ent, unit_state.state, ability.target_strategy))
        for ent, (unit_state, abilities) in esper.get_components(UnitState, Abilities):
            for ability in abilities.abilities:
                target_strategies.add((ent, unit_state.state, ability.target_strategy))
        for ent, state, target_strategy in target_strategies:
            # Consider new targets
            if state == State.IDLE or state == State.PURSUING:
                target_strategy.find_target(targetting_groups)
            elif state == State.DEAD:
                target_strategy.target = None
