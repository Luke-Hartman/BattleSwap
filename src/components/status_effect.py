"""Status effect component."""

from dataclasses import dataclass
from typing import List
import copy

from components.team import TeamType
from game_constants import gc

@dataclass
class StatusEffect:
    """A status effect."""

    time_remaining: float
    """The time remaining for the status effect."""

@dataclass
class CrusaderBannerBearerEmpowered(StatusEffect):
    """Status effect buffs damage."""

    damage_percentage = gc.CRUSADER_BANNER_BEARER_AURA_DAMAGE_PERCENTAGE

@dataclass
class CrusaderBannerBearerMovementSpeedBuff(StatusEffect):
    """Status effect that sets movement speed."""

    movement_speed = gc.CRUSADER_BANNER_BEARER_AURA_MOVEMENT_SPEED

@dataclass
class DamageOverTime(StatusEffect):
    """Status effect that deals damage over time."""

    dps: float
    """The damage per second dealt by the status effect."""

@dataclass
class Fleeing(StatusEffect):
    """Status effect that makes a unit flee from a specific entity."""

    entity: int
    """The entity to flee from."""

@dataclass
class Healing(StatusEffect):
    """Status effect that heals a unit."""

    dps: float
    """The amount of healing to apply per second."""

@dataclass
class ZombieInfection(StatusEffect):
    """Status effect that causes a unit to revive as a zombie."""
    
    team: TeamType
    """The team to revive as."""

@dataclass
class Grabbed(StatusEffect):
    """Status effect that makes a unit move towards a grabbing entity."""

    entity: int
    """The entity that is grabbing this unit."""
    grab_speed: float
    """The speed at which the unit moves towards the grabber."""

class StatusEffects:
    """Component that stores the status effects of a unit."""
    # TODO: This not really a following ECS best practice

    def __init__(self):
        self._status_by_type = {
            DamageOverTime: [],
            CrusaderBannerBearerEmpowered: [],
            CrusaderBannerBearerMovementSpeedBuff: [],
            Fleeing: [],
            Healing: [],
            ZombieInfection: [],
        }

    def add(self, status_effect: StatusEffect) -> None:
        """Add a status effect to the unit."""
        self._status_by_type[type(status_effect)].append(copy.copy(status_effect))
    
    def update(self, dt: float) -> None:
        """Update the status effects."""
        status_by_type = {}
        for status_type, status_effects in self._status_by_type.items():
            new_status_effects = []
            for status_effect in status_effects:
                status_effect.time_remaining -= dt
                if status_effect.time_remaining > 0:
                    new_status_effects.append(status_effect)
            status_by_type[status_type] = new_status_effects
        self._status_by_type = status_by_type

    def active_effects(self) -> List[StatusEffect]:
        """Get the active status effects."""
        active_effects = []
        if self._status_by_type[DamageOverTime]:
            strongest_ignited = max(self._status_by_type[DamageOverTime], key=lambda e: e.dps)
            active_effects.append(strongest_ignited)
        if self._status_by_type[CrusaderBannerBearerEmpowered]:
            active_effects.append(self._status_by_type[CrusaderBannerBearerEmpowered][0])
        if self._status_by_type[CrusaderBannerBearerMovementSpeedBuff]:
            active_effects.append(self._status_by_type[CrusaderBannerBearerMovementSpeedBuff][0])
        if self._status_by_type[Fleeing]:
            longest_fleeing = max(self._status_by_type[Fleeing], key=lambda e: e.time_remaining)
            active_effects.append(longest_fleeing)
        if self._status_by_type[ZombieInfection]:
            most_recent_zombie_infection = max(self._status_by_type[ZombieInfection], key=lambda e: e.time_remaining)
            active_effects.append(most_recent_zombie_infection)
        active_effects.extend(self._status_by_type[Healing])
        return active_effects


