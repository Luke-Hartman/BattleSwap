"""Module for handling items in the game."""

from enum import Enum
from abc import ABC, abstractmethod
from typing import Dict
import esper
import pygame
import os
from components.health import Health
from components.dying import OnDeathEffect
from components.armor import Armor, ArmorLevel
from unit_condition import All, Alive, Grounded, Always, NotHeavilyArmored
from effects import CreatesCircleAoE, CreatesVisual, Damages, PlaySound, Recipient, SoundEffect, Effect
from visuals import Visual
from game_constants import gc
from unit_condition import UnitCondition


class ExplodeOnDeathExplosionEffect(Effect):
    """Custom effect for ExplodeOnDeath explosion that can be identified and removed."""
    
    def __init__(self):
        self.effects = [
            CreatesCircleAoE(
                effects=[
                    Damages(damage=gc.ITEM_EXPLODE_ON_DEATH_DAMAGE, recipient=Recipient.TARGET),
                ],
                radius=9 * gc.ITEM_EXPLODE_ON_DEATH_AOE_SCALE,  # Smaller than wizard fireball (9*3.0 = 27 vs 9*5.0 = 45)
                unit_condition=All([Alive(), Grounded()]),  # Hits both allies and enemies
                location=Recipient.PARENT,
            ),
            CreatesVisual(
                recipient=Recipient.PARENT,
                visual=Visual.Explosion,
                animation_duration=gc.CORE_WIZARD_FIREBALL_AOE_DURATION,  # Same duration as wizard fireball
                scale=gc.ITEM_EXPLODE_ON_DEATH_AOE_SCALE,
                duration=gc.CORE_WIZARD_FIREBALL_AOE_DURATION,
                layer=2,
            ),
            PlaySound(SoundEffect(filename="fireball_impact.wav", volume=0.50)),  # Same sound as wizard fireball
        ]
    
    def apply(self, owner: int, parent: int, target: int) -> None:
        """Apply all the explosion effects."""
        for effect in self.effects:
            effect.apply(owner, parent, target)


class ItemType(Enum):
    """Types of items that can be equipped to units."""
    EXTRA_HEALTH = "extra_health"
    EXPLODE_ON_DEATH = "EXPLODE_ON_DEATH"
    UPGRADE_ARMOR = "upgrade_armor"

class Item(ABC):
    """Base class for all items."""
    
    @abstractmethod
    def apply(self, entity: int) -> None:
        """Apply the item's effect to the given entity."""
        pass
    
    @abstractmethod
    def remove(self, entity: int) -> None:
        """Remove the item's effect from the given entity."""
        pass
    
    @classmethod
    @abstractmethod
    def get_unit_condition(cls) -> UnitCondition:
        """Return the unit condition that determines which units this item can be applied to."""
        pass

class ExtraHealth(Item):
    """Grants extra HP to the equipped unit."""

    def apply(self, entity: int) -> None:
        """Apply health bonus to the entity."""
        if esper.has_component(entity, Health):
            health = esper.component_for_entity(entity, Health)
            health.current += gc.ITEM_EXTRA_HEALTH_HEALTH_BONUS
            health.maximum += gc.ITEM_EXTRA_HEALTH_HEALTH_BONUS
    
    def remove(self, entity: int) -> None:
        """Remove health bonus from the entity."""
        if esper.has_component(entity, Health):
            health = esper.component_for_entity(entity, Health)
            health.current -= gc.ITEM_EXTRA_HEALTH_HEALTH_BONUS
            health.maximum -= gc.ITEM_EXTRA_HEALTH_HEALTH_BONUS
    
    @classmethod
    def get_unit_condition(cls) -> UnitCondition:
        """Return the unit condition for this item."""
        return Always()


class ExplodeOnDeath(Item):
    """An item that creates an explosion when the unit dies, damaging all nearby units."""
    
    def apply(self, entity: int) -> None:
        """Add death explosion effect to the entity."""
        death_effect = esper.component_for_entity(entity, OnDeathEffect)
        death_effect.effects.append(ExplodeOnDeathExplosionEffect())
    
    def remove(self, entity: int) -> None:
        """Remove the death explosion effect from the entity."""
        death_effect = esper.component_for_entity(entity, OnDeathEffect)
        for effect in death_effect.effects:
            if isinstance(effect, ExplodeOnDeathExplosionEffect):
                death_effect.effects.remove(effect)
                break
    
    @classmethod
    def get_unit_condition(cls) -> UnitCondition:
        """Return the unit condition for this item."""
        return Always()


class UpgradeArmor(Item):
    """Upgrades a unit's armor. If no armor, adds normal armor. If normal armor, upgrades to heavily armored."""
    
    def apply(self, entity: int) -> None:
        """Apply armor upgrade to the entity."""
        if not esper.has_component(entity, Armor):
            # No armor - add normal armor
            esper.add_component(entity, Armor(level=ArmorLevel.NORMAL))
        else:
            # Has armor - upgrade to heavily armored
            armor = esper.component_for_entity(entity, Armor)
            armor.level = ArmorLevel.HEAVILY
    
    def remove(self, entity: int) -> None:
        """Remove armor upgrade from the entity."""
        if esper.has_component(entity, Armor):
            armor = esper.component_for_entity(entity, Armor)
            if armor.level == ArmorLevel.HEAVILY:
                # Downgrade to normal armor
                armor.level = ArmorLevel.NORMAL
            else:
                # Remove armor completely
                esper.remove_component(entity, Armor)
    
    @classmethod
    def get_unit_condition(cls) -> UnitCondition:
        """Return the unit condition for this item - can only be applied to units that are not heavily armored."""
        return NotHeavilyArmored()

# Item theme IDs for UI styling
item_theme_ids: Dict[ItemType, str] = {
    ItemType.EXTRA_HEALTH: "#extra_health_icon",
    ItemType.EXPLODE_ON_DEATH: "#explode_on_death_icon",
    ItemType.UPGRADE_ARMOR: "#upgrade_armor_icon"
}

# Item icon surfaces for rendering
item_icon_surfaces: Dict[ItemType, pygame.Surface] = {}

# Item registry
item_registry: Dict[ItemType, Item] = {
    ItemType.EXTRA_HEALTH: ExtraHealth(),
    ItemType.EXPLODE_ON_DEATH: ExplodeOnDeath(),
    ItemType.UPGRADE_ARMOR: UpgradeArmor()
}


def load_item_icons() -> None:
    """Load all item icons."""
    item_icon_paths: Dict[ItemType, str] = {
        ItemType.EXTRA_HEALTH: "ExtraHealthIcon.png",
        ItemType.EXPLODE_ON_DEATH: "ExplodeOnDeathIcon.png",
        ItemType.UPGRADE_ARMOR: "UpgradeArmorIcon.png",
    }
    
    for item_type, filename in item_icon_paths.items():
        if item_type in item_icon_surfaces:
            continue
        path = os.path.join("assets", "icons", filename)
        item_icon_surfaces[item_type] = pygame.image.load(path).convert_alpha()