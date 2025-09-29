"""Status effect component."""

from dataclasses import dataclass
from typing import List, Optional
import copy

from components.team import TeamType
from components.unit_tier import UnitTier
from corruption_powers import CorruptionPower
from game_constants import gc

@dataclass
class StatusEffect:
    """A status effect."""

    time_remaining: float
    """The time remaining for the status effect."""
    
    owner: Optional[int]
    """The entity that applied this status effect."""

@dataclass
class InfantryBannerBearerEmpowered(StatusEffect):
    """Status effect buffs damage."""

    damage_percentage = gc.INFANTRY_BANNER_BEARER_AURA_DAMAGE_PERCENTAGE

@dataclass
class InfantryBannerBearerMovementSpeedBuff(StatusEffect):
    """Status effect that sets movement speed."""

    movement_speed = gc.INFANTRY_BANNER_BEARER_AURA_MOVEMENT_SPEED

@dataclass
class InfantryBannerBearerAbilitySpeedBuff(StatusEffect):
    """Status effect that increases ability speed."""

    ability_speed_increase_percent: float = 25.0

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

    corruption_powers: Optional[List[CorruptionPower]]
    """The corruption powers to apply to the zombie."""

@dataclass
class Grabbed(StatusEffect):
    """Status effect that makes a unit move towards a grabbing entity."""

    entity: int
    """The entity that is grabbing this unit."""
    grab_speed: float
    """The speed at which the unit moves towards the grabber."""

@dataclass
class Invisible(StatusEffect):
    """Status effect that makes a unit invisible and untargetable."""
    # No additional fields needed beyond the base time_remaining

@dataclass
class Immobilized(StatusEffect):
    """Status effect that immobilizes a unit, preventing movement."""
    # No additional fields needed beyond the base time_remaining

@dataclass
class WontPursue(StatusEffect):
    """Status effect that prevents a unit from pursuing.
    
    These units can be moved by forced movement, but won't transition to the pursuing state.

    More specifically, they won't react to a destination target in the idle processor.
    """
    # No additional fields needed beyond the base time_remaining

@dataclass
class ReviveProgress(StatusEffect):
    """Status effect that tracks progress towards reviving a dead unit."""
    
    stacks: int
    """The number of revive progress stacks."""
    
    team: TeamType
    """The team that applied this revive progress."""
    
    tier: UnitTier
    """The tier of the lich that applied this revive progress."""
    
    corruption_powers: Optional[List[CorruptionPower]]
    """The corruption powers of the lich that applied this revive progress."""

class StatusEffects:
    """Component that stores the status effects of a unit."""
    # TODO: This not really a following ECS best practice

    def __init__(self):
        self._status_by_type = {
            DamageOverTime: [],
            InfantryBannerBearerEmpowered: [],
            InfantryBannerBearerMovementSpeedBuff: [],
            InfantryBannerBearerAbilitySpeedBuff: [],
            Fleeing: [],
            Healing: [],
            ZombieInfection: [],
            Invisible: [],
            Immobilized: [],
            WontPursue: [],
            ReviveProgress: [],
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
        if self._status_by_type[InfantryBannerBearerEmpowered]:
            active_effects.append(self._status_by_type[InfantryBannerBearerEmpowered][0])
        if self._status_by_type[InfantryBannerBearerMovementSpeedBuff]:
            active_effects.append(self._status_by_type[InfantryBannerBearerMovementSpeedBuff][0])
        if self._status_by_type[InfantryBannerBearerAbilitySpeedBuff]:
            active_effects.append(self._status_by_type[InfantryBannerBearerAbilitySpeedBuff][0])
        if self._status_by_type[Fleeing]:
            longest_fleeing = max(self._status_by_type[Fleeing], key=lambda e: e.time_remaining)
            active_effects.append(longest_fleeing)
        if self._status_by_type[Invisible]:
            longest_invisible = max(self._status_by_type[Invisible], key=lambda e: e.time_remaining)
            active_effects.append(longest_invisible)
        if self._status_by_type[ZombieInfection]:
            most_recent_zombie_infection = max(self._status_by_type[ZombieInfection], key=lambda e: e.time_remaining)
            active_effects.append(most_recent_zombie_infection)
        if self._status_by_type[Immobilized]:
            longest_immobilized = max(self._status_by_type[Immobilized], key=lambda e: e.time_remaining)
            active_effects.append(longest_immobilized)
        if self._status_by_type[WontPursue]:
            longest_wont_pursue = max(self._status_by_type[WontPursue], key=lambda e: e.time_remaining)
            active_effects.append(longest_wont_pursue)
        active_effects.extend(self._status_by_type[Healing])
        active_effects.extend(self._status_by_type[ReviveProgress])
        return active_effects


