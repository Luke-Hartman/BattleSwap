"""Processor responsible for abilities."""

import time
import esper

from components.ability import Abilities, Ability, Condition, Cooldown, HasTarget, SatisfiesUnitCondition
from components.unit_state import State, UnitState
from events import ABILITY_INTERRUPTED, ABILITY_TRIGGERED, AbilityInterruptedEvent, AbilityTriggeredEvent, emit_event

class AbilityProcessor(esper.Processor):
    """Processor responsible for abilities."""

    def process(self, dt: float):
        for ent, (unit_state, abilities) in esper.get_components(UnitState, Abilities):
            if unit_state.state in [State.IDLE, State.PURSUING]:
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
        if not condition.unit_condition.check(ability.target):
            return False
    elif isinstance(condition, SatisfiesUnitCondition):
        if not condition.unit_condition.check(entity):
            return False
    return True

