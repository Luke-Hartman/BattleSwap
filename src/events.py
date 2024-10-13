"""Event definitions for Battle Swap.

This module contains the event classes used for communication between different parts of the game.
"""

from dataclasses import dataclass
from components.team import TeamType
from components.unit_state import State
from pydispatch import dispatcher

@dataclass
class TargetAcquiredEvent:
    """Event triggered when a unit identifies an enemy target."""
    entity: int
    target: int

@dataclass
class TargetInRangeEvent:
    """Event triggered when a unit gets within attack range of its target."""
    entity: int
    target: int

@dataclass
class AttackCompletedEvent:
    """Event triggered when a unit's attack animation is completed."""
    entity: int

@dataclass
class StateChangedEvent:
    """Event triggered when a unit's state changes."""
    entity: int
    new_state: State

@dataclass
class AttackActivatedEvent:
    """Event triggered when a unit's attack is activated (e.g., sword swing)."""
    entity: int

# Define signal names for each event
TARGET_ACQUIRED = 'target_acquired'
TARGET_IN_RANGE = 'target_in_range'
ATTACK_ACTIVATED = 'attack_activated'
ATTACK_COMPLETED = 'attack_completed'
STATE_CHANGED = 'state_changed'

def emit_event(event_type, **kwargs):
    """Emit an event using pydispatch."""
    dispatcher.send(signal=event_type, sender=dispatcher.Any, **kwargs)
