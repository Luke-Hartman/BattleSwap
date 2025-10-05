"""Components for item system."""

from enum import Enum
from typing import List


class ItemType(str, Enum):
    """Types of items that can be equipped to units."""
    EXTRA_HEALTH = "extra_health"
    EXPLODE_ON_DEATH = "EXPLODE_ON_DEATH"
    UPGRADE_ARMOR = "upgrade_armor"
    DAMAGE_AURA = "damage_aura"
    EXTRA_MOVEMENT_SPEED = "extra_movement_speed"
    HEAL_ON_KILL = "heal_on_kill"
    INFECT_ON_HIT = "infect_on_hit"
    HUNTER = "hunter"
    REFLECT_DAMAGE = "reflect_damage"
    START_INVISIBLE = "start_invisible"
    STATIC_DISCHARGE = "static_discharge"


class ItemComponent:
    """Component for managing items equipped to an entity. All units have this component, even if they have no items."""
    
    def __init__(self, items: List[ItemType] = None):
        self.items = items or []
    
