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
class AuraHitEvent:
    """Event triggered when an aura hits a unit.
    
    Note that this doesn't mean the aura will actually affect the unit.
    """
    entity: int
    target: int

@dataclass
class ChangeMusicEvent:
    """Event triggered to change the music."""
    filename: str
    """The name of the music file to play."""

@dataclass
class ChangeMusicVolumeEvent:
    """Event triggered to change the music volume."""
    volume: float
    """The new volume to set."""

@dataclass
class CircleAoEHitEvent:
    """Event triggered when a CircleAoE hits a unit.
    
    Note that this doesn't mean the AoE will actually affect the unit.
    """
    entity: int
    target: int

@dataclass
class DeathEvent:
    """Event triggered when a unit dies."""
    entity: int

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
class InstantAbilityTriggeredEvent:
    """Event triggered when a unit's instant ability is triggered."""
    entity: int
    index: int

@dataclass
class LobbedArrivedEvent:
    """Event triggered when a lobbed entity arrives at its target."""
    entity: int

@dataclass
class PlaySoundEvent:
    """Event triggered to play a sound."""
    filename: str
    volume: float
    channel: str = None
    """Optional channel to play the sound on. If None, plays on a standard channel."""

@dataclass
class PlayVoiceEvent:
    """Event triggered to play a voice line."""
    filename: str
    force: bool
    """Whether to force the voice to play even if another voice is already playing."""

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

@dataclass
class StopAllSoundsEvent:
    """Event triggered to stop all sounds."""

@dataclass
class VisualAoEHitEvent:
    """Event triggered when a VisualAoE hits a unit.
    
    Note that this doesn't mean the AoE will actually affect the unit.
    """
    entity: int
    target: int

@dataclass
class GrabStartedEvent:
    """Event triggered when a unit starts being grabbed."""
    entity: int
    """The entity being grabbed."""

@dataclass
class GrabEndedEvent:
    """Event triggered when a unit stops being grabbed."""
    entity: int
    """The entity that was grabbed."""

@dataclass
class MuteDrumsEvent:
    """Event triggered to mute drums."""
    pass

@dataclass
class UnmuteDrumsEvent:
    """Event triggered to unmute drums."""
    pass

# Define signal names for each event
ABILITY_ACTIVATED = 'ability_activated'
ABILITY_COMPLETED = 'ability_completed'
ABILITY_INTERRUPTED = 'ability_interrupted'
ABILITY_TRIGGERED = 'ability_triggered'
AURA_HIT = 'aura_hit'
CHANGE_MUSIC = 'change_music'
CHANGE_MUSIC_VOLUME = 'change_music_volume'
CIRCLE_AOE_HIT = 'circle_aoe_hit'
DEATH = 'death'
DESTINATION_TARGET_ACQUIRED = 'destination_target_acquired'
DESTINATION_TARGET_LOST = 'destination_target_lost'
FLEEING_STARTED = 'fleeing_started'
FLEEING_EXPIRED = 'fleeing_expired'
GRAB_STARTED = 'grab_started'
GRAB_ENDED = 'grab_ended'
INSTANT_ABILITY_TRIGGERED = 'instant_ability_triggered'
LOBBED_ARRIVED = 'lobbed_arrived'
PLAY_SOUND = 'play_sound'
PLAY_VOICE = 'play_voice'
PROJECTILE_HIT = 'projectile_hit'
STATE_CHANGED = 'state_changed'
STOP_ALL_SOUNDS = 'stop_all_sounds'
VISUAL_AOE_HIT = 'visual_aoe_hit'
MUTE_DRUMS = 'mute_drums'
UNMUTE_DRUMS = 'unmute_drums'

def emit_event(event_type, **kwargs):
    """Emit an event using pydispatch."""
    dispatcher.send(signal=event_type, sender=dispatcher.Any, **kwargs)
