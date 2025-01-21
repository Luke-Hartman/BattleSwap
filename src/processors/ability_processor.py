"""Processor responsible for abilities."""

from typing import Optional, Union
import esper

from components.ability import Abilities, Ability, Condition, Cooldown, HasTarget, SatisfiesUnitCondition
from components.instant_ability import InstantAbilities, InstantAbility
from components.orientation import FacingDirection, Orientation
from components.position import Position
from components.unit_state import State, UnitState
from components.velocity import Velocity
from events import ABILITY_INTERRUPTED, ABILITY_TRIGGERED, AbilityInterruptedEvent, AbilityTriggeredEvent, emit_event, INSTANT_ABILITY_TRIGGERED, InstantAbilityTriggeredEvent

class AbilityProcessor(esper.Processor):
    """Processor responsible for abilities."""

    def process(self, dt: float):
        for ent, (unit_state, instant_abilities) in esper.get_components(UnitState, InstantAbilities):
            for i, ability in enumerate(instant_abilities.abilities):
                ability.time_since_last_use += dt
                if not all(check_condition(ent, condition, ability, ability.target_strategy.target) for condition in ability.trigger_conditions):
                    continue
                ability.time_since_last_use = 0
                emit_event(INSTANT_ABILITY_TRIGGERED, event=InstantAbilityTriggeredEvent(ent, i))
                break

        for ent, (unit_state, abilities) in esper.get_components(UnitState, Abilities):
            for ability in abilities.abilities:
                ability.time_since_last_use += dt
            if unit_state.state in [State.IDLE, State.PURSUING]:
                for i, ability in enumerate(abilities.abilities):
                    ability.target = ability.target_strategy.target
                    if not all(check_condition(ent, condition, ability, ability.target) for condition in ability.trigger_conditions):
                        continue
                    ability.time_since_last_use = 0
                    emit_event(ABILITY_TRIGGERED, event=AbilityTriggeredEvent(ent, i))
                    break
            if unit_state.state == State.ABILITY1:
                index = 0
            elif unit_state.state == State.ABILITY2:
                index = 1
            elif unit_state.state == State.ABILITY3:
                index = 2
            elif unit_state.state == State.ABILITY4:
                index = 3
            elif unit_state.state == State.ABILITY5:
                index = 4
            else:
                continue
            ability = abilities.abilities[index]
            if not all(check_condition(ent, condition, ability, ability.target) for condition in ability.persistent_conditions):
                emit_event(ABILITY_INTERRUPTED, event=AbilityInterruptedEvent(ent, index))
        for ent, (unit_state, velocity, pos, abilities, orientation) in esper.get_components(UnitState, Velocity, Position, Abilities, Orientation):
            if unit_state.state == State.ABILITY1:
                index = 0
            elif unit_state.state == State.ABILITY2:
                index = 1
            elif unit_state.state == State.ABILITY3:
                index = 2
            elif unit_state.state == State.ABILITY4:
                index = 3
            elif unit_state.state == State.ABILITY5:
                index = 4
            else:
                continue
            ability = abilities.abilities[index]
            velocity.x = 0
            velocity.y = 0
            if ability.target is not None:
                target_pos = esper.component_for_entity(ability.target, Position)
                dx = target_pos.x - pos.x
                orientation.facing = FacingDirection.LEFT if dx < 0 else FacingDirection.RIGHT
                

def check_condition(entity: int, condition: Condition, ability: Union[Ability, InstantAbility], target: Optional[int] = None) -> bool:
    """Check if the condition is met for the given ability."""
    if isinstance(condition, Cooldown):
        if ability.time_since_last_use < condition.duration:
            return False
    elif isinstance(condition, HasTarget):
        if target is None:
            return False
        if not condition.unit_condition.check(target):
            return False
    elif isinstance(condition, SatisfiesUnitCondition):
        if not condition.unit_condition.check(entity):
            return False
    else:
        raise ValueError(f"Unknown condition type: {type(condition)}, maybe missing SatisfiesUnitCondition?")
    return True

