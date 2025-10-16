"""UI component for spell cards."""

import pygame
import pygame_gui
import pygame_gui.core
from typing import Tuple, Optional
from components.spell_type import SpellType
from entities.spells import spell_icon_surfaces
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
                description=f"Summons {gc.SPELL_SUMMON_SKELETON_SWORDSMEN_COUNT} skeleton swordsmen in a circle with a radius of {gc.SPELL_SUMMON_SKELETON_SWORDSMEN_RADIUS}."
            )
        elif spell_type == SpellType.METEOR_SHOWER:
            return SpellData(
                name="Meteor Shower",
                description=f"Summons {gc.SPELL_METEOR_SHOWER_METEOR_COUNT} meteors that rain down from above, dealing {gc.SPELL_METEOR_SHOWER_DAMAGE} damage in a radius of {gc.SPELL_METEOR_SHOWER_AOE_RADIUS} around each impact point."
            )
        elif spell_type == SpellType.INFECTING_AREA:
            return SpellData(
                name="Infecting Area",
                description=f"Creates a {gc.SPELL_INFECTING_AREA_DURATION}-second aura with a radius of {gc.SPELL_INFECTING_AREA_RADIUS} that infects all living units with zombie infection."
            )
        elif spell_type == SpellType.HEALING_AREA:
            return SpellData(
                name="Healing Area",
                description=f"Creates a {gc.SPELL_HEALING_AREA_DURATION}-second aura with a radius of {gc.SPELL_HEALING_AREA_RADIUS} that heals all living allies for {gc.SPELL_HEALING_AREA_HEALING_DPS} HP per second."
            )
        elif spell_type == SpellType.SLOWING_AREA:
            return SpellData(
                name="Slowing Area",
                description=f"Creates a {gc.SPELL_SLOWING_AREA_DURATION}-second aura with a radius of {gc.SPELL_SLOWING_AREA_RADIUS} that slows all living units by {gc.SPELL_SLOWING_AREA_SPEED_REDUCTION_PERCENT * 100:.0f}%."
            )
        elif spell_type == SpellType.CHAIN_EXPLODE_ON_DEATH:
            return SpellData(
                name="Chain Explode On Death",
                description=f"Applies an explode-on-death effect to all living units in a radius of {gc.SPELL_CHAIN_EXPLODE_ON_DEATH_RADIUS}. Affected units explode when they die, dealing {gc.SPELL_CHAIN_EXPLODE_ON_DEATH_DAMAGE} damage in a radius of {gc.SPELL_CHAIN_EXPLODE_ON_DEATH_EXPLOSION_RADIUS}."
            )
        elif spell_type == SpellType.SUMMON_LICH:
            return SpellData(
                name="Summon Lich",
                description=f"Summons a Skeleton Lich once {gc.SPELL_SUMMON_LICH_HP_THRESHOLD} HP worth of usable corpses have died in a radius of {gc.SPELL_SUMMON_LICH_RADIUS}. Corpses are not removed when counted."
            )
        else:
            raise ValueError(f"Unknown spell type: {spell_type}")
    
    def _create_card_content(self) -> None:
        """Create the spell card content with icon at top and description below."""
        # Calculate dimensions
        card_width = self.width - 2 * self.padding
        icon_size = card_width  # Icon takes full width of card
        text_height = self.height - icon_size - 2 * self.padding - 40  # Leave space for icon and padding
        
        # Add spell icon at the top, scaled to full card width
        icon_surface = spell_icon_surfaces[self.spell_type]
        icon_width, icon_height = icon_surface.get_size()
        
        # Scale icon to fit the card width while maintaining aspect ratio
        scale_factor = icon_size / max(icon_width, icon_height)
        scaled_width = int(icon_width * scale_factor)
        scaled_height = int(icon_height * scale_factor)
        
        # Center the icon horizontally
        icon_x = self.padding + (card_width - scaled_width) // 2
        icon_y = self.padding
        
        # Create UIImage for the icon
        self.spell_icon = pygame_gui.elements.UIImage(
            relative_rect=pygame.Rect(
                (icon_x, icon_y),
                (scaled_width, scaled_height)
            ),
            image_surface=pygame.transform.scale(icon_surface, (scaled_width, scaled_height)),
            manager=self.manager,
            container=self.card_container
        )
        
        # Add description text box below the icon
        text_y = icon_y + scaled_height + 10  # 10px gap between icon and text
        self.description_text = pygame_gui.elements.UITextBox(
            relative_rect=pygame.Rect(
                (self.padding, text_y),
                (card_width, text_height)
            ),
            html_text=self.spell_data.description,
            manager=self.manager,
            container=self.card_container
        )
        
        # Store the window reference in the text box's container for link handling
        if self.window is not None:
            self.description_text.ui_container.window = self.window
        elif hasattr(self.container, 'window'):
            self.description_text.ui_container.window = self.container.window
    
    def _kill_card_elements(self) -> None:
        """Kill spell card specific elements."""
        self.spell_icon.kill()
        self.description_text.kill()
