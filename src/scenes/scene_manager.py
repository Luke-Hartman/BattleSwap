import pygame

from scenes.select_battle import SelectBattleScene
from scenes.battle import BattleScene
from scenes.events import CHANGE_TO_BATTLE_SCENE

class SceneManager:
    """Handles transitions between scenes and catches events for changing scenes."""

    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.current_scene = SelectBattleScene(screen)

    def update(self, time_delta: float, events: list[pygame.event.Event]) -> bool:
        """Update the current scene and handle scene transitions."""
        for event in events:
            if event.type == CHANGE_TO_BATTLE_SCENE:
                self.current_scene = BattleScene(self.screen, event.battle)
        
        return self.current_scene.update(time_delta, events)
