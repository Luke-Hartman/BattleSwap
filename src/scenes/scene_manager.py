import pygame
import pygame_gui

from camera import Camera
from progress_manager import ProgressManager
from scenes.select_battle import SelectBattleScene
from scenes.setup_battle import SetupBattleScene
from scenes.battle import BattleScene
from scenes.sandbox import SandboxScene
from scenes.events import (
    SETUP_BATTLE_SCENE,
    BATTLE_SCENE,
    SELECT_BATTLE_SCENE,
    SANDBOX_SCENE,
    BATTLE_EDITOR_SCENE,
)
from scenes.battle_editor import BattleEditorScene

class SceneManager:
    """Handles transitions between scenes and catches events for changing scenes."""

    def __init__(self, screen: pygame.Surface, camera: Camera, progress_manager: ProgressManager):
        self.screen = screen
        self.camera = camera
        self.progress_manager = progress_manager
        self.manager = pygame_gui.UIManager(
            (pygame.display.Info().current_w, pygame.display.Info().current_h), 
            'src/theme.json'
        )
        self.current_scene = SelectBattleScene(
            screen=self.screen,
            manager=self.manager,
            progress_manager=self.progress_manager
        )

    def update(self, time_delta: float, events: list[pygame.event.Event]) -> bool:
        """Update the current scene and handle scene transitions."""
        for event in events:
            if event.type == SETUP_BATTLE_SCENE:
                self.manager.clear_and_reset()
                self.current_scene = SetupBattleScene(
                    screen=self.screen,
                    camera=self.camera,
                    manager=self.manager,
                    battle_id=event.battle_id,
                    progress_manager=self.progress_manager,
                    potential_solution=event.potential_solution
                )
            elif event.type == BATTLE_SCENE:
                self.manager.clear_and_reset()
                self.current_scene = BattleScene(
                    screen=self.screen,
                    camera=self.camera,
                    manager=self.manager,
                    progress_manager=self.progress_manager,
                    potential_solution=event.potential_solution,
                    sandbox_mode=getattr(event, 'sandbox_mode', False)
                )
            elif event.type == SELECT_BATTLE_SCENE:
                self.manager.clear_and_reset()
                self.current_scene = SelectBattleScene(
                    screen=self.screen,
                    manager=self.manager,
                    progress_manager=self.progress_manager
                )
            elif event.type == SANDBOX_SCENE:
                self.manager.clear_and_reset()
                battle = getattr(event, 'battle', None)
                self.current_scene = SandboxScene(
                    screen=self.screen,
                    camera=self.camera,
                    manager=self.manager,
                    unit_placements=getattr(event, 'unit_placements', None),
                    enemy_placements=battle.enemies if battle else None,
                    editing_battle=battle,
                    editor_scroll=getattr(event, 'editor_scroll', 0.0)
                )
            elif event.type == BATTLE_EDITOR_SCENE:
                self.manager.clear_and_reset()
                self.current_scene = BattleEditorScene(
                    screen=self.screen,
                    manager=self.manager,
                    scroll_position=getattr(event, 'scroll_position', 0.0)
                )
        
        return self.current_scene.update(time_delta, events)
