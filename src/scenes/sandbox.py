"""Sandbox scene for experimenting with unit placement and battles."""
from typing import Optional, List, Tuple
import esper
import pygame
import pygame_gui
from components.position import Position
from components.range_indicator import RangeIndicator
from components.sprite_sheet import SpriteSheet
from components.stats_card import StatsCard
from components.team import Team, TeamType
from components.unit_type import UnitType, UnitTypeComponent
from events import CHANGE_MUSIC, ChangeMusicEvent, emit_event
from processors.animation_processor import AnimationProcessor
from processors.orientation_processor import OrientationProcessor
from processors.position_processor import PositionProcessor
from processors.rendering_processor import RenderingProcessor, draw_battlefield
from processors.rotation_processor import RotationProcessor
from scenes.scene import Scene
from game_constants import gc
from camera import Camera
from entities.units import create_unit
from ui_components.barracks_ui import BarracksUI, UnitCount
from ui_components.return_button import ReturnButton
from ui_components.start_button import StartButton
from scenes.events import BattleSceneEvent, PreviousSceneEvent
from ui_components.save_battle_dialog import SaveBattleDialog
from ui_components.reload_constants_button import ReloadConstantsButton
from auto_battle import BattleOutcome, get_unit_placements, simulate_battle


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
        ally_placements: Optional[List[Tuple[UnitType, Tuple[int, int]]]],
        enemy_placements: Optional[List[Tuple[UnitType, Tuple[int, int]]]],
        battle_id: Optional[str],
    ):
        """Initialize the sandbox scene.
        
        Args:
            screen: The pygame surface to render to.
            camera: The camera object controlling the view of the battlefield.
            manager: The pygame_gui manager for the scene.
            ally_placements: List of starting ally placements
            enemy_placements: List of starting enemy placements
            battle_id: Optional battle id when saving.
        """
        emit_event(CHANGE_MUSIC, event=ChangeMusicEvent(
            filename="Main Theme.wav",
        ))
        self.screen = screen
        self.camera = camera
        self.manager = manager
        self.selected_unit_id: Optional[int] = None
        self.rendering_processor = RenderingProcessor(screen, self.camera, self.manager)

        # Center the camera on the battlefield
        self.camera.x = (gc.BATTLEFIELD_WIDTH - pygame.display.Info().current_w) // 2
        self.camera.y = (gc.BATTLEFIELD_HEIGHT - pygame.display.Info().current_h) // 2
        
        self.return_button = ReturnButton(self.manager)
        self.start_button = StartButton(self.manager)
        
        esper.add_processor(self.rendering_processor)
        esper.add_processor(AnimationProcessor())
        esper.add_processor(PositionProcessor())
        esper.add_processor(OrientationProcessor())
        esper.add_processor(RotationProcessor())
        self.barracks = BarracksUI(
            self.manager,
            starting_units={},
            interactive=True,
            sandbox_mode=True,
        )

        # Restore previous unit placements if provided
        if ally_placements:
            for unit_type, pos in ally_placements:
                create_unit(pos[0], pos[1], unit_type, TeamType.TEAM1)
        
        if enemy_placements:
            for unit_type, pos in enemy_placements:
                create_unit(pos[0], pos[1], unit_type, TeamType.TEAM2)

        # Add save battle button
        self.save_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (pygame.display.Info().current_w - 310, 10),
                (100, 30)
            ),
            text='Save Battle',
            manager=self.manager
        )
        
        self.save_dialog: Optional[SaveBattleDialog] = None

        self.ally_placements = ally_placements
        self.enemy_placements = enemy_placements
        self.battle_id = battle_id

        self.reload_constants_button = ReloadConstantsButton(self.manager)
        self.simulate_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (pygame.display.Info().current_w - 420, 10),
                (100, 30)
            ),
            text='Simulate',
            manager=self.manager
        )

        # Add results display box
        self.results_box = pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (pygame.display.Info().current_w - 420, 50),  # Position below simulate button
                (100, 30)
            ),
            text='',
            manager=self.manager
        )

    def update(self, time_delta: float, events: list[pygame.event.Event]) -> bool:
        """Update the sandbox scene."""
        for event in events:
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.save_button:
                        enemy_placements = get_unit_placements(TeamType.TEAM2)
                        ally_placements = get_unit_placements(TeamType.TEAM1)
                        self.save_dialog = SaveBattleDialog(
                            self.manager,
                            ally_placements=ally_placements,
                            enemy_placements=enemy_placements,
                            existing_battle_id=self.battle_id,
                        )
                    elif event.ui_element == self.return_button:
                        pygame.event.post(PreviousSceneEvent().to_event())
                        return True
                    elif event.ui_element == self.start_button:
                        pygame.event.post(
                            BattleSceneEvent(
                                ally_placements=get_unit_placements(TeamType.TEAM1),
                                enemy_placements=get_unit_placements(TeamType.TEAM2),
                                battle_id=self.battle_id,
                                sandbox_mode=True,
                            ).to_event()
                        )
                        return True
                    elif (self.save_dialog and 
                          event.ui_element == self.save_dialog.save_battle_button):
                        self.save_dialog.save_battle(is_test=False)
                        self.save_dialog.kill()
                        self.save_dialog = None
                    elif (self.save_dialog and 
                          event.ui_element == self.save_dialog.save_test_button):
                        self.save_dialog.save_battle(is_test=True)
                        self.save_dialog.kill()
                        self.save_dialog = None
                    elif (self.save_dialog and 
                          event.ui_element == self.save_dialog.cancel_button):
                        self.save_dialog.kill()
                        self.save_dialog = None
                    elif isinstance(event.ui_element, UnitCount):
                        self.create_unit_from_list(event.ui_element)
                    elif event.ui_element == self.simulate_button:
                        outcome = simulate_battle(
                            ally_placements=get_unit_placements(TeamType.TEAM1),
                            enemy_placements=get_unit_placements(TeamType.TEAM2),
                            max_duration=60,  # 60 second timeout
                        )
                        
                        # Update results box based on outcome
                        if outcome == BattleOutcome.TEAM1_VICTORY:
                            self.results_box.set_text('Team 1 Wins')
                        elif outcome == BattleOutcome.TEAM2_VICTORY:
                            self.results_box.set_text('Team 2 Wins')
                        elif outcome == BattleOutcome.TIMEOUT:
                            self.results_box.set_text('Timeout')

            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    mouse_pos = pygame.mouse.get_pos()
                    if self.selected_unit_id is None:
                        self.selected_unit_id = self.get_hovered_unit(mouse_pos)
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
                        clicked_on_unit = self.get_hovered_unit(mouse_pos)
                        if clicked_on_unit is not None:
                            esper.delete_entity(clicked_on_unit, immediate=True)


            self.reload_constants_button.handle_event(event)
            self.manager.process_events(event)

        if self.selected_unit_id is not None:
            pos = esper.component_for_entity(self.selected_unit_id, Position)
            team = esper.component_for_entity(self.selected_unit_id, Team)
            mouse_pos = pygame.mouse.get_pos()
            adjusted_mouse_pos = (mouse_pos[0] + self.camera.x, mouse_pos[1] + self.camera.y)
            x, y = adjusted_mouse_pos
            
            # Update team based on which side of the battlefield the mouse is on
            new_team = TeamType.TEAM1 if x < gc.BATTLEFIELD_WIDTH // 2 else TeamType.TEAM2
            if team.type != new_team:
                # Delete unit and recreate it with the new team
                unit_type = esper.component_for_entity(self.selected_unit_id, UnitTypeComponent).type
                esper.delete_entity(self.selected_unit_id, immediate=True)
                self.selected_unit_id = create_unit(x, y, unit_type, new_team)

            # Constrain x based on current team
            if team.type == TeamType.TEAM1:
                x = max(0, min(x, gc.BATTLEFIELD_WIDTH // 2 - gc.NO_MANS_LAND_WIDTH//2))
            else:
                x = max(gc.BATTLEFIELD_WIDTH // 2 + gc.NO_MANS_LAND_WIDTH//2, min(x, gc.BATTLEFIELD_WIDTH))
            
            y = max(0, min(y, gc.BATTLEFIELD_HEIGHT))

            # Snap to grid if shift is held
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]:
                x = round(x / gc.GRID_SIZE) * gc.GRID_SIZE
                y = round(y / gc.GRID_SIZE) * gc.GRID_SIZE

            pos.x, pos.y = x, y

            # Update range indicator
            range_indicator = esper.try_component(self.selected_unit_id, RangeIndicator)
            if range_indicator:
                range_indicator.enabled = True

        # Update stats card for hovered unit
        mouse_pos = pygame.mouse.get_pos()
        hovered_unit = self.get_hovered_unit(mouse_pos)
        if hovered_unit is not None:
            stats_card = esper.component_for_entity(hovered_unit, StatsCard)
            stats_card.active = True

        # Only update camera if no dialog is focused
        if self.save_dialog is None or not self.save_dialog.dialog.alive():
            self.camera.update(time_delta)

        self.screen.fill((0, 0, 0))
        keys = pygame.key.get_pressed()
        show_grid = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
        draw_battlefield(self.screen, self.camera, include_no_mans_land=True, show_grid=show_grid)
        esper.process(time_delta)
        self.manager.update(time_delta)
        self.manager.draw_ui(self.screen)
        return True

    def get_hovered_unit(self, mouse_pos: tuple[int, int]) -> Optional[int]:
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
        entity = create_unit(0, 0, unit_list_item.unit_type, TeamType.TEAM1)
        self.selected_unit_id = entity

    def place_unit(self) -> None:
        """Place the currently selected unit on the battlefield."""
        assert self.selected_unit_id is not None
        unit_type = esper.component_for_entity(self.selected_unit_id, UnitTypeComponent).type
        team = esper.component_for_entity(self.selected_unit_id, Team).type
        range_indicator = esper.try_component(self.selected_unit_id, RangeIndicator)
        if range_indicator:
            range_indicator.enabled = False
        
        # Create a new unit of the same type and team
        entity = create_unit(0, 0, unit_type, team)
        self.selected_unit_id = entity

