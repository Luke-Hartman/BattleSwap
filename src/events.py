"""Event definitions for Battle Swap.

This module contains the event classes used for communication between different parts of the game.
"""

from dataclasses import dataclass
from components.skill import Skill
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

@dataclass
class KillingBlowEvent:
    """Event triggered when a unit's health reaches 0."""
    entity: int

@dataclass
class TargetLostEvent:
    """Event triggered when a unit loses its target."""
    entity: int

@dataclass
class ProjectileHitEvent:
    """Event triggered when a projectile hits a target."""
    entity: int
    target: int

@dataclass
class SkillTriggeredEvent:
    """Event triggered when a skill is triggered."""
    entity: int

@dataclass
class SkillActivatedEvent:
    """Event triggered when a skill is activated."""
    entity: int

@dataclass
class SkillCompletedEvent:
    """Event triggered when a skill is completed."""
    entity: int

@dataclass
class AoEHitEvent:
    """Event triggered when an AoE hits a unit.
    
    Note that this doesn't mean the AoE will actually affect the unit.
    """
    aoe: int
    target: int

# Define signal names for each event
TARGET_ACQUIRED = 'target_acquired'
TARGET_IN_RANGE = 'target_in_range'
ATTACK_ACTIVATED = 'attack_activated'
ATTACK_COMPLETED = 'attack_completed'
STATE_CHANGED = 'state_changed'
KILLING_BLOW = 'killing_blow'
TARGET_LOST = 'target_lost'
PROJECTILE_HIT = 'projectile_hit'
SKILL_TRIGGERED = 'skill_triggered'
SKILL_ACTIVATED = 'skill_activated'
SKILL_COMPLETED = 'skill_completed'
AOE_HIT = 'aoe_hit'

def emit_event(event_type, **kwargs):
    """Emit an event using pydispatch."""
    dispatcher.send(signal=event_type, sender=dispatcher.Any, **kwargs)
