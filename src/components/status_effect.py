"""Status effect component."""

import time
from typing import Dict, List

from game_constants import gc

class StatusEffect:
    """A status effect."""

    def __init__(self, duration: float):
        self.duration = duration

class CrusaderCommanderEmpowered(StatusEffect):
    """Status effect buffs damage."""

    def __init__(self, duration: float):
        super().__init__(duration)
        self.damage_percentage = gc.CRUSADER_COMMANDER_EMPOWERED_DAMAGE_PERCENTAGE

class Ignited(StatusEffect):
    """Status effect that deals damage over time."""

    def __init__(self, dps: float, duration: float):
        super().__init__(duration)
        self.dps = dps

class Fleeing(StatusEffect):
    """Status effect that makes a unit flee from a specific entity."""

    def __init__(self, duration: float, entity: int):
        super().__init__(duration)
        self.entity = entity
        self.created_at = time.time()


class StatusEffects:
    """Component that stores the status effects of a unit."""
    # TODO: This not really a following ECS best practice

    def __init__(self):
        self._status_by_type = {
            Ignited: [],
            CrusaderCommanderEmpowered: [],
            Fleeing: [],
        }
        self.application_time: Dict[StatusEffect, float] = {}

    def add(self, status_effect: StatusEffect) -> None:
        """Add a status effect to the unit."""
        self._status_by_type[type(status_effect)].append(status_effect)
        self.application_time[status_effect] = time.time()

    def active_effects(self) -> List[StatusEffect]:
        """Get the active status effects."""
        for status_effect_type, status_effects in self._status_by_type.items():
            new_status_effects = []
            current_time = time.time()
            for status_effect in status_effects:
                if current_time - self.application_time[status_effect] < status_effect.duration:
                    new_status_effects.append(status_effect)
            self._status_by_type[status_effect_type] = new_status_effects
        active_effects = []
        if self._status_by_type[Ignited]:
            strongest_ignited = max(self._status_by_type[Ignited], key=lambda e: e.dps)
            active_effects.append(strongest_ignited)
        if self._status_by_type[CrusaderCommanderEmpowered]:
            active_effects.append(self._status_by_type[CrusaderCommanderEmpowered][0])
        if self._status_by_type[Fleeing]:
            newest_fleeing = max(self._status_by_type[Fleeing], key=lambda e: e.created_at)
            active_effects.append(newest_fleeing)
        return active_effects


