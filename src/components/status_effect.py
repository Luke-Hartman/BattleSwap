"""Status effect component."""

import time
from typing import Dict, List

from CONSTANTS import CRUSADER_BLACK_KNIGHT_DEBUFFED_DAMAGE_PERCENTAGE, CRUSADER_COMMANDER_EMPOWERED_DAMAGE_PERCENTAGE

class StatusEffect:
    """A status effect."""

    def __init__(self, duration: float):
        self.duration = duration

class CrusaderCommanderEmpowered(StatusEffect):
    """Status effect buffs damage."""

    def __init__(self, duration: float):
        super().__init__(duration)
        self.damage_percentage = CRUSADER_COMMANDER_EMPOWERED_DAMAGE_PERCENTAGE

class CrusaderBlackKnightDebuffed(StatusEffect):
    """Status effect debuffs damage."""

    def __init__(self, duration: float):
        super().__init__(duration)
        self.damage_percentage = CRUSADER_BLACK_KNIGHT_DEBUFFED_DAMAGE_PERCENTAGE

class Ignited(StatusEffect):
    """Status effect that deals damage over time."""

    def __init__(self, dps: float, duration: float):
        super().__init__(duration)
        self.dps = dps


class StatusEffects:
    """Component that stores the status effects of a unit."""
    # TODO: This not really a following ECS best practice

    def __init__(self):
        self._status_by_type = {
            Ignited: [],
            CrusaderCommanderEmpowered: [],
            CrusaderBlackKnightDebuffed: [],
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
        if self._status_by_type[CrusaderBlackKnightDebuffed]:
            active_effects.append(self._status_by_type[CrusaderBlackKnightDebuffed][0])
        return active_effects


