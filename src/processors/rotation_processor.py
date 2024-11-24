"""Rotation processor module for Battle Swap."""

import math
import esper
import pygame
from components.angle import Angle
from components.sprite_sheet import SpriteSheet

class RotationProcessor(esper.Processor):
    """Processor responsible for updating the rotation of sprites."""

    def process(self, dt: float):
        """Process all entities with SpriteSheet and Angle components."""
        for ent, (sprite_sheet, angle) in esper.get_components(SpriteSheet, Angle):
            previous_position = sprite_sheet.rect.center
            previous_offset = sprite_sheet.sprite_center_offset
            sprite_sheet.sprite_center_offset = (
                angle.x * sprite_sheet.sprite_center_offset[0] + angle.y * sprite_sheet.sprite_center_offset[1],
                angle.y * sprite_sheet.sprite_center_offset[1] - angle.x * sprite_sheet.sprite_center_offset[0]
            )
            sprite_sheet.image = pygame.transform.rotate(sprite_sheet.image, -math.degrees(angle.angle))
            sprite_sheet.rect = sprite_sheet.image.get_rect()
            sprite_sheet.rect.center = (
                previous_position[0] - previous_offset[0] + sprite_sheet.sprite_center_offset[0],
                previous_position[1] - previous_offset[1] + sprite_sheet.sprite_center_offset[1]
            )