"""Module for handling items in the game."""

from enum import Enum
from abc import ABC, abstractmethod
from typing import Dict
import esper
from components.health import Health
from game_constants import gc

class ItemType(Enum):
    """Types of items that can be equipped to units."""
    HEALTH_POTION = "health_potion"

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

class HealthPotion(Item):
    """A health potion that grants +500 HP to the equipped unit."""

    def apply(self, entity: int) -> None:
        """Apply health bonus to the entity."""
        if esper.has_component(entity, Health):
            health = esper.component_for_entity(entity, Health)
            health.current += gc.ITEM_HEALTH_POTION_HEALTH_BONUS
            health.maximum += gc.ITEM_HEALTH_POTION_HEALTH_BONUS
    
    def remove(self, entity: int) -> None:
        """Remove health bonus from the entity."""
        if esper.has_component(entity, Health):
            health = esper.component_for_entity(entity, Health)
            health.current -= gc.ITEM_HEALTH_POTION_HEALTH_BONUS
            health.maximum -= gc.ITEM_HEALTH_POTION_HEALTH_BONUS

# Item theme IDs for UI styling
item_theme_ids: Dict[ItemType, str] = {
    ItemType.HEALTH_POTION: "#health_potion_icon"
}

# Item registry
item_registry: Dict[ItemType, Item] = {
    ItemType.HEALTH_POTION: HealthPotion()
}