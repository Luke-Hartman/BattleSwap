"""Event definitions for Battle Swap.

This module contains the event classes used for communication between different parts of the game.
"""

from dataclasses import dataclass
from typing import Tuple
from components.unit_state import State
from pydispatch import dispatcher

@dataclass
class AbilityActivatedEvent:
    """Event triggered when a unit's ability is activated."""
    entity: int
    index: int
    frame: int

@dataclass
class AbilityInterruptedEvent:
    """Event triggered when a unit's ability is interrupted."""
    entity: int
    index: int

@dataclass
class AbilityCompletedEvent:
    """Event triggered when a unit's ability is completed."""
    entity: int
    index: int

@dataclass
class AbilityTriggeredEvent:
    """Event triggered when a unit's ability is triggered."""
    entity: int
    index: int

@dataclass
class AoEHitEvent:
    """Event triggered when an AoE hits a unit.
    
    Note that this doesn't mean the AoE will actually affect the unit.
    """
    entity: int
    target: int

@dataclass
class AuraHitEvent:
    """Event triggered when an aura hits a unit.
    
    Note that this doesn't mean the aura will actually affect the unit.
    """
    entity: int
    target: int

@dataclass
class DestinationTargetAcquiredEvent:
    """Event triggered when a unit identifies a destination."""
    entity: int
    destination: Tuple[float, float]

@dataclass
class DestinationTargetLostEvent:
    """Event triggered when a unit loses its destination."""
    entity: int

@dataclass
class FleeingStartedEvent:
    """Event triggered when a unit starts fleeing."""
    entity: int

@dataclass
class FleeingExpiredEvent:
    """Event triggered when a fleeing unit's fleeing effect expires."""
    entity: int

@dataclass
class DeathEvent:
    """Event triggered when a unit dies."""
    entity: int

@dataclass
class ProjectileHitEvent:
    """Event triggered when a projectile hits a target."""
    entity: int
    target: int

@dataclass
class StateChangedEvent:
    """Event triggered when a unit's state changes."""
    entity: int
    new_state: State

# Define signal names for each event
ABILITY_ACTIVATED = 'ability_activated'
ABILITY_COMPLETED = 'ability_completed'
ABILITY_INTERRUPTED = 'ability_interrupted'
ABILITY_TRIGGERED = 'ability_triggered'
AOE_HIT = 'aoe_hit'
AURA_HIT = 'aura_hit'
DEATH = 'death'
DESTINATION_TARGET_ACQUIRED = 'destination_target_acquired'
DESTINATION_TARGET_LOST = 'destination_target_lost'
FLEEING_STARTED = 'fleeing_started'
FLEEING_EXPIRED = 'fleeing_expired'
PROJECTILE_HIT = 'projectile_hit'
STATE_CHANGED = 'state_changed'

def emit_event(event_type, **kwargs):
    """Emit an event using pydispatch."""
    dispatcher.send(signal=event_type, sender=dispatcher.Any, **kwargs)
