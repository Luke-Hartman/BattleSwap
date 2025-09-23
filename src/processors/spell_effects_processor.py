"""
Spell effects processor module for Battle Swap.

This module contains the SpellEffectsProcessor class, which is responsible for
applying spell effects when battles begin.
"""

import esper
from typing import List

from components.spell import SpellComponent
from components.position import Position
from effects import Effect, Recipient


class SpellEffectsProcessor(esper.Processor):
    """Processor that applies spell effects when battles begin."""
    
    def process(self, dt: float) -> None:
        """Process spell effects once at the start of battle."""
        # Find all spells and apply their effects
        for ent, (pos, spell_component) in esper.get_components(Position, SpellComponent):
            for effect in spell_component.effects:
                effect.apply(ent, ent, ent)
            esper.remove_component(ent, SpellComponent)
