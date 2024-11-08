"""Components for aura effects."""

from typing import List, Tuple


class AuraEffect:
    """Aura effect."""

    def __init__(
        self,
        key: str,
        affects_self: bool,
        affects_allies: bool,
        affects_enemies: bool,
        priority: int = 0,
    ):
        """Constructor.
        
        Args:
            key: A unit can only have one aura effect of each key.
                This is used to control stacking auras.
            priority: The priority of the aura effect.
                Aura effects with higher priority will override aura effects
                with lower priority on the same key.
            affects_self: Whether the aura effect affects the unit itself.
            affects_allies: Whether the aura effect affects allies.
            affects_enemies: Whether the aura effect affects enemies.
        """
        self.key = key
        self.affects_self = affects_self
        self.affects_allies = affects_allies
        self.affects_enemies = affects_enemies
        self.priority = priority


class DamageBuffAura(AuraEffect):
    """Increases (or decreases) the damage of affected units by a percentage."""

    def __init__(
        self,
        key: str,
        damage_percentage: float,
        affects_self: bool = False,
        affects_allies: bool = False,
        affects_enemies: bool = False,
        priority: int = 0,
    ):
        self.damage_percentage = damage_percentage
        super().__init__(
            key=key,
            affects_self=affects_self,
            affects_allies=affects_allies,
            affects_enemies=affects_enemies,
            priority=priority,
        )

class Aura:
    """Aura component."""

    def __init__(self, radius: int, effect: AuraEffect, color: Tuple[int, int, int]):
        self.radius = radius
        self.effect = effect
        self.color = color

class AffectedByAuras:
    """Auras that are affecting a unit."""

    def __init__(self):
        self._effects = {}

    @property
    def effects(self) -> List[AuraEffect]:
        return list(self._effects.values())

    def add(self, effect: AuraEffect):
        if effect.key in self._effects:
            if self._effects[effect.key].priority > effect.priority:
                return
        self._effects[effect.key] = effect

    def clear(self):
        self._effects = {}

