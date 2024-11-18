import esper
import pygame
import pygame_gui

from camera import Camera
from progress_manager import ProgressManager
from scenes.select_battle import SelectBattleScene
from scenes.setup_battle import SetupBattleScene
from scenes.battle import BattleScene
from scenes.sandbox import SandboxScene
from scenes.events import (
    BATTLE_EDITOR_SCENE_EVENT,
    BATTLE_SCENE_EVENT,
    SANDBOX_SCENE_EVENT,
    SELECT_BATTLE_SCENE_EVENT,
    SETUP_BATTLE_SCENE_EVENT,
    BattleEditorSceneEvent,
    BattleSceneEvent,
    SandboxSceneEvent,
    SelectBattleSceneEvent,
    SetupBattleSceneEvent,
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
    
    def cleanup(self) -> None:
        """Clean up the current scene."""
        self.manager.clear_and_reset()
        if esper.current_world != "world2":
            previous_world = esper.current_world
            new_world = "world2"
        else:
            previous_world = "world2"
            new_world = "world1"
        esper.switch_world(new_world)
        esper.delete_world(previous_world)
            

    def update(self, time_delta: float, events: list[pygame.event.Event]) -> bool:
        """Update the current scene and handle scene transitions."""
        for event in events:
            if event.type == SETUP_BATTLE_SCENE_EVENT:
                validated_event = SetupBattleSceneEvent.model_validate(event.dict)
                self.cleanup()
                self.current_scene = SetupBattleScene(
                    screen=self.screen,
                    camera=self.camera,
                    manager=self.manager,
                    battle_id=validated_event.battle_id,
                    progress_manager=self.progress_manager,
                    ally_placements=validated_event.ally_placements,
                )
            elif event.type == BATTLE_SCENE_EVENT:
                validated_event = BattleSceneEvent.model_validate(event.dict)
                self.cleanup()
                self.current_scene = BattleScene(
                    screen=self.screen,
                    camera=self.camera,
                    manager=self.manager,
                    progress_manager=self.progress_manager,
                    ally_placements=event.ally_placements,
                    enemy_placements=validated_event.enemy_placements,
                    battle_id=validated_event.battle_id,
                    sandbox_mode=validated_event.sandbox_mode,
                    editor_scroll=validated_event.editor_scroll
                )
            elif event.type == SELECT_BATTLE_SCENE_EVENT:
                validated_event = SelectBattleSceneEvent.model_validate(event.dict)
                self.cleanup()
                self.current_scene = SelectBattleScene(
                    screen=self.screen,
                    manager=self.manager,
                    progress_manager=self.progress_manager
                )
            elif event.type == SANDBOX_SCENE_EVENT:
                validated_event = SandboxSceneEvent.model_validate(event.dict)
                self.cleanup()
                self.current_scene = SandboxScene(
                    screen=self.screen,
                    camera=self.camera,
                    manager=self.manager,
                    ally_placements=event.ally_placements,
                    enemy_placements=event.enemy_placements,
                    battle_id=validated_event.battle_id,
                    editor_scroll=validated_event.editor_scroll
                )
            elif event.type == BATTLE_EDITOR_SCENE_EVENT:
                validated_event = BattleEditorSceneEvent.model_validate(event.dict)
                self.cleanup()
                self.current_scene = BattleEditorScene(
                    screen=self.screen,
                    manager=self.manager,
                    editor_scroll=validated_event.editor_scroll
                )
        
        return self.current_scene.update(time_delta, events)
