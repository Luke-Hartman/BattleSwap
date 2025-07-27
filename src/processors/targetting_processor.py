"""Processor responsible for targetting."""


import esper
from components.ability import Abilities
from components.destination import Destination
from components.instant_ability import InstantAbilities
from components.unit_state import State, UnitState
from unit_sets import unit_set_manager


class TargettingProcessor(esper.Processor):
    """Processor responsible for targetting."""

    def process(self, dt: float):
        # Reset the unit set manager for this frame
        unit_set_manager.reset_frame()
        
        # Collect all target strategies and request their unit sets
        target_strategies = set()
        for ent, (unit_state, destination) in esper.get_components(UnitState, Destination):
            target_strategy = destination.target_strategy
            target_strategies.add((ent, unit_state.state, target_strategy))
            # Request unit set if the strategy uses one
            if target_strategy.unit_set_type is not None:
                unit_set_manager.request_unit_set(target_strategy.unit_set_type)
                
        for ent, (unit_state, instant_abilities) in esper.get_components(UnitState, InstantAbilities):
            for ability in instant_abilities.abilities:
                target_strategy = ability.target_strategy
                target_strategies.add((ent, unit_state.state, target_strategy))
                # Request unit set if the strategy uses one
                if target_strategy.unit_set_type is not None:
                    unit_set_manager.request_unit_set(target_strategy.unit_set_type)
                    
        for ent, (unit_state, abilities) in esper.get_components(UnitState, Abilities):
            for ability in abilities.abilities:
                target_strategy = ability.target_strategy
                target_strategies.add((ent, unit_state.state, target_strategy))
                # Request unit set if the strategy uses one
                if target_strategy.unit_set_type is not None:
                    unit_set_manager.request_unit_set(target_strategy.unit_set_type)
        
        # Compute all requested unit sets once
        unit_set_manager.compute_sets()
        
        # Now process all target strategies
        for ent, state, target_strategy in target_strategies:
            # Consider new targets
            if state == State.IDLE or state == State.PURSUING:
                target_strategy.find_target()
            elif state == State.DEAD:
                target_strategy.target = None
