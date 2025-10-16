"""
Spell effects processor module for Battle Swap.

This module contains the SpellEffectsProcessor class, which is responsible for
applying spell effects when battles begin or when spell conditions are met.
"""

import esper
from typing import List

from components.spell import SpellComponent
from components.position import Position
from effects import Effect, Recipient


class SpellEffectsProcessor(esper.Processor):
    """Processor that applies spell effects when ready."""
    
    def process(self, dt: float) -> None:
        """Process spell effects when they are ready to trigger."""
        # Find all spells and check if they're ready to trigger
        for ent, (pos, spell_component) in esper.get_components(Position, SpellComponent):
            # Check if spell is ready to trigger
            if spell_component.ready_to_trigger is not None and not spell_component.ready_to_trigger(ent):
                continue
            
            # Spell is ready (either no callback or callback returned True)
            for effect in spell_component.effects:
                effect.apply(None, ent, None)
            esper.remove_component(ent, SpellComponent)
