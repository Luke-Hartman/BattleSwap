"""Components for item system."""

from entities.items import ItemType
from typing import List


class ItemComponent:
    """Component for managing items equipped to an entity. All units have this component, even if they have no items."""
    
    def __init__(self, items: List[ItemType] = None):
        self.items = items or []
    
