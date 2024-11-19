"""Status effect component."""

from dataclasses import dataclass
from typing import List
import copy

from game_constants import gc

@dataclass
class StatusEffect:
    """A status effect."""

    time_remaining: float
    """The time remaining for the status effect."""

@dataclass
class CrusaderCommanderEmpowered(StatusEffect):
    """Status effect buffs damage."""

    damage_percentage = gc.CRUSADER_COMMANDER_EMPOWERED_DAMAGE_PERCENTAGE

@dataclass
class Ignited(StatusEffect):
    """Status effect that deals damage over time."""

    dps: float
    """The damage per second dealt by the status effect."""

@dataclass
class Fleeing(StatusEffect):
    """Status effect that makes a unit flee from a specific entity."""

    entity: int
    """The entity to flee from."""


class StatusEffects:
    """Component that stores the status effects of a unit."""
    # TODO: This not really a following ECS best practice

    def __init__(self):
        self._status_by_type = {
            Ignited: [],
            CrusaderCommanderEmpowered: [],
            Fleeing: [],
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
        if self._status_by_type[Ignited]:
            strongest_ignited = max(self._status_by_type[Ignited], key=lambda e: e.dps)
            active_effects.append(strongest_ignited)
        if self._status_by_type[CrusaderCommanderEmpowered]:
            active_effects.append(self._status_by_type[CrusaderCommanderEmpowered][0])
        if self._status_by_type[Fleeing]:
            longest_fleeing = max(self._status_by_type[Fleeing], key=lambda e: e.time_remaining)
            active_effects.append(longest_fleeing)
        return active_effects


