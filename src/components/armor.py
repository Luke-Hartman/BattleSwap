"""Armor component."""

from dataclasses import dataclass

from game_constants import gc

@dataclass
class Armor:
    """Represents the defensive properties of a unit's armor."""

    flat_reduction: int
    """The flat reduction of the armor."""

    percent_reduction: float
    """The percent reduction of the armor."""

    def calculate_damage_after_armor(self, damage: int) -> int:
        """Calculate the damage after armor reduction."""
        return max(max(damage - self.flat_reduction, 0) * (1 - self.percent_reduction), damage * (1 - gc.MAX_ARMOR_DAMAGE_REDUCTION))

    def __post_init__(self):
        if self.percent_reduction < 0 or self.percent_reduction > 1:
            raise ValueError("Percent reduction must be between 0 and 1")

