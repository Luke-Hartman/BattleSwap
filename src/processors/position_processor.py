"""Position processor module for Battle Swap."""

import esper
from components.position import Position
from components.sprite_sheet import SpriteSheet

class PositionProcessor(esper.Processor):
    """Processor responsible for updating the position of entities."""

    def process(self, dt: float):
        """Process all entities with Position components."""
        for ent, (pos, sprite_sheet) in esper.get_components(Position, SpriteSheet):
            sprite_sheet.rect.center = (pos.x + sprite_sheet.sprite_center_offset[0], pos.y + sprite_sheet.sprite_center_offset[1])