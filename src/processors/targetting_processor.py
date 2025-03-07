"""Processor responsible for targetting."""


import esper
from components.ability import Abilities
from components.destination import Destination
from components.instant_ability import InstantAbilities
from components.unit_state import State, UnitState
from target_strategy import TargetStrategy


class TargettingProcessor(esper.Processor):
    """Processor responsible for targetting."""

    def process(self, dt: float):
        for ent, (unit_state, destination) in esper.get_components(UnitState, Destination):
            self._update_target(ent, unit_state, destination.target_strategy)
        for ent, (unit_state, instant_abilities) in esper.get_components(UnitState, InstantAbilities):
            for ability in instant_abilities.abilities:
                self._update_target(ent, unit_state, ability.target_strategy)
        for ent, (unit_state, abilities) in esper.get_components(UnitState, Abilities):
            for ability in abilities.abilities:
                self._update_target(ent, unit_state, ability.target_strategy)

    def _update_target(self, ent: int, unit_state: UnitState, target_strategy: TargetStrategy):
        """Update the target for the given entity."""
        # Consider new targets
        if unit_state.state == State.IDLE or unit_state.state == State.PURSUING:
            target_strategy.find_target()
        elif unit_state.state == State.DEAD:
            target_strategy.target = None
