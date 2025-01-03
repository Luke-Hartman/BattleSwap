from components.team import TeamType
from game_constants import gc
import pygame
import pygame_gui
from auto_battle import AutoBattle, BattleOutcome
from events import CHANGE_MUSIC, ChangeMusicEvent, emit_event
from scene_utils import get_unit_placements, use_world
from scenes.scene import Scene
from scenes.events import PreviousSceneEvent
from world_map_view import WorldMapView
from ui_components.return_button import ReturnButton
from progress_manager import progress_manager, Solution

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
        self.victory_panel = None
        self.defeat_panel = None
        self.outcome_time = None
        self.panel_delay = 0.25  # Delay in seconds before showing panel

        with use_world(self.battle_id):
            self.auto_battle = AutoBattle(
                max_duration=float('inf'),
                hex_coords=self.battle.hex_coords
            )

    def create_victory_panel(self) -> None:
        """Create the victory panel with large text and buttons."""
        panel_width = 400
        panel_height = 200  # Reduced height since buttons are now side by side
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
                (panel_width, 100)
            ),
            text="Victory!",
            manager=self.manager,
            container=self.victory_panel,
            object_id=pygame_gui.core.ObjectID(
                class_id="@title_label",
                object_id="#title_label"
            )
        )

        button_width = 160  # Slightly narrower to fit side by side
        button_height = 40
        button_spacing = 20
        start_y = 140

        # Calculate x positions for the buttons
        left_button_x = (panel_width - (2 * button_width + button_spacing)) // 2

        # Save and continue button (left)
        self.save_continue_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (left_button_x, start_y),
                (button_width, button_height)
            ),
            text="Save and Continue",
            manager=self.manager,
            container=self.victory_panel
        )

        # Edit button (right)
        self.edit_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                (left_button_x + button_width + button_spacing, start_y),
                (button_width, button_height)
            ),
            text="Edit Solution",
            manager=self.manager,
            container=self.victory_panel
        )

    def create_defeat_panel(self) -> None:
        """Create the defeat panel with large text and button."""
        panel_width = 400
        panel_height = 200
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
                (panel_width, 100)
            ),
            text="Defeated!",
            manager=self.manager,
            container=self.defeat_panel,
            object_id=pygame_gui.core.ObjectID(
                class_id="@title_label",
                object_id="#title_label"
            )
        )

        # Try again button
        button_width = 200
        button_height = 40
        self.try_again_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect(
                ((panel_width - button_width) // 2, 140),
                (button_width, button_height)
            ),
            text="Try Again",
            manager=self.manager,
            container=self.defeat_panel
        )

    def update(self, time_delta: float, events: list[pygame.event.Event]) -> bool:
        """Update the battle scene."""
        for event in events:
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.return_button:
                        self.world_map_view.rebuild(self.world_map_view.battles.values())
                        pygame.event.post(PreviousSceneEvent().to_event())
                        return super().update(time_delta, events)
                    elif hasattr(self, 'save_continue_button') and event.ui_element == self.save_continue_button:
                        progress_manager.save_solution(Solution(hex_coords=self.battle.hex_coords, unit_placements=self.battle.allies))
                        self.world_map_view.rebuild(progress_manager.get_battles_including_solutions())
                        self.world_map_view.move_camera_above_battle(self.battle_id)
                        pygame.event.post(PreviousSceneEvent(n=2).to_event())
                        return super().update(time_delta, events)
                    elif hasattr(self, 'edit_button') and event.ui_element == self.edit_button:
                        self.world_map_view.rebuild(self.world_map_view.battles.values())
                        pygame.event.post(PreviousSceneEvent().to_event())
                        return super().update(time_delta, events)
                    elif hasattr(self, 'try_again_button') and event.ui_element == self.try_again_button:
                        self.world_map_view.rebuild(self.world_map_view.battles.values())
                        pygame.event.post(PreviousSceneEvent().to_event())
                        return super().update(time_delta, events)

            self.world_map_view.camera.process_event(event)
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
        return super().update(time_delta, events)
