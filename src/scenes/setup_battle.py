"""Setup battle scene for Battle Swap."""
from typing import Tuple, Optional
import esper
import pygame
import pygame_gui
from components.position import Position
from components.sprite_sheet import SpriteSheet
from components.team import Team, TeamType
from components.unit_type import UnitTypeComponent
from processors.animation_processor import AnimationProcessor
from processors.rendering_processor import RenderingProcessor, draw_battlefield
from scenes.scene import Scene
from scenes.events import SELECT_BATTLE_SCENE, BATTLE_SCENE
from CONSTANTS import BATTLEFIELD_HEIGHT, BATTLEFIELD_WIDTH, NO_MANS_LAND_WIDTH
from camera import Camera
from entities.units import TeamType, create_unit
from battles import get_battle
from ui_components.start_button import StartButton
from ui_components.return_button import ReturnButton
from ui_components.barracks_ui import BarracksUI, UnitCount
from progress_manager import ProgressManager, Solution
from ui_components.tip_box import TipBox


class SetupBattleScene(Scene):
    """The scene for setting up the battle.
    
    This scene allows players to position their units on the battlefield before the battle begins.
    It provides a UI for selecting units from the barracks and placing them on the field.
    """

    def __init__(
            self,
            screen: pygame.Surface,
            camera: Camera,
            manager: pygame_gui.UIManager,
            battle_id: str,
            progress_manager: ProgressManager,
            potential_solution: Optional[Solution] = None
    ):
        """Initialize the setup battle scene.
        
        Args:
            screen: The pygame surface to render to.
            camera: The camera object controlling the view of the battlefield.
            manager: The pygame_gui manager for the scene.
            battle_id: The name of the battle to set up.
            progress_manager: The progress manager for the game.
            potential_solution: The potential solution to the battle, if any.
        """
        self.screen = screen
        self.progress_manager = progress_manager
        self.camera = camera
        self.battle = get_battle(battle_id)
        self.manager = manager
        self.selected_unit_id: Optional[int] = None
        self.rendering_processor = RenderingProcessor(screen, self.camera)

        # Center the camera on the battlefield
        self.camera.x = (BATTLEFIELD_WIDTH - pygame.display.Info().current_w) // 2
        self.camera.y = (BATTLEFIELD_HEIGHT - pygame.display.Info().current_h) // 2
        
        self.return_button = ReturnButton(self.manager)
        
        esper.add_processor(self.rendering_processor)
        animation_processor = AnimationProcessor()
        esper.add_processor(animation_processor)

        for unit_type, position in self.battle.enemies:
            create_unit(position[0], position[1], unit_type, TeamType.TEAM2)

        self.barracks = BarracksUI(
            self.manager,
            self.progress_manager.available_units(current_battle_id=battle_id),
            interactive=True,
            sandbox_mode=False,
        )
        self.start_button = StartButton(self.manager)
        self.potential_solution = potential_solution
        if potential_solution is not None:
            for (unit_type, position) in potential_solution.unit_placements:
                create_unit(position[0], position[1], unit_type, TeamType.TEAM1)
                self.barracks.remove_unit(unit_type)

        
        self.tip_box = TipBox(self.manager, self.battle)

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
                        if self.selected_unit_id is not None:
                            self.return_unit_to_barracks(self.selected_unit_id)
                            self.selected_unit_id = None
                        unit_placements = []
                        for ent, (team, unit_type, pos) in esper.get_components(Team, UnitTypeComponent, Position):
                            if team.type == TeamType.TEAM1:
                                unit_placements.append((unit_type.type, (pos.x, pos.y)))
                        self.potential_solution = Solution(self.battle.id, unit_placements)
                        pygame.event.post(pygame.event.Event(BATTLE_SCENE, potential_solution=self.potential_solution))
                    elif event.ui_element == self.return_button:
                        pygame.event.post(pygame.event.Event(SELECT_BATTLE_SCENE))
                        esper.clear_database()
                        esper.remove_processor(RenderingProcessor)
                        esper.remove_processor(AnimationProcessor)
                        return True
                    elif isinstance(event.ui_element, UnitCount):
                        self.create_unit_from_list(event.ui_element)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    mouse_pos = pygame.mouse.get_pos()
                    if self.selected_unit_id is None:
                        self.selected_unit_id = self.click_on_unit(mouse_pos)
                    else:
                        # Mouse must be within 25 pixels of the legal placement area to place the unit
                        grace_zone = 25
                        pos = esper.component_for_entity(self.selected_unit_id, Position)
                        adjusted_mouse_pos = (mouse_pos[0] + self.camera.x, mouse_pos[1] + self.camera.y)
                        distance = ((adjusted_mouse_pos[0] - pos.x)**2 + (adjusted_mouse_pos[1] - pos.y)**2)**0.5
                        if distance <= grace_zone:
                            self.place_unit()
                elif event.button == 3:  # Right click
                    if self.selected_unit_id is not None:
                        self.return_unit_to_barracks(self.selected_unit_id)
                    else:
                        mouse_pos = pygame.mouse.get_pos()
                        clicked_on_unit = self.click_on_unit(mouse_pos)
                        if clicked_on_unit is not None:
                            self.return_unit_to_barracks(clicked_on_unit)
            self.manager.process_events(event)

        if self.selected_unit_id is not None:
            pos = esper.component_for_entity(self.selected_unit_id, Position)
            mouse_pos = pygame.mouse.get_pos()
            adjusted_mouse_pos = (mouse_pos[0] + self.camera.x, mouse_pos[1] + self.camera.y)
            x, y = adjusted_mouse_pos
            x = max(0, min(x, BATTLEFIELD_WIDTH // 2 - NO_MANS_LAND_WIDTH//2))
            y = max(0, min(y, BATTLEFIELD_HEIGHT))
            pos.x, pos.y = x, y
        self.camera.update(time_delta)

        self.screen.fill((0, 0, 0))
        draw_battlefield(self.screen, self.camera, include_no_mans_land=True)
        esper.process(time_delta)
        self.manager.update(time_delta)
        self.manager.draw_ui(self.screen)
        return True

    def click_on_unit(self, mouse_pos: Tuple[int, int]) -> Optional[int]:
        """Return the unit from team 1 at the given mouse position.
        
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
        return candidate_unit_id

    def place_unit(self) -> None:
        """Place the currently selected unit on the battlefield."""
        assert self.selected_unit_id is not None
        unit_type = esper.component_for_entity(self.selected_unit_id, UnitTypeComponent).type
        # if there are more available, continue to place them
        if self.barracks.units[unit_type] > 0:
            entity = create_unit(0, 0, unit_type, TeamType.TEAM1)
            self.barracks.remove_unit(unit_type)
            self.selected_unit_id = entity
        else:
            self.selected_unit_id = None

    def return_unit_to_barracks(self, unit_id: int) -> None:
        """Deselect the current unit and return it to the unit pool."""
        unit_type = esper.component_for_entity(unit_id, UnitTypeComponent).type
        esper.delete_entity(unit_id, immediate=True)
        self.barracks.add_unit(unit_type)
        self.selected_unit_id = None

    def create_unit_from_list(self, unit_list_item: UnitCount) -> None:
        """Create a unit from a unit list item and update the UI."""
        entity = create_unit(0, 0, unit_list_item.unit_type, TeamType.TEAM1)
        self.barracks.remove_unit(unit_list_item.unit_type)
        self.selected_unit_id = entity
