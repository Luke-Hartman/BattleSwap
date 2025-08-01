"""Scene manager module for handling scene transitions."""
import esper
import pygame
import pygame_gui
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Any, List

from camera import Camera
from events import STOP_ALL_SOUNDS, StopAllSoundsEvent, emit_event, MUTE_DRUMS, MuteDrumsEvent
from hex_grid import axial_to_world
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
    DeveloperToolsSceneEvent,
    PreviousSceneEvent,
    SetupBattleSceneEvent,
    TestEditorSceneEvent,
    CampaignEditorSceneEvent,
    CampaignSceneEvent,
    SettingsSceneEvent,
    DEVELOPER_TOOLS_SCENE_EVENT,
)
from scenes.campaign_editor import CampaignEditorScene
from scenes.campaign import CampaignScene
from scenes.main_menu import MainMenuScene
from scenes.developer_tools import DeveloperToolsScene
from scenes.settings import SettingsScene
from world_map_view import WorldMapView
from progress_manager import progress_manager
from screen_dimensions import get_width, get_height

def get_resource_path(relative_path: str) -> Path:
    """Get absolute path to resource, works for dev and for PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return Path(base_path) / relative_path

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

    def __init__(self):
        """Initialize the scene manager without screen/UI dependencies."""
        self.screen: Optional[pygame.Surface] = None
        self.manager: Optional[pygame_gui.UIManager] = None
        self.developer_mode = False
        self.current_scene: Optional[Any] = None
        self.scene_stack: List[SceneState] = []
        self.last_played_battle_id: Optional[str] = None

    def initialize(self, screen: pygame.Surface, developer_mode: bool = False) -> None:
        """Initialize with screen and UI dependencies."""
        self.screen = screen
        theme_path = str(get_resource_path('data/theme.json'))
        self.manager = pygame_gui.UIManager(
            (get_width(), get_height()), 
            theme_path
        )
        self.developer_mode = developer_mode
        self.current_scene = MainMenuScene(screen, self.manager, self.developer_mode)

    def cleanup(self, add_to_stack: bool = True) -> None:
        """Clean up the current scene and save its state."""
        emit_event(MUTE_DRUMS, event=MuteDrumsEvent())
        if not self.current_scene:
            return

        if add_to_stack:
            if isinstance(self.current_scene, MainMenuScene):
                self.scene_stack.append(SceneState(
                    scene_type=MainMenuScene,
                    params={
                        "screen": self.screen,
                        "manager": self.manager,
                        "developer_mode": self.developer_mode,
                    }
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
                    }
                ))
            elif isinstance(self.current_scene, SetupBattleScene):
                self.scene_stack.append(SceneState(
                    scene_type=SetupBattleScene,
                    params={
                        "screen": self.screen, 
                        "manager": self.manager,
                        "world_map_view": self.current_scene.world_map_view,
                        "battle_id": self.current_scene.battle_id,
                        "sandbox_mode": self.current_scene.sandbox_mode,
                        "developer_mode": self.current_scene.developer_mode,
                        "is_corrupted": self.current_scene.is_corrupted,
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
        if self.manager:
            self.manager.clear_and_reset()
        emit_event(STOP_ALL_SOUNDS, event=StopAllSoundsEvent())
            
    def update(self, time_delta: float, events: list[pygame.event.Event]) -> bool:
        """Update the current scene and handle scene transitions."""
        if not self.current_scene:
            return False
        for event in events:
            if event.type == PREVIOUS_SCENE_EVENT:
                validated_event = PreviousSceneEvent.model_validate(event.dict)
                if validated_event.current_scene_id != id(self.current_scene):
                    continue
                n = validated_event.n
                while n > 0:
                    previous_state = self.scene_stack.pop()
                    n -= 1
                self.cleanup(add_to_stack=False)

                # Handle special case for CampaignScene to pass last_played_battle_id
                if previous_state.scene_type == CampaignScene:
                    params_with_battle_id = previous_state.params.copy()
                    params_with_battle_id["last_played_battle_id"] = self.last_played_battle_id
                    self.current_scene = previous_state.scene_type(**params_with_battle_id)
                else:
                    self.current_scene = previous_state.scene_type(**previous_state.params)
                    
                if previous_state.camera_state:
                    previous_state.camera_state.restore_position()
            elif event.type == BATTLE_SCENE_EVENT:
                validated_event = BattleSceneEvent.model_validate(event.dict)
                if validated_event.current_scene_id != id(self.current_scene):
                    continue
                self.cleanup()
                self.current_scene = BattleScene(
                    screen=self.screen,
                    manager=self.manager,
                    world_map_view=validated_event.world_map_view,
                    battle_id=validated_event.battle_id,
                    sandbox_mode=validated_event.sandbox_mode,
                    developer_mode=self.developer_mode,
                )
            elif event.type == SETUP_BATTLE_SCENE_EVENT:
                validated_event = SetupBattleSceneEvent.model_validate(event.dict)
                if validated_event.current_scene_id != id(self.current_scene):
                    continue
                # Track this battle if coming from campaign scene
                if isinstance(self.current_scene, CampaignScene):
                    self.last_played_battle_id = validated_event.battle_id
                self.cleanup()
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
                    sandbox_mode=validated_event.sandbox_mode,
                    developer_mode=validated_event.developer_mode,
                    is_corrupted=validated_event.is_corrupted,
                )
            elif event.type == TEST_EDITOR_SCENE_EVENT:
                validated_event = TestEditorSceneEvent.model_validate(event.dict)
                if validated_event.current_scene_id != id(self.current_scene):
                    continue
                self.cleanup()
                self.current_scene = TestEditorScene(
                    screen=self.screen,
                    manager=self.manager,
                )
            elif event.type == CAMPAIGN_EDITOR_SCENE_EVENT:
                validated_event = CampaignEditorSceneEvent.model_validate(event.dict)
                if validated_event.current_scene_id != id(self.current_scene):
                    continue
                self.cleanup()
                self.current_scene = CampaignEditorScene(
                    screen=self.screen,
                    manager=self.manager,
                    world_map_view=WorldMapView(
                        screen=self.screen,
                        manager=self.manager,
                        battles=progress_manager.get_battles_including_solutions(),
                        camera=Camera(zoom=1/4),
                    )
                )
            elif event.type == CAMPAIGN_SCENE_EVENT:
                validated_event = CampaignSceneEvent.model_validate(event.dict)
                if validated_event.current_scene_id != id(self.current_scene):
                    continue
                # Clear last battle tracking if coming from main menu
                if isinstance(self.current_scene, MainMenuScene):
                    self.last_played_battle_id = None
                self.cleanup()
                camera = Camera(zoom=1/2)
                world_map_view = WorldMapView(
                    screen=self.screen,
                    manager=self.manager,
                    battles=progress_manager.get_battles_including_solutions(),
                    camera=camera,
                )
                self.current_scene = CampaignScene(
                    screen=self.screen,
                    manager=self.manager,
                    world_map_view=world_map_view,
                    last_played_battle_id=self.last_played_battle_id,
                )
            elif event.type == DEVELOPER_TOOLS_SCENE_EVENT:
                validated_event = DeveloperToolsSceneEvent.model_validate(event.dict)
                if validated_event.current_scene_id != id(self.current_scene):
                    continue
                self.cleanup()
                self.current_scene = DeveloperToolsScene(
                    screen=self.screen,
                    manager=self.manager,
                )
            elif event.type == SETTINGS_SCENE_EVENT:
                validated_event = SettingsSceneEvent.model_validate(event.dict)
                if validated_event.current_scene_id != id(self.current_scene):
                    continue
                self.cleanup()
                self.current_scene = SettingsScene(
                    screen=self.screen,
                    manager=self.manager,
                )
        
        return self.current_scene.update(time_delta, events)

# Create the singleton instance
scene_manager = SceneManager()
