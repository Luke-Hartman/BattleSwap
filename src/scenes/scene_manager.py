import esper
import pygame
import pygame_gui
from dataclasses import dataclass
from typing import Optional, Any, List

from camera import Camera
from events import STOP_ALL_SOUNDS, StopAllSoundsEvent, emit_event
from hex_grid import axial_to_world
from progress_manager import ProgressManager
from scenes.battle import BattleScene
from scenes.setup_battle import SetupBattleScene
from scenes.test_editor import TestEditorScene
from scenes.events import (
    BATTLE_SCENE_EVENT,
    SETUP_BATTLE_SCENE_EVENT,
    TEST_EDITOR_SCENE_EVENT,
    PREVIOUS_SCENE_EVENT,
    CAMPAIGN_EDITOR_SCENE_EVENT,
    CAMPAIGN_SCENE_EVENT,
    SETTINGS_SCENE_EVENT,
    BattleSceneEvent,
    PreviousSceneEvent,
    SetupBattleSceneEvent,
    TestEditorSceneEvent,
    CampaignEditorSceneEvent,
    CampaignSceneEvent,
    SettingsSceneEvent,
    DEVELOPER_TOOLS_SCENE_EVENT,
)
from scenes.campaign_editor import CampaignEditorScene
from world_map_view import WorldMapView
from battles import Battle, get_battle_id, get_battles
from scenes.campaign import CampaignScene
from scenes.main_menu import MainMenuScene
from scenes.developer_tools import DeveloperToolsScene
from scenes.settings import SettingsScene

class CameraState:
    
    def __init__(self, camera: Camera):
        self.camera = camera
        self.centerx = camera.centerx
        self.centery = camera.centery
        self.zoom = camera.zoom
    
    def restore_position(self):
        self.camera.move(
            centerx=self.centerx,
            centery=self.centery,
            zoom=self.zoom,
        )

@dataclass
class SceneState:
    """Stores the state of a scene."""
    scene_type: type
    params: dict[str, Any]
    camera_state: Optional[CameraState] = None

class SceneManager:
    """Handles transitions between scenes and catches events for changing scenes."""

    def __init__(
            self, 
            screen: pygame.Surface,
            progress_manager: ProgressManager
    ):
        self.screen = screen
        self.progress_manager = progress_manager
        self.manager = pygame_gui.UIManager(
            (pygame.display.Info().current_w, pygame.display.Info().current_h), 
            'src/theme.json'
        )

        self.current_scene = MainMenuScene(screen, self.manager)
        self.scene_stack: List[SceneState] = []

    def cleanup(self, add_to_stack: bool = True) -> None:
        """Clean up the current scene and save its state."""
        if add_to_stack:
            if isinstance(self.current_scene, MainMenuScene):
                self.scene_stack.append(SceneState(
                    scene_type=MainMenuScene,
                    params={"screen": self.screen, "manager": self.manager}
                ))
            elif isinstance(self.current_scene, TestEditorScene):
                self.scene_stack.append(SceneState(
                    scene_type=TestEditorScene,
                    params={"screen": self.screen, "manager": self.manager, 
                        "editor_scroll": self.current_scene._get_scroll_percentage()}
                ))
            elif isinstance(self.current_scene, CampaignEditorScene):
                self.scene_stack.append(SceneState(
                    scene_type=CampaignEditorScene,
                    params={"screen": self.screen, "manager": self.manager,
                        "world_map_view": self.current_scene.world_map_view},
                ))
            elif isinstance(self.current_scene, CampaignScene):
                self.scene_stack.append(SceneState(
                    scene_type=CampaignScene,
                    params={"screen": self.screen, "manager": self.manager,
                        "world_map_view": self.current_scene.world_map_view,
                        "progress_manager": self.progress_manager},
                ))
            elif isinstance(self.current_scene, SetupBattleScene):
                self.scene_stack.append(SceneState(
                    scene_type=SetupBattleScene,
                    params={
                        "screen": self.screen, 
                        "manager": self.manager,
                        "world_map_view": self.current_scene.world_map_view,
                        "battle_id": self.current_scene.battle_id,
                        "progress_manager": self.progress_manager,
                        "sandbox_mode": self.current_scene.sandbox_mode,
                    },
                ))
            elif isinstance(self.current_scene, DeveloperToolsScene):
                self.scene_stack.append(SceneState(
                    scene_type=DeveloperToolsScene,
                    params={"screen": self.screen, "manager": self.manager}
                ))
            elif isinstance(self.current_scene, SettingsScene):
                self.scene_stack.append(SceneState(
                    scene_type=SettingsScene,
                    params={"screen": self.screen, "manager": self.manager}
                ))

        # Clean up UI and ECS
        self.manager.clear_and_reset()
        emit_event(STOP_ALL_SOUNDS, event=StopAllSoundsEvent())
            
    def update(self, time_delta: float, events: list[pygame.event.Event]) -> bool:
        """Update the current scene and handle scene transitions."""
        for event in events:
            if event.type == PREVIOUS_SCENE_EVENT:
                validated_event = PreviousSceneEvent.model_validate(event.dict)
                for _ in range(validated_event.n):
                    previous_state = self.scene_stack.pop()
                self.cleanup(add_to_stack=False)
                self.current_scene = previous_state.scene_type(
                    **previous_state.params
                )
                if previous_state.camera_state:
                    previous_state.camera_state.restore_position()
            elif event.type == BATTLE_SCENE_EVENT:
                validated_event = BattleSceneEvent.model_validate(event.dict)
                self.cleanup()
                self.current_scene = BattleScene(
                    screen=self.screen,
                    manager=self.manager,
                    progress_manager=self.progress_manager,
                    world_map_view=validated_event.world_map_view,
                    battle_id=validated_event.battle_id,
                    sandbox_mode=validated_event.sandbox_mode,
                )
            elif event.type == SETUP_BATTLE_SCENE_EVENT:
                self.cleanup()
                validated_event = SetupBattleSceneEvent.model_validate(event.dict)
                if validated_event.world_map_view is not None:
                    camera = validated_event.world_map_view.camera
                    battle = validated_event.world_map_view.battles[validated_event.battle_id]
                    world_x, world_y = axial_to_world(*battle.hex_coords)
                    camera.move(
                        centerx=world_x,
                        centery=world_y,
                        zoom=1.0
                    )
                self.current_scene = SetupBattleScene(
                    screen=self.screen,
                    manager=self.manager,
                    world_map_view=validated_event.world_map_view,
                    battle_id=validated_event.battle_id,
                    progress_manager=self.progress_manager,
                    sandbox_mode=validated_event.sandbox_mode,
                    developer_mode=validated_event.developer_mode,
                )
            elif event.type == TEST_EDITOR_SCENE_EVENT:
                self.cleanup()
                validated_event = TestEditorSceneEvent.model_validate(event.dict)
                self.current_scene = TestEditorScene(
                    screen=self.screen,
                    manager=self.manager,
                )
            elif event.type == CAMPAIGN_EDITOR_SCENE_EVENT:
                self.cleanup()
                validated_event = CampaignEditorSceneEvent.model_validate(event.dict)
                self.current_scene = CampaignEditorScene(
                    screen=self.screen,
                    manager=self.manager,
                    world_map_view=validated_event.world_map_view,
                )
            elif event.type == CAMPAIGN_SCENE_EVENT:
                self.cleanup()
                validated_event = CampaignSceneEvent.model_validate(event.dict)
                self.current_scene = CampaignScene(
                    screen=self.screen,
                    manager=self.manager,
                    world_map_view=validated_event.world_map_view,
                    progress_manager=self.progress_manager
                )
            elif event.type == DEVELOPER_TOOLS_SCENE_EVENT:
                self.cleanup()
                self.current_scene = DeveloperToolsScene(
                    screen=self.screen,
                    manager=self.manager,
                )
            elif event.type == SETTINGS_SCENE_EVENT:
                self.cleanup()
                validated_event = SettingsSceneEvent.model_validate(event.dict)
                self.current_scene = SettingsScene(
                    screen=self.screen,
                    manager=self.manager,
                )
        
        return self.current_scene.update(time_delta, events)
