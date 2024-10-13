"""State machine module for Battle Swap.

This module contains the StateMachine class, which is responsible for
managing the states of units based on events.
"""

import esper
from components.unit_state import UnitState, State
from events import (
    TargetAcquiredEvent, TargetInRangeEvent, AttackCompletedEvent, StateChangedEvent,
    TARGET_ACQUIRED, TARGET_IN_RANGE, ATTACK_COMPLETED, STATE_CHANGED,
    emit_event
)
from pydispatch import dispatcher

class StateMachine:
    """Manages unit states based on events."""

    def __init__(self):
        dispatcher.connect(self.handle_target_acquired, signal=TARGET_ACQUIRED)
        dispatcher.connect(self.handle_target_in_range, signal=TARGET_IN_RANGE)
        dispatcher.connect(self.handle_attack_completed, signal=ATTACK_COMPLETED)

    def handle_target_acquired(self, event: TargetAcquiredEvent):
        unit_state = esper.component_for_entity(event.entity, UnitState)
        unit_state.state = State.PURSUING
        unit_state.target = event.target
        emit_event(STATE_CHANGED, event=StateChangedEvent(event.entity, State.PURSUING))

    def handle_target_in_range(self, event: TargetInRangeEvent):
        unit_state = esper.component_for_entity(event.entity, UnitState)
        unit_state.state = State.ATTACKING
        emit_event(STATE_CHANGED, event=StateChangedEvent(event.entity, State.ATTACKING))

    def handle_attack_completed(self, event: AttackCompletedEvent):
        unit_state = esper.component_for_entity(event.entity, UnitState)
        unit_state.state = State.IDLE
        unit_state.target = None
        emit_event(STATE_CHANGED, event=StateChangedEvent(event.entity, State.IDLE))
