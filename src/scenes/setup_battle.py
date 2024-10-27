"""Setup battle scene for Battle Swap."""
from pygame_gui.core import ObjectID
from typing import Tuple, Optional
from dataclasses import dataclass
import esper
import pygame
import pygame_gui
from components.position import Position
from components.sprite_sheet import SpriteSheet
from components.team import Team, TeamType
from processors.animation_processor import AnimationProcessor
from processors.rendering_processor import RenderingProcessor, draw_battlefield
from scenes.scene import Scene
from scenes.events import RETURN_TO_SELECT_BATTLE, START_BATTLE
from CONSTANTS import BATTLEFIELD_HEIGHT, BATTLEFIELD_WIDTH, SCREEN_WIDTH, SCREEN_HEIGHT, NO_MANS_LAND_WIDTH
from camera import Camera
from entities.units import UnitType, TeamType, unit_theme_ids, create_unit
from battles import starting_units, enemies

@dataclass
class SelectedUnit:
    """Dataclass to store information about the selected unit."""
    entity: int
    """The entity ID of the selected unit."""
    original_pos: Tuple[float, float]
    """The original position (x, y) of the unit before being moved."""

class SetupBattleScene(Scene):
    """The scene for setting up the battle.
    
    This scene allows players to position their units on the battlefield before the battle begins.
    It provides a UI for selecting units from the barracks and placing them on the field.
    """

    def __init__(self, screen: pygame.Surface, camera: Camera, battle: str):
        """Initialize the setup battle scene.
        
        Args:
            screen: The pygame surface to render to.
            camera: The camera object controlling the view of the battlefield.
            battle: The name of the battle to set up.
        """
        self.screen = screen
        self.camera = camera
        self.battle = battle
        self.manager = pygame_gui.UIManager((SCREEN_WIDTH, SCREEN_HEIGHT), 'src/theme.json')
        self.selected_unit: Optional[SelectedUnit] = None
        self.rendering_processor = RenderingProcessor(screen, self.camera)
        self.units = starting_units

        # Center the camera on the battlefield
        self.camera.x = (BATTLEFIELD_WIDTH - SCREEN_WIDTH) // 2
        self.camera.y = (BATTLEFIELD_HEIGHT - SCREEN_HEIGHT) // 2

        
        self.create_return_button()
        
        esper.add_processor(self.rendering_processor)
        animation_processor = AnimationProcessor()
        esper.add_processor(animation_processor)
        for unit_type, position in enemies[battle]:
            create_unit(position[0], position[1], unit_type, TeamType.TEAM2)

        self.create_ui_elements()


    def create_return_button(self) -> None:
        button_width = 100
        button_height = 30
        button_rect = pygame.Rect(
            (10, 10),
            (button_width, button_height)
        )
        self.return_button = pygame_gui.elements.UIButton(
            relative_rect=button_rect,
            text="Return",
            manager=self.manager
        )

    def create_ui_elements(self) -> None:
        """Create all UI elements for the scene.
        
        Creates:
            - A panel spanning the full width at the bottom showing available units
            - A scrollable container for unit listings
            - Individual unit items showing icon and count
            - A start battle button above the panel
        """
        # Create barracks panel at the bottom, full width
        panel_height = 110
        side_padding = 75
        panel_width = SCREEN_WIDTH - 2 * side_padding
        panel_rect = pygame.Rect(
            (side_padding, SCREEN_HEIGHT - panel_height - 10),
            (panel_width, panel_height)
        )
        self.units_panel = pygame_gui.elements.UIPanel(
            relative_rect=panel_rect,
            manager=self.manager
        )

        # Create scrolling container for unit listings
        padding = 10
        container_rect = pygame.Rect(
            (padding, padding),
            (panel_width - 2 * padding, panel_height - 2 * padding)  # Full width of panel
        )
        self.unit_container = pygame_gui.elements.UIScrollingContainer(
            relative_rect=container_rect,
            manager=self.manager,
            container=self.units_panel,
            allow_scroll_y=False,
        )

        # Create unit listings horizontally
        self.unit_list_items = []
        x_position = 0
        for unit_type, count in self.units.items():
            item = UnitListItem(
                x_pos=x_position,
                y_pos=0,
                unit_type=unit_type,
                count=count,
                manager=self.manager,
                container=self.unit_container
            )
            self.unit_list_items.append(item)
            x_position += item.size + padding // 2

        # Create start button above panel in top right corner
        button_width = 70
        button_height = 40
        button_rect = pygame.Rect(
            (SCREEN_WIDTH - button_width - 10, 10),
            (button_width, button_height)
        )
        self.start_button = pygame_gui.elements.UIButton(
            relative_rect=button_rect,
            text="Start",
            manager=self.manager
        )

    def update(self, time_delta: float, events: list[pygame.event.Event]) -> bool:
        """Update the setup battle scene.

        Handles user input, updates unit positions, and renders the scene.

        Args:
            time_delta: Time passed since last frame in seconds.
            events: List of pygame events to process.

        Returns:
            bool: True if the game should continue, False if it should quit.
        """
        for event in events:
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.start_button:
                        pygame.event.post(pygame.event.Event(START_BATTLE, battle=self.battle))
                    elif event.ui_element == self.return_button:
                        pygame.event.post(pygame.event.Event(RETURN_TO_SELECT_BATTLE))
                        esper.clear_database()
                        esper.remove_processor(RenderingProcessor)
                        esper.remove_processor(AnimationProcessor)
                        return True
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    mouse_pos = pygame.mouse.get_pos()
                    if self.selected_unit is None:
                        self.select_unit(mouse_pos)
                    else:
                        self.selected_unit = None
                elif event.button == 3:  # Right click
                    self.deselect_unit()
            self.manager.process_events(event)

        if self.selected_unit is not None:
            pos = esper.component_for_entity(self.selected_unit.entity, Position)
            mouse_pos = pygame.mouse.get_pos()
            adjusted_mouse_pos = (mouse_pos[0] + self.camera.x, mouse_pos[1] + self.camera.y)
            x, y = adjusted_mouse_pos
            x = max(0, min(x, BATTLEFIELD_WIDTH // 2 - NO_MANS_LAND_WIDTH//2))
            y = max(0, min(y, BATTLEFIELD_HEIGHT))
            pos.x, pos.y = x, y
        self.camera.handle_event(events)

        self.screen.fill((0, 0, 0))
        draw_battlefield(self.screen, self.camera, include_no_mans_land=True)
        if self.selected_unit is not None:
            original_pos_screen = (
                self.selected_unit.original_pos[0] - self.camera.x,
                self.selected_unit.original_pos[1] - self.camera.y
            )
            pygame.draw.circle(self.screen, (0, 200, 0), original_pos_screen, 3)
        esper.process(time_delta)
        self.manager.update(time_delta)
        self.manager.draw_ui(self.screen)
        return True

    def select_unit(self, mouse_pos: Tuple[int, int]) -> None:
        """Select a unit at the given mouse position.
        
        Finds the topmost unit (highest y-value) at the clicked position and makes it
        the currently selected unit for movement.

        Args:
            mouse_pos: The (x, y) screen coordinates where the mouse was clicked.
        """
        adjusted_mouse_pos = (mouse_pos[0] + self.camera.x, mouse_pos[1] + self.camera.y)
        candidate_unit = SelectedUnit(None, (0, -float('inf')))
        for ent, (team, sprite, pos) in esper.get_components(Team, SpriteSheet, Position):
            if team.type == TeamType.TEAM1 and sprite.rect.collidepoint(adjusted_mouse_pos):
                relative_mouse_pos = (
                    adjusted_mouse_pos[0] - sprite.rect.x,
                    adjusted_mouse_pos[1] - sprite.rect.y
                )
                try:
                    if sprite.image.get_at(relative_mouse_pos).a != 0:
                        if pos.y > candidate_unit.original_pos[1]:
                            candidate_unit = SelectedUnit(ent, (pos.x, pos.y))
                except IndexError:
                    pass
        if candidate_unit.entity is not None:
            self.selected_unit = candidate_unit

    def deselect_unit(self) -> None:
        """Deselect the current unit and return it to its original position.
        
        If a unit is currently selected, it will be deselected and moved back
        to the position it was in when it was selected.
        """
        if self.selected_unit is not None:
            pos = esper.component_for_entity(self.selected_unit.entity, Position)
            pos.x, pos.y = self.selected_unit.original_pos
            self.selected_unit = None

class UnitListItem(pygame_gui.elements.UIButton):
    """A custom UI button that displays a unit icon and its count.
    
    This button shows a unit's icon and can be clicked to select the unit type.
    """
    
    size = 64
    
    def __init__(self, 
                 x_pos: int,
                 y_pos: int,
                 unit_type: UnitType,
                 count: int,
                 manager: pygame_gui.UIManager,
                 container: pygame_gui.core.UIContainer):
        """Initialize the unit list item button."""
        super().__init__(
            relative_rect=pygame.Rect((x_pos, y_pos), (self.size, self.size)),
            text=str(count),
            manager=manager,
            container=container,
            object_id=ObjectID(class_id="@unit_list_item", object_id=unit_theme_ids[unit_type])
        )
        self.unit_type = unit_type
        self.count = count
