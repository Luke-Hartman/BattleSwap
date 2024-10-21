import pygame

from scenes.select_battle import SelectBattleScene
from scenes.setup_battle import SetupBattleScene
from scenes.battle import BattleScene
from scenes.events import SETUP_BATTLE_SCENE, START_BATTLE, RETURN_TO_SELECT_BATTLE

class SceneManager:
    """Handles transitions between scenes and catches events for changing scenes."""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.current_scene = SelectBattleScene(screen)

    def update(self, time_delta: float, events: list[pygame.event.Event]) -> bool:
        """Update the current scene and handle scene transitions."""
        for event in events:
            if event.type == SETUP_BATTLE_SCENE:
                self.current_scene = SetupBattleScene(self.screen, event.battle)
            elif event.type == START_BATTLE:
                self.current_scene = BattleScene(self.screen)
            elif event.type == RETURN_TO_SELECT_BATTLE:
                self.current_scene = SelectBattleScene(self.screen)
        
        return self.current_scene.update(time_delta, events)
