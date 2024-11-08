"""Compontent for area of effect abilities.

The primary difference between an AoE and an Aura, is than an AoE is an entity that
affects other entities which collide with it, while an Aura is a continuous effect
that affects entities in a radius of another entity.
"""

from typing import List, Optional
from dataclasses import dataclass, field

class AoEEffect:
    """AoE effect."""

    def __init__(self, affects_allies: bool, affects_enemies: bool):
        """Initialize the AoE effect."""
        self.affects_allies = affects_allies
        self.affects_enemies = affects_enemies

class DamageAoE(AoEEffect):
    """AoE effect that deals damage to entities."""

    def __init__(self, affects_allies: bool, affects_enemies: bool, damage: int):
        super().__init__(affects_allies, affects_enemies)
        self.damage = damage

@dataclass
class AoE:
    """The AoE component."""

    effect: AoEEffect
    owner: Optional[int]
    """Owner is used to apply buffs/debuffs to AoE effects."""
    affected_entities: List[int] = field(default_factory=list)
    """Used to prevent double hits."""
