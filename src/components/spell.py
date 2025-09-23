"""Components for spell system."""

from dataclasses import dataclass
from typing import List, Optional, Tuple
from components.spell_type import SpellType
from effects import Effect


@dataclass
class SpellComponent:
    """Component for managing spells placed on the battlefield.
    
    This component is attached to spell entities that have been placed
    on the battlefield and will be executed when the battle starts.
    """
    
    spell_type: SpellType
    """The type of spell this entity represents."""
    
    team: int
    """The team that cast this spell (TeamType enum value)."""
    
    effects: List[Effect]
    """The effects that will be triggered when this spell is cast."""
    
    radius: float
    """The radius of the spell effect area."""
    
    def __init__(self, spell_type: SpellType, team: int, effects: List[Effect], radius: float):
        self.spell_type = spell_type
        self.team = team
        self.effects = effects
        self.radius = radius


