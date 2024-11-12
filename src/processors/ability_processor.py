"""Processor responsible for abilities."""

import math
import time
import esper

from components.ability import Abilities, Ability, Condition, Cooldown, HasTarget, SatisfiesUnitCondition
from components.position import Position
from components.unit_state import State, UnitState
from events import ABILITY_INTERRUPTED, ABILITY_TRIGGERED, AbilityInterruptedEvent, AbilityTriggeredEvent, emit_event

class AbilityProcessor(esper.Processor):
    """Processor responsible for abilities."""

    def process(self, dt: float):
        for ent, (unit_state, abilities) in esper.get_components(UnitState, Abilities):
            if unit_state.state == State.PURSUING:
                for i, ability in enumerate(abilities.abilities):
                    ability.target = ability.target_strategy.target
                    if not all(check_condition(ent, condition, ability) for condition in ability.trigger_conditions):
                        continue
                    ability.last_used = time.time()
                    emit_event(ABILITY_TRIGGERED, event=AbilityTriggeredEvent(ent, i))
                    break
            if unit_state.state == State.ABILITY1:
                index = 0
            elif unit_state.state == State.ABILITY2:
                index = 1
            elif unit_state.state == State.ABILITY3:
                index = 2
            else:
                continue
            ability = abilities.abilities[index]
            if not all(check_condition(ent, condition, ability) for condition in ability.persistent_conditions):
                emit_event(ABILITY_INTERRUPTED, event=AbilityInterruptedEvent(ent, index))

def check_condition(entity: int, condition: Condition, ability: Ability) -> bool:
    """Check if the condition is met for the given ability."""
    if isinstance(condition, Cooldown):
        if time.time() - ability.last_used < condition.duration:
            return False
    elif isinstance(condition, HasTarget):
        if ability.target is None:
            return False
        if condition.requires_living_target and not esper.component_for_entity(ability.target, UnitState).state != State.DEAD:
            return False
        if condition.maximum_distance is not None:
            pos = esper.component_for_entity(entity, Position)
            target_pos = esper.component_for_entity(ability.target, Position)
            if pos.distance(target_pos, condition.y_bias) >= condition.maximum_distance:
                return False
        if condition.maximum_angle is not None:
            pos = esper.component_for_entity(entity, Position)
            target_pos = esper.component_for_entity(ability.target, Position)
            angle = math.atan2(
                abs(target_pos.y - pos.y),
                abs(target_pos.x - pos.x)
            )
            if abs(angle) > condition.maximum_angle:
                return False
    elif isinstance(condition, SatisfiesUnitCondition):
        if not condition.unit_condition.check(entity):
            return False
    return True

