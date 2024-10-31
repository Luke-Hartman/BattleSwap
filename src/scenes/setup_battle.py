"""Setup battle scene for Battle Swap."""
from pygame_gui.core import ObjectID
from typing import Tuple, Optional
import esper
import pygame
import pygame_gui
from components.position import Position
from components.sprite_sheet import SpriteSheet
from components.team import Team, TeamType
from components.unit_type import UnitType, UnitTypeComponent
from processors.animation_processor import AnimationProcessor
from processors.rendering_processor import RenderingProcessor, draw_battlefield
from scenes.scene import Scene
from scenes.events import RETURN_TO_SELECT_BATTLE, START_BATTLE
from CONSTANTS import BATTLEFIELD_HEIGHT, BATTLEFIELD_WIDTH, SCREEN_WIDTH, SCREEN_HEIGHT, NO_MANS_LAND_WIDTH
from camera import Camera
from entities.units import TeamType, unit_theme_ids, create_unit
from battles import starting_units, enemies
from ui_components.start_button import StartButton
from ui_components.return_button import ReturnButton
from ui_components.barracks_ui import BarracksUI, UnitListItem

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
        self.selected_unit_id: Optional[int] = None
        self.rendering_processor = RenderingProcessor(screen, self.camera)

        # Center the camera on the battlefield
        self.camera.x = (BATTLEFIELD_WIDTH - SCREEN_WIDTH) // 2
        self.camera.y = (BATTLEFIELD_HEIGHT - SCREEN_HEIGHT) // 2
        
        self.return_button = ReturnButton(self.manager)
        
        esper.add_processor(self.rendering_processor)
        animation_processor = AnimationProcessor()
        esper.add_processor(animation_processor)
        for unit_type, position in enemies[battle]:
            create_unit(position[0], position[1], unit_type, TeamType.TEAM2)

        self.barracks = BarracksUI(self.manager, starting_units.copy())
        self.start_button = StartButton(self.manager)

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
                    elif isinstance(event.ui_element, UnitListItem):
                        self.create_unit_from_list(event.ui_element)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    mouse_pos = pygame.mouse.get_pos()
                    if self.selected_unit_id is None:
                        self.select_unit(mouse_pos)
                    else:
                        self.selected_unit_id = None
                elif event.button == 3:  # Right click
                    self.deselect_unit()
            self.manager.process_events(event)

        if self.selected_unit_id is not None:
            pos = esper.component_for_entity(self.selected_unit_id, Position)
            mouse_pos = pygame.mouse.get_pos()
            adjusted_mouse_pos = (mouse_pos[0] + self.camera.x, mouse_pos[1] + self.camera.y)
            x, y = adjusted_mouse_pos
            x = max(0, min(x, BATTLEFIELD_WIDTH // 2 - NO_MANS_LAND_WIDTH//2))
            y = max(0, min(y, BATTLEFIELD_HEIGHT))
            pos.x, pos.y = x, y
        self.camera.handle_event(events)

        self.screen.fill((0, 0, 0))
        draw_battlefield(self.screen, self.camera, include_no_mans_land=True)
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
        candidate_unit_id = None
        highest_y = -float('inf')
        for ent, (team, sprite, pos) in esper.get_components(Team, SpriteSheet, Position):
            if team.type == TeamType.TEAM1 and sprite.rect.collidepoint(adjusted_mouse_pos):
                relative_mouse_pos = (
                    adjusted_mouse_pos[0] - sprite.rect.x,
                    adjusted_mouse_pos[1] - sprite.rect.y
                )
                try:
                    if sprite.image.get_at(relative_mouse_pos).a != 0:
                        if pos.y > highest_y:
                            highest_y = pos.y
                            candidate_unit_id = ent
                except IndexError:
                    pass
        if candidate_unit_id is not None:
            self.selected_unit_id = candidate_unit_id

    def deselect_unit(self) -> None:
        """Deselect the current unit and return it to the unit pool."""
        if self.selected_unit_id is not None:
            unit_type = esper.component_for_entity(self.selected_unit_id, UnitTypeComponent).type
            esper.delete_entity(self.selected_unit_id)
            self.barracks.add_unit(unit_type)
            self.selected_unit_id = None

    def create_unit_from_list(self, unit_list_item: UnitListItem) -> None:
        """Create a unit from a unit list item and update the UI."""
        entity = create_unit(0, 0, unit_list_item.unit_type, TeamType.TEAM1)
        self.barracks.remove_unit(unit_list_item.unit_type)
        self.selected_unit_id = entity
