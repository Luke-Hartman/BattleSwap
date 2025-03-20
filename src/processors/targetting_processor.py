"""Processor responsible for targetting."""


import esper
from components.ability import Abilities
from components.destination import Destination
from components.instant_ability import InstantAbilities
from components.unit_state import State, UnitState


class TargettingProcessor(esper.Processor):
    """Processor responsible for targetting."""

    def process(self, dt: float):
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
                target_strategy.find_target()
            elif state == State.DEAD:
                target_strategy.target = None
