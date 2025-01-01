from components.team import TeamType
from game_constants import gc
import pygame
import pygame_gui
from auto_battle import AutoBattle, BattleOutcome
from events import CHANGE_MUSIC, ChangeMusicEvent, emit_event
from scene_utils import get_unit_placements, use_world
from scenes.scene import Scene
from scenes.events import PreviousSceneEvent, SandboxSceneEvent, SelectBattleSceneEvent, SetupBattleSceneEvent
from world_map_view import WorldMapView
from ui_components.return_button import ReturnButton
from progress_manager import ProgressManager, Solution

class BattleScene(Scene):
    """The scene for the battle."""

    def __init__(
        self,
        screen: pygame.Surface,
        manager: pygame_gui.UIManager,
        progress_manager: ProgressManager,
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
        self.progress_manager = progress_manager
        self.world_map_view = world_map_view
        self.battle_id = battle_id
        self.battle = self.world_map_view.battles[self.battle_id]
        self.sandbox_mode = sandbox_mode
        self.return_button = ReturnButton(self.manager)
        self.victory_button = None
        self.victory_achieved = False
        with use_world(self.battle_id):
            self.auto_battle = AutoBattle(
                max_duration=float('inf'),
                hex_coords=self.battle.hex_coords
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
                    elif event.ui_element == self.victory_button:
                        self.progress_manager.save_solution(Solution(self.battle.hex_coords, self.battle.allies))
                        self.world_map_view.rebuild(self.progress_manager.get_battles_including_solutions())
                        self.world_map_view.move_camera_above_battle(self.battle_id)
                        pygame.event.post(PreviousSceneEvent(n=2).to_event())
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
        if battle_outcome == BattleOutcome.TEAM1_VICTORY and not self.victory_achieved and not self.sandbox_mode:
            self.victory_achieved = True
            self.victory_button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((pygame.display.Info().current_w//2 - 100, pygame.display.Info().current_h - 75), (200, 50)),
                text='Victory!',
                manager=self.manager
            )
        self.manager.update(time_delta)
        self.manager.draw_ui(self.screen)
        return super().update(time_delta, events)
