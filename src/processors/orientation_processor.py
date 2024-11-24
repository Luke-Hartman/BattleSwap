"""Orientation processor module for Battle Swap."""

import esper
import pygame
from components.orientation import Orientation, FacingDirection
from components.sprite_sheet import SpriteSheet

class OrientationProcessor(esper.Processor):
    """Processor responsible for updating the orientation of sprites."""

    def process(self, dt: float):
        """Process all entities with SpriteSheet and Orientation components."""
        for ent, (sprite_sheet, orientation) in esper.get_components(SpriteSheet, Orientation):
            if orientation.facing == FacingDirection.LEFT:
                previous_position = sprite_sheet.rect.center
                previous_offset = sprite_sheet.sprite_center_offset
                sprite_sheet.sprite_center_offset = (
                    -sprite_sheet.sprite_center_offset[0],
                    sprite_sheet.sprite_center_offset[1]
                )
                sprite_sheet.image = pygame.transform.flip(sprite_sheet.image, True, False)
                sprite_sheet.rect = sprite_sheet.image.get_rect()
                sprite_sheet.rect.center = (
                    previous_position[0] - previous_offset[0] + sprite_sheet.sprite_center_offset[0],
                    previous_position[1] - previous_offset[1] + sprite_sheet.sprite_center_offset[1]
                )
