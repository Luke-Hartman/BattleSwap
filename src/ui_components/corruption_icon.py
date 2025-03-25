import pygame
import pygame_gui
from typing import List, Optional, Tuple
import os

from corruption_powers import CorruptionPower

icon_surface = None

def load_corruption_icon_surface() -> pygame.Surface:
    """Load the corruption icon surface."""
    global icon_surface
    if icon_surface is None:
        icon_surface = pygame.image.load(os.path.join("assets", "icons", "CorruptionIcon.png")).convert_alpha()
    return icon_surface

class CorruptionIcon(pygame_gui.elements.UIImage):
    """A UI component for displaying corruption powers, extending UIImage."""
    
    def __init__(
        self,
        manager: pygame_gui.UIManager,
        position: Tuple[int, int],
        size: Tuple[int, int],
        battle_hex_coords: Optional[Tuple[int, int]] = None,
        corruption_powers: Optional[List[CorruptionPower]] = None
    ):
        """
        Initialize the corruption icon.
        
        Args:
            manager: The pygame_gui UIManager
            position: The (x, y) position of the icon
            size: The (width, height) size of the icon
            battle_hex_coords: The hex coordinates of the battle to show powers for
            corruption_powers: The list of corruption powers to show
        """
        self.battle_hex_coords = battle_hex_coords
        self.corruption_powers = corruption_powers

        scaled_surface = pygame.transform.scale(load_corruption_icon_surface(), size)

        super().__init__(
            relative_rect=pygame.Rect(position, size),
            image_surface=scaled_surface,
            manager=manager
        )
        self.tool_tip_text = self._get_tooltip_text()
        self.tool_tip_delay = 0
    
    def _get_tooltip_text(self) -> str:
        """Generate tooltip text based on corruption powers."""
        tooltip = ""
        for power in self.corruption_powers:
            tooltip += f"{power.description}\n"
        
        return tooltip