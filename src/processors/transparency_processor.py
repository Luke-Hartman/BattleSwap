from esper import Processor
import esper
import pygame

from components.sprite_sheet import SpriteSheet
from components.transparent import Transparency


class TransparencyProcessor(Processor):
    """A processor that updates the transparency of entities."""

    def process(self, dt: float) -> None:
        """Process the transparency of entities."""
        for ent, (transparency, sprite_sheet) in esper.get_components(Transparency, SpriteSheet):
            sprite_sheet.image.set_alpha(transparency.alpha)
