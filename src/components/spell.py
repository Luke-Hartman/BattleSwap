"""Components for spell system."""

from dataclasses import dataclass
from typing import List, Optional, Tuple, Callable
from components.spell_type import SpellType
from effects import Effect


@dataclass
class SpellComponent:
    """Component for managing spells placed on the battlefield.
    
    This component is attached to spell entities that have been placed
    on the battlefield and will be executed when the battle starts or when
    the ready_to_trigger callback returns True.
    """
    
    spell_type: SpellType
    """The type of spell this entity represents."""
    
    team: int
    """The team that cast this spell (TeamType enum value)."""
    
    effects: List[Effect]
    """The effects that will be triggered when this spell is cast."""
    
    radius: Optional[float]
    """The radius of the spell effect area."""
    
    ready_to_trigger: Optional[Callable[[int], bool]]
    """Optional callback function that takes the spell entity ID and returns True when the spell should trigger.
    If None, the spell triggers immediately at battle start. If provided, the spell remains visible
    until the callback returns True."""
    
    def __init__(
        self, 
        spell_type: SpellType, 
        team: int, 
        effects: List[Effect], 
        radius: Optional[float] = None,
        ready_to_trigger: Optional[Callable[[int], bool]] = None
    ):
        self.spell_type = spell_type
        self.team = team
        self.effects = effects
        self.radius = radius
        self.ready_to_trigger = ready_to_trigger


