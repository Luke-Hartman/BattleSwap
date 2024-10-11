"""Combat component for the Battle Swap game."""

from dataclasses import dataclass

@dataclass
class Combat:
    """Represents the combat attributes of an entity."""

    attack_damage: int
    """The amount of damage the entity deals with each attack."""

    attack_range: float
    """The maximum distance at which the entity can attack."""

    attack_cooldown: int
    """The number of frames between attacks."""

    current_cooldown: int = 0
    """The current cooldown timer for attacks."""