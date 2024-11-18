"""Button component for reloading game constants."""
import pygame
import pygame_gui
import esper
from game_constants import reload_game_constants
from components.position import Position
from components.team import Team
from components.unit_type import UnitTypeComponent
from entities.units import create_unit


class ReloadConstantsButton:
    """A button that reloads game constants when clicked."""

    def __init__(self, manager: pygame_gui.UIManager):
        """Initialize the reload constants button.
        
        Args:
            manager: The UI manager to create the button with.
        """
        self.button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (pygame.display.Info().current_w - 160, 50),
                (150, 30)
            ),
            text='Reload Constants',
            manager=manager
        )

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle button click events.
        
        Args:
            event: The pygame event to handle.
        """
        if (event.type == pygame.USEREVENT and
            event.user_type == pygame_gui.UI_BUTTON_PRESSED and
            event.ui_element == self.button):
            # Store current unit positions and types
            units = [
                (unit_type.type, pos.x, pos.y, team.type)
                for _, (unit_type, pos, team) 
                in esper.get_components(UnitTypeComponent, Position, Team)
            ]
            
            # Clear all entities
            esper.clear_database()
            
            # Reload constants
            reload_game_constants()
            
            # Recreate units with new stats
            for unit_type, x, y, team_type in units:
                create_unit(x, y, unit_type, team_type) 