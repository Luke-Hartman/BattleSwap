import esper
import pygame
import pygame_gui
from dataclasses import dataclass
from typing import Optional, Any

from camera import Camera
from events import STOP_ALL_SOUNDS, StopAllSoundsEvent, emit_event
from handlers.sound_handler import SoundHandler
from progress_manager import ProgressManager
from scenes.select_battle import SelectBattleScene
from scenes.setup_battle import SetupBattleScene
from scenes.battle import BattleScene
from scenes.sandbox import SandboxScene
from scenes.test_editor import TestEditorScene
from scenes.events import (
    BATTLE_EDITOR_SCENE_EVENT,
    BATTLE_SCENE_EVENT,
    SANDBOX_SCENE_EVENT,
    SELECT_BATTLE_SCENE_EVENT,
    SETUP_BATTLE_SCENE_EVENT,
    TEST_EDITOR_SCENE_EVENT,
    BattleEditorSceneEvent,
    BattleSceneEvent,
    SandboxSceneEvent,
    SelectBattleSceneEvent,
    SetupBattleSceneEvent,
    TestEditorSceneEvent,
    PREVIOUS_SCENE_EVENT,
)
from scenes.battle_editor import BattleEditorScene

@dataclass
class SceneState:
    """Stores the state of a scene."""
    scene_type: type
    params: dict[str, Any]

class SceneManager:
    """Handles transitions between scenes and catches events for changing scenes."""

    def __init__(
            self, 
            screen: pygame.Surface, 
            camera: Camera, 
            progress_manager: ProgressManager, 
            sound_handler: SoundHandler
    ):
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
        self.previous_scene_state: Optional[SceneState] = None
        self.sound_handler = sound_handler
    def cleanup(self) -> None:
        """Clean up the current scene and save its state."""
        # Save current scene state, but don't save SetupBattleScene
        if isinstance(self.current_scene, SelectBattleScene):
            self.previous_scene_state = SceneState(
                scene_type=SelectBattleScene,
                params={"screen": self.screen, "manager": self.manager, 
                       "progress_manager": self.progress_manager}
            )
        elif isinstance(self.current_scene, BattleEditorScene):
            self.previous_scene_state = SceneState(
                scene_type=BattleEditorScene,
                params={"screen": self.screen, "manager": self.manager, 
                       "editor_scroll": self.current_scene._get_scroll_percentage()}
            )
        elif isinstance(self.current_scene, TestEditorScene):
            self.previous_scene_state = SceneState(
                scene_type=TestEditorScene,
                params={"screen": self.screen, "manager": self.manager, 
                       "editor_scroll": self.current_scene._get_scroll_percentage()}
            )
        elif isinstance(self.current_scene, BattleScene):
            # Battle scene should return to select battle scene
            self.previous_scene_state = SceneState(
                scene_type=SelectBattleScene,
                params={"screen": self.screen, "manager": self.manager,
                       "progress_manager": self.progress_manager}
            )

        # Clean up UI and ECS
        self.manager.clear_and_reset()
        if esper.current_world != "world2":
            previous_world = esper.current_world
            new_world = "world2"
        else:
            previous_world = "world2"
            new_world = "world1"
        esper.switch_world(new_world)
        esper.delete_world(previous_world)

        emit_event(STOP_ALL_SOUNDS, event=StopAllSoundsEvent())
            
    def update(self, time_delta: float, events: list[pygame.event.Event]) -> bool:
        """Update the current scene and handle scene transitions."""
        for event in events:
            if event.type == PREVIOUS_SCENE_EVENT:
                if self.previous_scene_state:
                    self.cleanup()
                    self.current_scene = self.previous_scene_state.scene_type(
                        **self.previous_scene_state.params
                    )
                    self.previous_scene_state = None
            elif event.type == SETUP_BATTLE_SCENE_EVENT:
                validated_event = SetupBattleSceneEvent.model_validate(event.dict)
                self.cleanup()
                self.current_scene = SetupBattleScene(
                    screen=self.screen,
                    camera=self.camera,
                    manager=self.manager,
                    battle_id=validated_event.battle_id,
                    progress_manager=self.progress_manager,
                    ally_placements=validated_event.ally_placements,
                    play_tip_sound=validated_event.play_tip_sound,
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
                )
            elif event.type == SELECT_BATTLE_SCENE_EVENT:
                self.cleanup()
                validated_event = SelectBattleSceneEvent.model_validate(event.dict)
                self.current_scene = SelectBattleScene(
                    screen=self.screen,
                    manager=self.manager,
                    progress_manager=self.progress_manager
                )
            elif event.type == SANDBOX_SCENE_EVENT:
                self.cleanup()
                validated_event = SandboxSceneEvent.model_validate(event.dict)
                self.current_scene = SandboxScene(
                    screen=self.screen,
                    camera=self.camera,
                    manager=self.manager,
                    ally_placements=event.ally_placements,
                    enemy_placements=event.enemy_placements,
                    battle_id=validated_event.battle_id,
                )
            elif event.type == BATTLE_EDITOR_SCENE_EVENT:
                self.cleanup()
                validated_event = BattleEditorSceneEvent.model_validate(event.dict)
                self.current_scene = BattleEditorScene(
                    screen=self.screen,
                    manager=self.manager,
                )
            elif event.type == TEST_EDITOR_SCENE_EVENT:
                self.cleanup()
                validated_event = TestEditorSceneEvent.model_validate(event.dict)
                self.current_scene = TestEditorScene(
                    screen=self.screen,
                    manager=self.manager,
                )
        
        return self.current_scene.update(time_delta, events)
