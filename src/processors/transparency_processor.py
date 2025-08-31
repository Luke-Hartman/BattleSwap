from esper import Processor
import esper
import pygame

from components.sprite_sheet import SpriteSheet
from components.status_effect import Invisible, StatusEffects
from components.transparent import Transparency


class TransparencyProcessor(Processor):
    """A processor that updates the transparency of entities."""

    def process(self, dt: float) -> None:
        """Process the transparency of entities."""
        for ent, (status_effects, sprite_sheet) in esper.get_components(StatusEffects, SpriteSheet):
            if any(isinstance(effect, Invisible) for effect in status_effects.active_effects()):
                sprite_sheet.image.set_alpha(128)
            else:
                sprite_sheet.image.set_alpha(255)
        for ent, (transparency, sprite_sheet) in esper.get_components(Transparency, SpriteSheet):
            sprite_sheet.image.set_alpha(transparency.alpha)