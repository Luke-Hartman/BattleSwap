"""Custom pygame events related to scenes."""

from typing import Optional
import pygame
from abc import abstractmethod
from pydantic import BaseModel

from world_map_view import WorldMapView

BATTLE_SCENE_EVENT = pygame.event.custom_type()
SETUP_BATTLE_SCENE_EVENT = pygame.event.custom_type()
TEST_EDITOR_SCENE_EVENT = pygame.event.custom_type()
PREVIOUS_SCENE_EVENT = pygame.event.custom_type()
CAMPAIGN_EDITOR_SCENE_EVENT = pygame.event.custom_type()
CAMPAIGN_SCENE_EVENT = pygame.event.custom_type()
DEVELOPER_TOOLS_SCENE_EVENT = pygame.event.custom_type()
SETTINGS_SCENE_EVENT = pygame.event.custom_type()

class PyGameEvent(BaseModel):
    """Base class for pygame events."""
    
    current_scene_id: int
    """The Python id() of the scene that created this event.
    
    This is used to prevent multiple of the same scene from being created when a user
    rapidly presses the return button or otherwise creates multiple scene transition events.
    """
    
    class Config:
        arbitrary_types_allowed = True

    @property
    @abstractmethod
    def _type(self) -> int:
        pass

    def to_event(self) -> pygame.event.Event:
        """Convert the pydantic model to a pygame event."""
        return pygame.event.Event(self._type, **self.model_dump())

class BattleSceneEvent(PyGameEvent):
    """Event for starting a battle."""
    world_map_view: WorldMapView
    battle_id: str
    sandbox_mode: bool

    @property
    def _type(self) -> int:
        return BATTLE_SCENE_EVENT

class SetupBattleSceneEvent(PyGameEvent):
    """Event for setting up a battle."""
    world_map_view: Optional[WorldMapView]
    battle_id: Optional[str]
    sandbox_mode: bool
    developer_mode: bool

    @property
    def _type(self) -> int:
        return SETUP_BATTLE_SCENE_EVENT


class TestEditorSceneEvent(PyGameEvent):
    """Event for switching to the test editor scene."""

    @property
    def _type(self) -> int:
        return TEST_EDITOR_SCENE_EVENT

class PreviousSceneEvent(PyGameEvent):
    """Event for returning to the previous scene."""
    n: int = 1
    """The number of scenes to pop."""

    @property
    def _type(self) -> int:
        return PREVIOUS_SCENE_EVENT

class CampaignEditorSceneEvent(PyGameEvent):
    """Event for transitioning to the campaign editor scene."""

    world_map_view: WorldMapView

    @property
    def _type(self) -> int:
        return CAMPAIGN_EDITOR_SCENE_EVENT

class CampaignSceneEvent(PyGameEvent):
    """Event for transitioning to the campaign scene."""

    @property
    def _type(self) -> int:
        return CAMPAIGN_SCENE_EVENT

class DeveloperToolsSceneEvent(PyGameEvent):
    """Event for transitioning to the developer tools scene."""

    @property
    def _type(self) -> int:
        return DEVELOPER_TOOLS_SCENE_EVENT

class SettingsSceneEvent(PyGameEvent):
    """Event for transitioning to the settings scene."""

    @property
    def _type(self) -> int:
        return SETTINGS_SCENE_EVENT
