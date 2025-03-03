from components.team import TeamType
from game_constants import gc
import pygame
import pygame_gui
from auto_battle import AutoBattle, BattleOutcome
from events import CHANGE_MUSIC, ChangeMusicEvent, emit_event
from scene_utils import use_world, has_unsaved_changes
from scenes.scene import Scene
from scenes.events import PreviousSceneEvent
from world_map_view import WorldMapView
from ui_components.return_button import ReturnButton
from progress_manager import progress_manager, Solution, calculate_points_for_units
from ui_components.time_controls import TimeControls
from time_manager import time_manager

class BattleScene(Scene):
    """The scene for the battle."""

    def __init__(
        self,
        screen: pygame.Surface,
        manager: pygame_gui.UIManager,
        world_map_view: WorldMapView,
        battle_id: str,
        sandbox_mode: bool = False
    ):
        """Initialize the battle scene.

        Args:
            screen: The pygame surface to render to.
            manager: The pygame_gui UI manager.
            progress_manager: The progress manager.
            world_map_view: The world map view.
            battle_id: The id of the battle to load.
            sandbox_mode: Whether this battle is in sandbox mode.
        """
        emit_event(CHANGE_MUSIC, event=ChangeMusicEvent(
            filename="Battle Theme.wav",
        ))
        self.screen = screen
        self.manager = manager
        self.world_map_view = world_map_view
        self.battle_id = battle_id
        self.battle = self.world_map_view.battles[self.battle_id]
        self.sandbox_mode = sandbox_mode
        self.return_button = ReturnButton(self.manager)
        self.time_controls = TimeControls(self.manager)
        self.victory_panel = None
        self.defeat_panel = None
        self.outcome_time = None
        self.panel_delay = 0.25  # Delay in seconds before showing panel
        self.confirmation_dialog = None

        self.world_map_view.rebuild(self.world_map_view.battles.values())

        with use_world(self.battle_id):
            self.auto_battle = AutoBattle(
                max_duration=float('inf'),
                hex_coords=self.battle.hex_coords
            )

    def handle_return(self, n: int = 1) -> None:
        """Handle return button press or escape key."""
        self.world_map_view.move_camera_above_battle(self.battle_id)
        self.world_map_view.rebuild(self.world_map_view.battles.values())
        pygame.event.post(PreviousSceneEvent(n=n).to_event())

    def create_victory_panel(self) -> None:
        """Create the victory panel with large text and buttons."""
        panel_width = 230
        panel_height = 200
        screen_width = pygame.display.Info().current_w
        screen_height = pygame.display.Info().current_h

        self.victory_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(
                ((screen_width - panel_width) // 2, (screen_height - panel_height) // 2),
                (panel_width, panel_height)
            ),
            manager=self.manager
        )

        # Victory text
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (0, 20),
                (panel_width, 60)
            ),
            text="Victory!",
            manager=self.manager,
            container=self.victory_panel,
            object_id=pygame_gui.core.ObjectID(
                class_id="@title_label",
                object_id="#title_label"
            )
        )

        button_width = 100
        button_height = 40
        button_spacing = 10
        start_y = 100

        # Calculate positions for the wider save button
        wide_button_width = button_width * 2 + button_spacing
        save_button_x = (panel_width - wide_button_width) // 2

        # Save button (top, wider)
        has_changes = has_unsaved_changes(self.battle)
        save_text = "Save" if has_changes else "No changes"
        
        # Prepare tooltip with score information
        current_points = calculate_points_for_units(self.battle.allies or [])
        current_grade = self.battle.grades.get_grade(current_points) if self.battle.grades else None
        
        if self.battle.hex_coords in progress_manager.solutions:
            previous_solution = progress_manager.solutions[self.battle.hex_coords]
            previous_points = calculate_points_for_units(previous_solution.unit_placements)
            previous_grade = self.battle.grades.get_grade(previous_points) if self.battle.grades else None
            tooltip = f"{previous_points} ({previous_grade}) to {current_points} ({current_grade})"
        else:
            tooltip = f"{current_points} ({current_grade})"

        self.save_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (save_button_x, start_y),
                (wide_button_width, button_height)
            ),
            text=save_text,
            manager=self.manager,
            container=self.victory_panel,
            tool_tip_text=tooltip,
        )
        self.save_button.tool_tip_delay = 0.1
        if not has_changes:
            self.save_button.disable()

        # Calculate x positions for the two bottom buttons
        start_y += button_height + button_spacing
        left_button_x = (panel_width - (2 * button_width + button_spacing)) // 2

        # Improve button (bottom left)
        self.improve_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (left_button_x, start_y),
                (button_width, button_height)
            ),
            text="Improve",
            manager=self.manager,
            container=self.victory_panel
        )

        # Continue button (bottom right)
        self.continue_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (left_button_x + button_width + button_spacing, start_y),
                (button_width, button_height)
            ),
            text="Continue",
            manager=self.manager,
            container=self.victory_panel
        )
        if self.battle.hex_coords not in progress_manager.solutions:
            self.continue_button.disable()

    def create_defeat_panel(self) -> None:
        """Create the defeat panel with large text and buttons."""
        panel_width = 250
        panel_height = 150
        screen_width = pygame.display.Info().current_w
        screen_height = pygame.display.Info().current_h
        
        self.defeat_panel = pygame_gui.elements.UIPanel(
            relative_rect=pygame.Rect(
                ((screen_width - panel_width) // 2, (screen_height - panel_height) // 2),
                (panel_width, panel_height)
            ),
            manager=self.manager
        )

        # Defeat text
        pygame_gui.elements.UILabel(
            relative_rect=pygame.Rect(
                (0, 20),
                (panel_width, 60)
            ),
            text="Defeated!",
            manager=self.manager,
            container=self.defeat_panel,
            object_id=pygame_gui.core.ObjectID(
                class_id="@title_label",
                object_id="#title_label"
            )
        )

        button_width = 100
        button_height = 40
        button_spacing = 20
        start_y = 100

        # Calculate x positions for the two buttons
        total_width = 2 * button_width + button_spacing
        left_button_x = (panel_width - total_width) // 2

        # Try Again button (left)
        self.try_again_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (left_button_x, start_y),
                (button_width, button_height)
            ),
            text="Try Again",
            manager=self.manager,
            container=self.defeat_panel
        )

        # Leave button (right)
        self.leave_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (left_button_x + button_width + button_spacing, start_y),
                (button_width, button_height)
            ),
            text="Leave",
            manager=self.manager,
            container=self.defeat_panel
        )

    def show_continue_confirmation(self) -> None:
        """Show confirmation dialog for continuing with unsaved changes."""
        self.confirmation_dialog = pygame_gui.windows.UIConfirmationDialog(
            rect=pygame.Rect((pygame.display.Info().current_w/2 - 150, pygame.display.Info().current_h/2 - 100), (300, 200)),
            manager=self.manager,
            window_title="Confirmation",
            action_long_desc="You have unsaved changes. Are you sure you want to continue?",
            action_short_name="Continue",
            blocking=True
        )

    def render_paused_text(self) -> None:
        """Render giant PAUSED text across the screen when the game is paused."""
        if time_manager._is_paused:
            # Create semi-transparent overlay
            overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))  # Semi-transparent black
            self.screen.blit(overlay, (0, 0))
            
            # Use pygame's default font system
            pygame.font.init()
            large_font = pygame.font.SysFont('Arial', 72, bold=True)
            
            # Render PAUSED text
            paused_text = large_font.render("PAUSED", True, (255, 255, 255))
            text_rect = paused_text.get_rect(center=(self.screen.get_width() // 2, self.screen.get_height() // 2))
            
            # Add shadow effect for better visibility
            shadow_text = large_font.render("PAUSED", True, (0, 0, 0))
            shadow_rect = shadow_text.get_rect(center=(text_rect.centerx + 3, text_rect.centery + 3))
            self.screen.blit(shadow_text, shadow_rect)
            
            # Draw the main text
            self.screen.blit(paused_text, text_rect)

    def update(self, time_delta: float, events: list[pygame.event.Event]) -> bool:
        """Update the battle scene."""
        for event in events:
            if event.type == pygame.QUIT:
                return False
            
            if self.handle_confirmation_dialog_keys(event):
                continue

            self.handle_escape(event)
                
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.return_button:
                        self.handle_return()
                        return super().update(time_delta, events)
                    elif hasattr(self, 'improve_button') and event.ui_element == self.improve_button:
                        self.world_map_view.rebuild(self.world_map_view.battles.values())
                        pygame.event.post(PreviousSceneEvent().to_event())
                        return super().update(time_delta, events)
                    elif hasattr(self, 'save_button') and event.ui_element == self.save_button:
                        progress_manager.save_solution(Solution(hex_coords=self.battle.hex_coords, unit_placements=self.battle.allies))
                        # Recreate the victory panel to update the save button state
                        self.victory_panel.kill()
                        self.create_victory_panel()
                    elif hasattr(self, 'continue_button') and event.ui_element == self.continue_button:
                        if has_unsaved_changes(self.battle):
                            self.show_continue_confirmation()
                        else:
                            self.world_map_view.rebuild(progress_manager.get_battles_including_solutions())
                            self.world_map_view.move_camera_above_battle(self.battle_id)
                            pygame.event.post(PreviousSceneEvent(n=2).to_event())
                            return super().update(time_delta, events)
                    elif hasattr(self, 'try_again_button') and event.ui_element == self.try_again_button:
                        self.world_map_view.rebuild(self.world_map_view.battles.values())
                        pygame.event.post(PreviousSceneEvent().to_event())
                        return super().update(time_delta, events)
                    elif hasattr(self, 'leave_button') and event.ui_element == self.leave_button:
                        self.world_map_view.rebuild(progress_manager.get_battles_including_solutions())
                        self.handle_return(n=2)
                        return super().update(time_delta, events)

                elif event.user_type == pygame_gui.UI_CONFIRMATION_DIALOG_CONFIRMED:
                    if self.confirmation_dialog is not None and event.ui_element == self.confirmation_dialog:
                        self.world_map_view.rebuild(progress_manager.get_battles_including_solutions())
                        self.handle_return(n=2)
                        return super().update(time_delta, events)

            self.world_map_view.camera.process_event(event)
            self.time_controls.handle_event(event)
            self.manager.process_events(event)

        self.screen.fill(gc.MAP_BACKGROUND_COLOR)
        self.world_map_view.camera.update(time_delta)
        self.world_map_view.draw_map()
        self.world_map_view.update_battles(time_delta)
        with use_world(self.battle_id):
            self.auto_battle.update(time_delta)
        battle_outcome = self.auto_battle.battle_outcome
        
        # Track when we first get a victory/defeat outcome
        if battle_outcome in (BattleOutcome.TEAM1_VICTORY, BattleOutcome.TEAM2_VICTORY) and not self.sandbox_mode:
            if self.outcome_time is None:
                self.outcome_time = 0.0
            else:
                self.outcome_time += time_delta
                
            # Create panel after delay
            if self.outcome_time >= self.panel_delay:
                if battle_outcome == BattleOutcome.TEAM1_VICTORY and self.victory_panel is None:
                    self.return_button.hide()
                    self.create_victory_panel()
                elif battle_outcome == BattleOutcome.TEAM2_VICTORY and self.defeat_panel is None:
                    self.return_button.hide()
                    self.create_defeat_panel()

        self.manager.update(time_delta)
        self.manager.draw_ui(self.screen)
        
        # Render PAUSED text if the game is paused
        self.render_paused_text()
        
        return super().update(time_delta, events)
