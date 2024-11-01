import pygame

from camera import Camera
from progress_manager import ProgressManager
from scenes.select_battle import SelectBattleScene
from scenes.setup_battle import SetupBattleScene
from scenes.battle import BattleScene
from scenes.events import SETUP_BATTLE_SCENE, START_BATTLE, RETURN_TO_SELECT_BATTLE

class SceneManager:
    """Handles transitions between scenes and catches events for changing scenes."""

    def __init__(self, screen: pygame.Surface, camera: Camera, progress_manager: ProgressManager):
        self.screen = screen
        self.camera = camera
        self.progress_manager = progress_manager
        self.current_scene = SelectBattleScene(screen, progress_manager)

    def update(self, time_delta: float, events: list[pygame.event.Event]) -> bool:
        """Update the current scene and handle scene transitions."""
        for event in events:
            if event.type == SETUP_BATTLE_SCENE:
                self.current_scene = SetupBattleScene(
                    screen=self.screen,
                    camera=self.camera,
                    battle=event.battle,
                    progress_manager=self.progress_manager,
                    potential_solution=event.potential_solution
                )
            elif event.type == START_BATTLE:
                self.current_scene = BattleScene(
                    self.screen, self.camera, self.progress_manager, event.potential_solution
                )
            elif event.type == RETURN_TO_SELECT_BATTLE:
                self.current_scene = SelectBattleScene(self.screen, self.progress_manager)
        
        return self.current_scene.update(time_delta, events)
