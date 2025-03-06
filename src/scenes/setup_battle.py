"""Sandbox scene for experimenting with unit placement and battles."""
from typing import Optional, Tuple
import esper
import pygame
import pygame_gui
import shapely
import battles
from components.focus import Focus
from components.position import Position
from components.team import Team, TeamType
from components.transparent import Transparency
from components.unit_type import UnitType, UnitTypeComponent
from entities.units import create_unit
from events import CHANGE_MUSIC, PLAY_SOUND, ChangeMusicEvent, PlaySoundEvent, emit_event
from hex_grid import axial_to_world
from progress_manager import progress_manager
from scenes.scene import Scene
from game_constants import gc
from camera import Camera
from ui_components.barracks_ui import BarracksUI
from ui_components.feedback_button import FeedbackButton
from ui_components.return_button import ReturnButton
from ui_components.start_button import StartButton
from scenes.events import BattleSceneEvent, PreviousSceneEvent
from ui_components.save_battle_dialog import SaveBattleDialog
from auto_battle import BattleOutcome, simulate_battle
from ui_components.tip_box import TipBox
from voice import play_intro
from world_map_view import FillState, HexState, WorldMapView
from scene_utils import draw_grid, get_center_line, get_placement_pos, get_hovered_unit, get_unit_placements, get_legal_placement_area, has_unsaved_changes, mouse_over_ui
from ui_components.grades_panel import GradesPanel


class SetupBattleScene(Scene):
    """A scene for setting up a battle.

    Has additional options for sandbox and developer modes.
    """

    def __init__(
        self,
        screen: pygame.Surface,
        manager: pygame_gui.UIManager,
        world_map_view: Optional[WorldMapView],
        battle_id: Optional[str],
        sandbox_mode: bool = False,
        developer_mode: bool = False,
    ):
        """Initialize the sandbox scene.
        
        Args:
            screen: The pygame surface to render to.
            manager: The pygame_gui manager for the scene.
            world_map_view: The world map view for the scene.
            battle_id: Which battle is focused.
            sandbox_mode: In sandbox mode, there are no restrictions on unit placement.
            developer_mode: In developer mode, there are additional buttons such as saving
                and simulating the battle.
        """
        emit_event(CHANGE_MUSIC, event=ChangeMusicEvent(
            filename="Main Theme.wav",
        ))
        self.screen = screen
        self.manager = manager
        self._selected_unit_type: Optional[UnitType] = None
        if world_map_view is None:
            battle = battles.Battle(
                id="sandbox",
                tip=["A customizable battle for experimenting"],
                hex_coords=(0, 0),
                allies=[],
                enemies=[],
                is_test=True,
            )
            world_map_view = WorldMapView(
                screen=self.screen,
                manager=self.manager,
                battles=[battle],
                camera=Camera(),
            )
            if battle_id is not None:
                raise ValueError("Battle ID must be None if world_map_view is None")
            battle_id = "sandbox"
        else:
            if battle_id is None:
                raise ValueError("Battle ID must be provided if world_map_view is not None")
            battle = world_map_view.battles[battle_id]
        self.world_map_view = world_map_view
        self.camera = world_map_view.camera
        self.battle_id = battle_id
        self.battle = battle
        self.sandbox_mode = sandbox_mode
        self.developer_mode = developer_mode
        
        if self.sandbox_mode:
            # Set unfocused states for all battles except the focused one
            unfocused_states = {
                other_battle.hex_coords: HexState(fill=FillState.UNFOCUSED) if other_battle.hex_coords != battle.hex_coords else HexState(fill=FillState.NORMAL)
                for other_battle in self.world_map_view.battles.values()
            }
        else:
            # Set unfocused for all solved battles except the focused one
            # Set fogged for all unsolved battles
            unfocused_states = {}
            for other_battle in self.world_map_view.battles.values():
                if other_battle.hex_coords == battle.hex_coords:
                    unfocused_states[other_battle.hex_coords] = HexState(fill=FillState.NORMAL)
                elif other_battle.hex_coords in progress_manager.solutions:
                    unfocused_states[other_battle.hex_coords] = HexState(fill=FillState.UNFOCUSED)
                else:
                    unfocused_states[other_battle.hex_coords] = HexState(fill=FillState.FOGGED)
        self.world_map_view.reset_hex_states()
        self.world_map_view.update_hex_state(unfocused_states)

        self.return_button = ReturnButton(self.manager)
        self.start_button = StartButton(self.manager)
        self.feedback_button = FeedbackButton(self.manager)
        self.tip_box = TipBox(self.manager, battle)

        self.barracks = BarracksUI(
            self.manager,
            starting_units={} if self.sandbox_mode else progress_manager.available_units(battle),
            interactive=True,
            sandbox_mode=self.sandbox_mode,
            current_battle=battle,
        )

        # Create grades panel to the right of barracks, aligned at the bottom
        barracks_bottom = self.barracks.rect.bottom
        self.grades_panel = GradesPanel(
            relative_rect=pygame.Rect(
                (pygame.display.Info().current_w - 295, barracks_bottom - 100),
                (215, 100)
            ),
            manager=self.manager,
            current_battle=battle,
            is_setup_mode=not self.battle.is_test,  # Only use setup mode for non-test battles
        ) if not self.sandbox_mode else None

        self.selected_partial_unit: Optional[int] = None

        self.save_dialog: Optional[SaveBattleDialog] = None
        if self.developer_mode:
            self.save_button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (pygame.display.Info().current_w - 310, 10),
                    (100, 30)
                ),
                text='Save Battle',
                manager=self.manager
            )
            self.simulate_button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect(
                    (pygame.display.Info().current_w - 420, 10),
                    (100, 30)
                ),
                text='Simulate',
                manager=self.manager
            )
            self.results_box = pygame_gui.elements.UILabel(
                relative_rect=pygame.Rect(
                    (pygame.display.Info().current_w - 420, 50),  # Position below simulate button
                    (100, 30)
                ),
                text='',
                manager=self.manager
            )
        else:
            self.save_button = None
            self.simulate_button = None
            self.results_box = None
        
        self.confirmation_dialog: Optional[pygame_gui.windows.UIConfirmationDialog] = None
    
    @property
    def selected_unit_type(self) -> Optional[UnitType]:
        """Get the currently selected unit type."""
        return self._selected_unit_type

    def set_selected_unit_type(
        self,
        value: Optional[UnitType],
        placement_team: TeamType,
    ) -> None:
        """Set the currently selected unit type."""
        self._selected_unit_type = value
        self.barracks.select_unit_type(value)
        if self.selected_partial_unit is not None:
            esper.delete_entity(self.selected_partial_unit)
        if value is None:
            self.selected_partial_unit = None
            return
        self.selected_partial_unit = create_unit(
            x=0,
            y=0,
            unit_type=value,
            team=placement_team,
        )
        esper.remove_component(self.selected_partial_unit, UnitTypeComponent)
        esper.add_component(self.selected_partial_unit, Transparency(alpha=128))
    
    def create_unit_of_selected_type(self, placement_pos: Tuple[int, int], team: TeamType) -> None:
        """Create a unit of the selected type."""
        assert self.sandbox_mode or team == TeamType.TEAM1
        self.world_map_view.add_unit(
            self.battle_id,
            self.selected_unit_type,
            placement_pos,
            team,
        )
        self.barracks.remove_unit(self.selected_unit_type)
        if self.barracks.units[self.selected_unit_type] == 0:
            self.set_selected_unit_type(None, TeamType.TEAM1)
        if self.grades_panel is not None:
            self.grades_panel.update_battle(self.battle)
    
    def remove_unit(self, unit_id: int) -> None:
        """Delete a unit of the selected type."""
        assert self.sandbox_mode or esper.component_for_entity(unit_id, Team).type == TeamType.TEAM1
        self.world_map_view.remove_unit(
            self.battle_id,
            unit_id,
        )
        unit_type = esper.component_for_entity(unit_id, UnitTypeComponent).type
        self.barracks.add_unit(unit_type)
        if self.grades_panel is not None:
            self.grades_panel.update_battle(self.battle)

    def show_exit_confirmation(self) -> None:
        """Show confirmation dialog for exiting with unsaved changes."""
        self.confirmation_dialog = pygame_gui.windows.UIConfirmationDialog(
            rect=pygame.Rect((pygame.display.Info().current_w/2 - 150, pygame.display.Info().current_h/2 - 100), (300, 200)),
            manager=self.manager,
            window_title="Unsaved Changes",
            action_long_desc="You have unsaved changes. Are you sure you want to exit?" if not self.sandbox_mode else "Are you sure you want to exit?",
            action_short_name="Exit",
            blocking=True
        )

    def handle_return(self) -> None:
        """Handle return button press or escape key."""
        if (
            not self.sandbox_mode and has_unsaved_changes(self.battle)
            or self.sandbox_mode and (
                len(get_unit_placements(TeamType.TEAM1, self.battle.hex_coords)) > 0
                or len(get_unit_placements(TeamType.TEAM2, self.battle.hex_coords)) > 0
            )
        ):
            self.show_exit_confirmation()
        else:
            self.world_map_view.move_camera_above_battle(self.battle_id)
            self.world_map_view.rebuild(battles=progress_manager.get_battles_including_solutions())
            pygame.event.post(PreviousSceneEvent().to_event())

    def update(self, time_delta: float, events: list[pygame.event.Event]) -> bool:
        """Update the sandbox scene."""
        esper.switch_world(self.battle_id)
        keys = pygame.key.get_pressed()
        show_grid = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]

        # Get battle hex coordinates
        battle = self.world_map_view.battles[self.battle_id]
        if battle.hex_coords is None:
            raise ValueError(f"Battle {self.battle_id} has no hex coordinates")
        battle_coords = battle.hex_coords
        world_x, _ = axial_to_world(*battle_coords)

        hovered_unit = get_hovered_unit(self.camera)
        hovered_team = esper.component_for_entity(hovered_unit, Team).type if hovered_unit is not None else None
        placement_pos = get_placement_pos(
            self.battle_id,
            battle_coords,
            self.camera,
            snap_to_grid=show_grid,
            required_team=None if self.sandbox_mode else TeamType.TEAM1,
        )
        placement_team = TeamType.TEAM1 if placement_pos[0] < world_x else TeamType.TEAM2

        # Update preview for selected unit
        if self.selected_partial_unit is not None:
            team = esper.component_for_entity(self.selected_partial_unit, Team)
            if team.type != placement_team:
                # If the partial unit is no longer on the side it was created on, recreate it
                self.set_selected_unit_type(self.selected_unit_type, placement_team)
            position = esper.component_for_entity(self.selected_partial_unit, Position)
            position.x, position.y = placement_pos
            esper.add_component(self.selected_partial_unit, Focus())

        for event in events:
            if event.type == pygame.QUIT:
                return False

            if self.handle_confirmation_dialog_keys(event):
                continue

            self.handle_escape(event)

            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    for unit_count in self.barracks.unit_list_items:
                        if event.ui_element == unit_count.button:
                            play_intro(unit_count.unit_type)
                            self.set_selected_unit_type(unit_count.unit_type, placement_team)
                            break
                    assert event.ui_element is not None
                    if event.ui_element == self.save_button:
                        enemy_placements = get_unit_placements(TeamType.TEAM2, battle_coords)
                        ally_placements = get_unit_placements(TeamType.TEAM1, battle_coords)
                        self.save_dialog = SaveBattleDialog(
                            self.manager,
                            ally_placements=ally_placements,
                            enemy_placements=enemy_placements,
                            existing_battle_id=self.battle_id,
                        )
                    elif event.ui_element == self.return_button:
                        self.handle_return()
                        return super().update(time_delta, events)
                    elif event.ui_element == self.start_button:
                        pygame.event.post(
                            BattleSceneEvent(
                                world_map_view=self.world_map_view,
                                battle_id=self.battle_id,
                                sandbox_mode=self.sandbox_mode,
                            ).to_event()
                        )
                        return super().update(time_delta, events)
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
                    elif event.ui_element == self.simulate_button:
                        outcome = simulate_battle(
                            ally_placements=get_unit_placements(TeamType.TEAM1, battle_coords),
                            enemy_placements=get_unit_placements(TeamType.TEAM2, battle_coords),
                            max_duration=60,  # 60 second timeout
                        )
                        
                        # Update results box based on outcome
                        if outcome == BattleOutcome.TEAM1_VICTORY:
                            self.results_box.set_text('Team 1 Wins')
                        elif outcome == BattleOutcome.TEAM2_VICTORY:
                            self.results_box.set_text('Team 2 Wins')
                        elif outcome == BattleOutcome.TIMEOUT:
                            self.results_box.set_text('Timeout')
                elif event.user_type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED:
                    if self.confirmation_dialog is not None and event.ui_element == self.confirmation_dialog:
                        self.world_map_view.move_camera_above_battle(self.battle_id)
                        self.world_map_view.rebuild(battles=progress_manager.get_battles_including_solutions())
                        pygame.event.post(PreviousSceneEvent().to_event())
                        return super().update(time_delta, events)

            if event.type == pygame.MOUSEBUTTONDOWN and not mouse_over_ui(self.manager):
                if event.button == pygame.BUTTON_LEFT:
                    if self.selected_unit_type is None:
                        if hovered_unit is not None and (self.sandbox_mode or hovered_team == TeamType.TEAM1):
                            self.set_selected_unit_type(esper.component_for_entity(hovered_unit, UnitTypeComponent).type, placement_team)
                            self.remove_unit(hovered_unit)
                            hovered_unit = None
                    else:
                        self.create_unit_of_selected_type(
                            placement_pos,
                            placement_team,
                        )
                elif event.button == pygame.BUTTON_RIGHT:
                    if self.selected_unit_type is not None:
                        self.set_selected_unit_type(None, placement_team)
                        emit_event(PLAY_SOUND, event=PlaySoundEvent(
                            filename="unit_picked_up.wav",
                            volume=0.5,
                        ))
                    else:
                        if hovered_unit is not None and (self.sandbox_mode or hovered_team == TeamType.TEAM1):
                            self.remove_unit(hovered_unit)
                            hovered_unit = None

            self.camera.process_event(event)
            self.manager.process_events(event)
            self.feedback_button.handle_event(event)
            self.barracks.handle_event(event)
            if self.grades_panel is not None:
                self.grades_panel.handle_event(event)

        # Only update camera if no dialog is focused
        if self.save_dialog is None or not self.save_dialog.dialog.alive():
            self.camera.update(time_delta)

        self.screen.fill(gc.MAP_BACKGROUND_COLOR)
        # Update and draw the world map view
        self.world_map_view.draw_map()
        # Draw the grid lines if shift is held
        if show_grid:
            draw_grid(self.screen, self.camera, battle_coords)

        # Draw the legal placement area
        if self.selected_unit_type is not None:
            legal_area = get_legal_placement_area(
                self.battle_id,
                battle_coords,
                required_team=None if self.sandbox_mode else TeamType.TEAM1,
                include_units=False,
            )
            for polygon in legal_area.geoms if isinstance(legal_area, shapely.MultiPolygon) else [legal_area]:
                pygame.draw.lines(self.screen, (175, 175, 175), False, 
                    [self.camera.world_to_screen(x, y) for x, y in polygon.exterior.coords], 
                    width=2)
        # Draw white line down the middle of the hexagon
        center_line = get_center_line(battle_coords)
        pygame.draw.lines(
            self.screen,
            gc.MAP_BATTLEFIELD_EDGE_COLOR,
            False,
            [self.camera.world_to_screen(x, y) for x, y in center_line.coords],
            width=2,
        )

        self.world_map_view.update_battles(time_delta)
        self.barracks.select_unit_type(self.selected_unit_type)
        self.manager.update(time_delta)
        self.manager.draw_ui(self.screen)
        return super().update(time_delta, events)



