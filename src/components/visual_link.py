from dataclasses import dataclass
from typing import Optional
from unit_condition import UnitCondition
from visuals import Visual

@dataclass
class VisualLink:

    other_entity: int
    """The entity at the end of the link."""

    visual: Visual
    """The visual to tile between the start and end entities."""

    tile_size: float
    """The size of the tiles to use for the link."""

    entity_delete_condition: Optional[UnitCondition] = None
    """The condition that, if met, will remove the visual link."""

    other_entity_delete_condition: Optional[UnitCondition] = None
    """The condition that, if met, will remove the visual link."""
