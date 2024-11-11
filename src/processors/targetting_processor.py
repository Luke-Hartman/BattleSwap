"""Processor responsible for targetting."""


import esper
from components.ability import Abilities
from components.destination import Destination
from components.unit_state import State, UnitState
from targetting_strategy import TargetStrategy


class TargettingProcessor(esper.Processor):
    """Processor responsible for targetting."""

    def process(self, dt: float):
        for ent, (unit_state, destination) in esper.get_components(UnitState, Destination):
            self._update_target(ent, unit_state, destination.target_strategy)
        for ent, (unit_state, abilities) in esper.get_components(UnitState, Abilities):
            for ability in abilities.abilities:
                self._update_target(ent, unit_state, ability.target_strategy)

    def _update_target(self, ent: int, unit_state: UnitState, target_strategy: TargetStrategy):
        """Update the target for the given entity."""
        # Clear target if it is dead
        target = target_strategy.target
        if target is not None and esper.component_for_entity(target, UnitState).state == State.DEAD:
            target_strategy.target = None
        # Consider new targets
        if unit_state.state in [State.IDLE, State.PURSUING]:
            target_strategy.find_target(ent)
        elif unit_state.state == State.DEAD:
            target_strategy.target = None
        # Otherwise, keep the current target
