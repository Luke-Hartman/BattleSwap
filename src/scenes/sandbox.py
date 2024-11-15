"""Sandbox scene for experimenting with unit placement and battles."""
from typing import Optional, List, Tuple
import esper
import pygame
import pygame_gui
from components.orientation import FacingDirection, Orientation
from components.position import Position
from components.sprite_sheet import SpriteSheet
from components.team import Team, TeamType
from components.unit_type import UnitType, UnitTypeComponent
from processors.animation_processor import AnimationProcessor
from processors.rendering_processor import RenderingProcessor, draw_battlefield
from scenes.scene import Scene
from CONSTANTS import BATTLEFIELD_HEIGHT, BATTLEFIELD_WIDTH, NO_MANS_LAND_WIDTH
from camera import Camera
from entities.units import create_unit
from ui_components.barracks_ui import BarracksUI, UnitCount
from ui_components.return_button import ReturnButton
from ui_components.start_button import StartButton
from scenes.events import RETURN_TO_SELECT_BATTLE, START_BATTLE
from progress_manager import Solution


class SandboxScene(Scene):
    """A sandbox scene for experimenting with unit placement and battles.
    
    This scene allows placing any units on either team without restrictions.
    Units can be placed on their respective sides of the battlefield.
    """

    def __init__(
        self,
        screen: pygame.Surface,
        camera: Camera,
        manager: pygame_gui.UIManager,
        unit_placements: Optional[List[Tuple[UnitType, Tuple[int, int]]]] = None,
        enemy_placements: Optional[List[Tuple[UnitType, Tuple[int, int]]]] = None,
    ):
        """Initialize the sandbox scene.
        
        Args:
            screen: The pygame surface to render to.
            camera: The camera object controlling the view of the battlefield.
            manager: The pygame_gui manager for the scene.
            unit_placements: Optional list of unit placements to restore
            enemy_placements: Optional list of enemy placements to restore
        """
        self.screen = screen
        self.camera = camera
        self.manager = manager
        self.selected_unit_id: Optional[int] = None
        self.rendering_processor = RenderingProcessor(screen, self.camera)

        # Center the camera on the battlefield
        self.camera.x = (BATTLEFIELD_WIDTH - pygame.display.Info().current_w) // 2
        self.camera.y = (BATTLEFIELD_HEIGHT - pygame.display.Info().current_h) // 2
        
        self.return_button = ReturnButton(self.manager)
        self.start_button = StartButton(self.manager)
        
        esper.add_processor(self.rendering_processor)
        esper.add_processor(AnimationProcessor())

        self.barracks = BarracksUI(
            self.manager,
            starting_units={},
            interactive=True,
            sandbox_mode=True,
        )

        # Restore previous unit placements if provided
        if unit_placements:
            for unit_type, pos in unit_placements:
                create_unit(pos[0], pos[1], unit_type, TeamType.TEAM1)
        
        if enemy_placements:
            for unit_type, pos in enemy_placements:
                create_unit(pos[0], pos[1], unit_type, TeamType.TEAM2)

    def update(self, time_delta: float, events: list[pygame.event.Event]) -> bool:
        """Update the sandbox scene."""
        for event in events:
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.return_button:
                        pygame.event.post(pygame.event.Event(RETURN_TO_SELECT_BATTLE))
                        esper.clear_database()
                        esper.remove_processor(RenderingProcessor)
                        esper.remove_processor(AnimationProcessor)
                        return True
                    elif event.ui_element == self.start_button:
                        unit_placements = []
                        for ent, (team, unit_type, pos) in esper.get_components(Team, UnitTypeComponent, Position):
                            if team.type == TeamType.TEAM1:
                                unit_placements.append((unit_type.type, (pos.x, pos.y)))
                        sandbox_solution = Solution("SANDBOX", unit_placements)
                        pygame.event.post(pygame.event.Event(START_BATTLE, potential_solution=sandbox_solution, sandbox_mode=True))
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
                        esper.delete_entity(self.selected_unit_id, immediate=True)
                        self.selected_unit_id = None
                    else:
                        mouse_pos = pygame.mouse.get_pos()
                        clicked_on_unit = self.click_on_unit(mouse_pos)
                        if clicked_on_unit is not None:
                            esper.delete_entity(clicked_on_unit, immediate=True)

            self.manager.process_events(event)

        if self.selected_unit_id is not None:
            pos = esper.component_for_entity(self.selected_unit_id, Position)
            team = esper.component_for_entity(self.selected_unit_id, Team)
            mouse_pos = pygame.mouse.get_pos()
            adjusted_mouse_pos = (mouse_pos[0] + self.camera.x, mouse_pos[1] + self.camera.y)
            x, y = adjusted_mouse_pos
            
            # Update team based on which side of the battlefield the mouse is on
            new_team = TeamType.TEAM1 if x < BATTLEFIELD_WIDTH // 2 else TeamType.TEAM2
            if team.type != new_team:
                team.type = new_team
                orientation = esper.component_for_entity(self.selected_unit_id, Orientation)
                orientation.facing = FacingDirection.RIGHT if new_team == TeamType.TEAM1 else FacingDirection.LEFT

            
            # Constrain x based on current team
            if team.type == TeamType.TEAM1:
                x = max(0, min(x, BATTLEFIELD_WIDTH // 2 - NO_MANS_LAND_WIDTH//2))
            else:
                x = max(BATTLEFIELD_WIDTH // 2 + NO_MANS_LAND_WIDTH//2, min(x, BATTLEFIELD_WIDTH))
            
            y = max(0, min(y, BATTLEFIELD_HEIGHT))
            pos.x, pos.y = x, y

        self.camera.handle_event(events)

        self.screen.fill((0, 0, 0))
        draw_battlefield(self.screen, self.camera, include_no_mans_land=True)
        esper.process(time_delta)
        self.manager.update(time_delta)
        self.manager.draw_ui(self.screen)
        return True

    def click_on_unit(self, mouse_pos: tuple[int, int]) -> Optional[int]:
        """Return the unit at the given mouse position."""
        adjusted_mouse_pos = (mouse_pos[0] + self.camera.x, mouse_pos[1] + self.camera.y)
        candidate_unit_id = None
        highest_y = -float('inf')
        for ent, (sprite, pos) in esper.get_components(SpriteSheet, Position):
            if sprite.rect.collidepoint(adjusted_mouse_pos):
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

    def create_unit_from_list(self, unit_list_item: UnitCount) -> None:
        """Create a unit from a barracks selection."""
        # Create unit with initial team based on mouse position
        mouse_pos = pygame.mouse.get_pos()
        adjusted_x = mouse_pos[0] + self.camera.x
        team_type = TeamType.TEAM1 if adjusted_x < BATTLEFIELD_WIDTH // 2 else TeamType.TEAM2
        
        entity = create_unit(0, 0, unit_list_item.unit_type, team_type)
        self.selected_unit_id = entity

    def place_unit(self) -> None:
        """Place the currently selected unit on the battlefield."""
        assert self.selected_unit_id is not None
        unit_type = esper.component_for_entity(self.selected_unit_id, UnitTypeComponent).type
        team = esper.component_for_entity(self.selected_unit_id, Team).type
        
        # Create a new unit of the same type and team
        entity = create_unit(0, 0, unit_type, team)
        self.selected_unit_id = entity
