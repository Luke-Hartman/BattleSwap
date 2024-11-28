"""State machine module for Battle Swap.

This module contains the StateMachine class, which is responsible for
managing the states of units based on events.
"""

import esper
from components.unit_state import UnitState, State
from events import (
    ABILITY_INTERRUPTED, AbilityInterruptedEvent, AbilityTriggeredEvent, ABILITY_TRIGGERED,
    AbilityCompletedEvent, ABILITY_COMPLETED,
    DestinationTargetAcquiredEvent, DESTINATION_TARGET_ACQUIRED,
    DestinationTargetLostEvent, DESTINATION_TARGET_LOST,
    FleeingStartedEvent, FLEEING_STARTED,
    FleeingExpiredEvent, FLEEING_EXPIRED,
    DeathEvent, DEATH,
    StateChangedEvent, STATE_CHANGED,
    emit_event
)
from pydispatch import dispatcher

class StateMachine:
    """Manages unit states based on events."""

    def __init__(self):
        dispatcher.connect(self.handle_ability_interrupted, signal=ABILITY_INTERRUPTED)
        dispatcher.connect(self.handle_ability_triggered, signal=ABILITY_TRIGGERED)
        dispatcher.connect(self.handle_ability_completed, signal=ABILITY_COMPLETED)
        dispatcher.connect(self.handle_death, signal=DEATH)
        dispatcher.connect(self.handle_destination_target_acquired, signal=DESTINATION_TARGET_ACQUIRED)
        dispatcher.connect(self.handle_destination_target_lost, signal=DESTINATION_TARGET_LOST)
        dispatcher.connect(self.handle_fleeing_started, signal=FLEEING_STARTED)
        dispatcher.connect(self.handle_fleeing_expired, signal=FLEEING_EXPIRED)
    def handle_ability_interrupted(self, event: AbilityInterruptedEvent):
        unit_state = esper.component_for_entity(event.entity, UnitState)
        unit_state.state = State.IDLE
        emit_event(STATE_CHANGED, event=StateChangedEvent(event.entity, State.IDLE))

    def handle_ability_triggered(self, event: AbilityTriggeredEvent):
        unit_state = esper.component_for_entity(event.entity, UnitState)
        if event.index == 0:
            unit_state.state = State.ABILITY1
        elif event.index == 1:
            unit_state.state = State.ABILITY2
        elif event.index == 2:
            unit_state.state = State.ABILITY3
        else:
            raise ValueError(f"Invalid ability index: {event.index}")
        emit_event(STATE_CHANGED, event=StateChangedEvent(event.entity, unit_state.state))

    def handle_ability_completed(self, event: AbilityCompletedEvent):
        unit_state = esper.component_for_entity(event.entity, UnitState)
        unit_state.state = State.IDLE
        emit_event(STATE_CHANGED, event=StateChangedEvent(event.entity, State.IDLE))

    def handle_destination_target_acquired(self, event: DestinationTargetAcquiredEvent):
        unit_state = esper.component_for_entity(event.entity, UnitState)
        unit_state.state = State.PURSUING
        emit_event(STATE_CHANGED, event=StateChangedEvent(event.entity, State.PURSUING))

    def handle_destination_target_lost(self, event: DestinationTargetLostEvent):
        unit_state = esper.component_for_entity(event.entity, UnitState)
        unit_state.state = State.IDLE
        emit_event(STATE_CHANGED, event=StateChangedEvent(event.entity, State.IDLE))

    def handle_fleeing_started(self, event: FleeingStartedEvent):
        unit_state = esper.component_for_entity(event.entity, UnitState)
        unit_state.state = State.FLEEING
        emit_event(STATE_CHANGED, event=StateChangedEvent(event.entity, State.FLEEING))

    def handle_fleeing_expired(self, event: FleeingExpiredEvent):
        unit_state = esper.component_for_entity(event.entity, UnitState)
        unit_state.state = State.IDLE
        emit_event(STATE_CHANGED, event=StateChangedEvent(event.entity, State.IDLE))

    def handle_death(self, event: DeathEvent):
        unit_state = esper.component_for_entity(event.entity, UnitState)
        unit_state.state = State.DEAD
        emit_event(STATE_CHANGED, event=StateChangedEvent(event.entity, State.DEAD))
