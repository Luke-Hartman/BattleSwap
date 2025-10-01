"""UI component for spell cards."""

import pygame
import pygame_gui
import pygame_gui.core
from typing import Tuple, Optional
from components.spell_type import SpellType
from ui_components.base_card import BaseCard
from game_constants import gc


class SpellCard(BaseCard):
    """A simple UI component that displays a spell card with description."""
    
    def __init__(self, 
                 screen: pygame.Surface,
                 manager: pygame_gui.UIManager,
                 position: Tuple[int, int],
                 spell_type: SpellType,
                 container: Optional[pygame_gui.core.UIContainer] = None,
                 padding: int = 0):
        """
        Initialize a SpellCard component.
        
        Args:
            screen: The pygame surface
            manager: The UI manager for this component
            position: The (x, y) position to place the window (ignored if container is provided)
            spell_type: The type of spell to display
            container: Optional container to place the card in (if None, creates a window)
            padding: Padding around the spell card
        """
        self.spell_type = spell_type
        
        # Get spell data
        self.spell_data = self._get_spell_data(spell_type)
        
        # Initialize base card
        super().__init__(
            screen=screen,
            manager=manager,
            position=position,
            title=self.spell_data.name,
            container=container,
            padding=padding
        )
    
    def _get_spell_data(self, spell_type: SpellType):
        """Get spell data for the given spell type."""
        # Simple data class for spell information
        class SpellData:
            def __init__(self, name: str, description: str):
                self.name = name
                self.description = description
        
        if spell_type == SpellType.SUMMON_SKELETON_SWORDSMEN:
            return SpellData(
                name="Summon Skeleton Swordsmen",
                description=f"Summons {gc.SPELL_SUMMON_SKELETON_SWORDSMEN_COUNT} skeleton swordsmen in a circle with radius {gc.SPELL_SUMMON_SKELETON_SWORDSMEN_RADIUS}."
            )
        elif spell_type == SpellType.METEOR_SHOWER:
            return SpellData(
                name="Meteor Shower",
                description=f"Summons {gc.SPELL_METEOR_SHOWER_METEOR_COUNT} meteors that rain down from above, dealing {gc.SPELL_METEOR_SHOWER_DAMAGE} damage in a {gc.SPELL_METEOR_SHOWER_AOE_RADIUS} radius around each impact point."
            )
        elif spell_type == SpellType.INFECT_AREA:
            return SpellData(
                name="Infect Area",
                description=f"Creates a {gc.SPELL_INFECT_AREA_DURATION}-second aura with radius {gc.SPELL_INFECT_AREA_RADIUS} that infects all living units with zombie infection."
            )
        else:
            raise ValueError(f"Unknown spell type: {spell_type}")
    
    def _create_card_content(self) -> None:
        """Create the spell card content."""
        # Add description
        self.description_label = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (self.padding, self.padding),
                (self.width - 2 * self.padding, self.height - 2 * self.padding)
            ),
            text=self.spell_data.description,
            manager=self.manager,
            container=self.card_container
        )
    
    def _kill_card_elements(self) -> None:
        """Kill spell card specific elements."""
        self.description_label.kill()
