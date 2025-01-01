"""Custom pygame events related to scenes."""

import pygame
from abc import abstractmethod
from pydantic import BaseModel

from world_map_view import WorldMapView

SETUP_BATTLE_SCENE_EVENT = pygame.event.custom_type()
BATTLE_SCENE_EVENT = pygame.event.custom_type()
SANDBOX_SCENE_EVENT = pygame.event.custom_type()
SELECT_BATTLE_SCENE_EVENT = pygame.event.custom_type()
TEST_EDITOR_SCENE_EVENT = pygame.event.custom_type()
PREVIOUS_SCENE_EVENT = pygame.event.custom_type()
MOVE_BATTLES_SCENE_EVENT = pygame.event.custom_type()
CAMPAIGN_SCENE_EVENT = pygame.event.custom_type()

class PyGameEvent(BaseModel):
    """Base class for pygame events."""
    
    class Config:
        arbitrary_types_allowed = True

    @property
    @abstractmethod
    def _type(self) -> int:
        pass

    def to_event(self) -> pygame.event.Event:
        """Convert the pydantic model to a pygame event."""
        return pygame.event.Event(self._type, **self.model_dump())

class SetupBattleSceneEvent(PyGameEvent):
    """Event for setting up a battle."""
    world_map_view: WorldMapView
    battle_id: str
    play_tip_sound: bool = False

    @property
    def _type(self) -> int:
        return SETUP_BATTLE_SCENE_EVENT

class BattleSceneEvent(PyGameEvent):
    """Event for starting a battle."""
    world_map_view: WorldMapView
    battle_id: str
    sandbox_mode: bool

    @property
    def _type(self) -> int:
        return BATTLE_SCENE_EVENT

class SandboxSceneEvent(PyGameEvent):
    """Event for starting a sandbox battle."""
    world_map_view: WorldMapView
    battle_id: str
    sandbox_mode: bool

    @property
    def _type(self) -> int:
        return SANDBOX_SCENE_EVENT


class SelectBattleSceneEvent(PyGameEvent):
    """Event for selecting a battle."""

    @property
    def _type(self) -> int:
        return SELECT_BATTLE_SCENE_EVENT


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

class MoveBattlesSceneEvent(PyGameEvent):
    """Event for transitioning to the world map scene."""

    world_map_view: WorldMapView

    @property
    def _type(self) -> int:
        return MOVE_BATTLES_SCENE_EVENT

class CampaignSceneEvent(PyGameEvent):
    """Event for transitioning to the campaign scene."""

    world_map_view: WorldMapView

    @property
    def _type(self) -> int:
        return CAMPAIGN_SCENE_EVENT
