"""Armor component."""

from dataclasses import dataclass
from enum import Enum

from game_constants import gc


class ArmorLevel(Enum):
    """Levels of armor protection."""
    NORMAL = "normal"
    HEAVILY = "heavily"


@dataclass
class Armor:
    """Represents the defensive properties of a unit's armor."""

    level: ArmorLevel
    """The level of armor protection."""

    @property
    def flat_reduction(self) -> int:
        """The flat reduction of the armor."""
        if self.level == ArmorLevel.NORMAL:
            return gc.ARMOR_FLAT_DAMAGE_REDUCTION
        elif self.level == ArmorLevel.HEAVILY:
            return gc.HEAVILY_ARMOR_FLAT_DAMAGE_REDUCTION
        else:
            raise ValueError(f"Unknown armor level: {self.level}")

    @property
    def percent_reduction(self) -> float:
        """The percent reduction of the armor."""
        if self.level == ArmorLevel.NORMAL:
            return gc.ARMOR_PERCENT_DAMAGE_REDUCTION
        elif self.level == ArmorLevel.HEAVILY:
            return gc.HEAVILY_ARMOR_PERCENT_DAMAGE_REDUCTION
        else:
            raise ValueError(f"Unknown armor level: {self.level}")

    def calculate_damage_after_armor(self, damage: int) -> int:
        """Calculate the damage after armor reduction."""
        max_reduction = gc.MAX_ARMOR_DAMAGE_REDUCTION if self.level == ArmorLevel.NORMAL else gc.MAX_HEAVILY_ARMOR_DAMAGE_REDUCTION
        return max(max(damage - self.flat_reduction, 0) * (1 - self.percent_reduction), damage * (1 - max_reduction))

