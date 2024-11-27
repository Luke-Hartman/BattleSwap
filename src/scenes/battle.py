from typing import List, Tuple, Optional
import esper
import pygame
import pygame_gui
from auto_battle import AutoBattle, BattleOutcome
from components.unit_type import UnitType
from processors.rendering_processor import RenderingProcessor, draw_battlefield
from scenes.scene import Scene
from scenes.events import PreviousSceneEvent, SandboxSceneEvent, SelectBattleSceneEvent, SetupBattleSceneEvent
from camera import Camera
from ui_components.return_button import ReturnButton
from progress_manager import ProgressManager, Solution

class BattleScene(Scene):
    """The scene for the battle."""

    def __init__(
        self,
        screen: pygame.Surface,
        camera: Camera,
        manager: pygame_gui.UIManager,
        progress_manager: ProgressManager,
        ally_placements: List[Tuple[UnitType, Tuple[int, int]]],
        enemy_placements: List[Tuple[UnitType, Tuple[int, int]]],
        battle_id: Optional[str] = None,
        sandbox_mode: bool = False,
        editor_scroll: float = 0.0
    ):
        """Initialize the battle scene.
        
        Args:
            screen: The pygame surface to render to.
            camera: The camera object controlling the view.
            manager: The pygame_gui UI manager.
            progress_manager: The progress manager.
            ally_placements: The placements of the ally units.
            enemy_placements: The placements of the enemy units.
            battle_id: The id of the battle to load.
            sandbox_mode: Whether this battle is in sandbox mode.
            editor_scroll: The scroll position of the battle editor.
        """
        self.screen = screen
        self.camera = camera
        self.manager = manager
        self.progress_manager = progress_manager
        self.ally_placements = ally_placements
        self.enemy_placements = enemy_placements
        self.battle_id = battle_id
        self.sandbox_mode = sandbox_mode
        self.editor_scroll = editor_scroll
        self.auto_battle = AutoBattle(
            ally_placements=self.ally_placements,
            enemy_placements=self.enemy_placements,
            max_duration=float('inf')
        )
        rendering_processor = RenderingProcessor(
            screen=self.screen,
            camera=self.camera
        )
        esper.add_processor(rendering_processor)
        self.return_button = ReturnButton(self.manager)
        self.restart_button = pygame_gui.elements.UIButton(
            relative_rect=pygame.Rect((pygame.display.Info().current_w - 210, 10), (100, 30)),
            text='Restart',
            manager=self.manager
        )
        self.victory_button = None
        self.victory_achieved = False

    def update(self, time_delta: float, events: list[pygame.event.Event]) -> bool:
        """Update the battle scene."""
        for event in events:
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.USEREVENT:
                if event.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.return_button:
                        pygame.event.post(PreviousSceneEvent().to_event())
                        return True
                    elif event.ui_element == self.victory_button:
                        self.progress_manager.save_solution(Solution(self.battle_id, self.ally_placements))
                        pygame.event.post(SelectBattleSceneEvent().to_event())
                        return True
                    elif event.ui_element == self.restart_button:
                        if self.sandbox_mode:
                            pygame.event.post(
                                SandboxSceneEvent(
                                    ally_placements=self.ally_placements,
                                    enemy_placements=self.enemy_placements,
                                    battle_id=self.battle_id,
                                    editor_scroll=self.editor_scroll
                                ).to_event()
                            )
                        else:
                            pygame.event.post(
                                SetupBattleSceneEvent(
                                    ally_placements=self.ally_placements,
                                    enemy_placements=self.enemy_placements,
                                    battle_id=self.battle_id
                                ).to_event()
                            )
                        return True
            
            self.manager.process_events(event)

        self.camera.update(time_delta)
        self.screen.fill((0, 0, 0))
        draw_battlefield(self.screen, self.camera, include_no_mans_land=True)
        esper.process(time_delta)
        battle_outcome = self.auto_battle.update(time_delta)
        if battle_outcome == BattleOutcome.TEAM1_VICTORY and not self.victory_achieved and not self.sandbox_mode:
            self.victory_achieved = True
            self.victory_button = pygame_gui.elements.UIButton(
                relative_rect=pygame.Rect((pygame.display.Info().current_w//2 - 100, pygame.display.Info().current_h - 75), (200, 50)),
                text='Victory!',
                manager=self.manager
            )
        self.manager.update(time_delta)
        self.manager.draw_ui(self.screen)
        return True
