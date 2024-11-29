"""Custom pygame events related to scenes."""

import pygame
from typing import List, Optional, Tuple
from abc import abstractmethod
from components.unit_type import UnitType
from pydantic import BaseModel

SETUP_BATTLE_SCENE_EVENT = pygame.event.custom_type()
BATTLE_SCENE_EVENT = pygame.event.custom_type()
SANDBOX_SCENE_EVENT = pygame.event.custom_type()
SELECT_BATTLE_SCENE_EVENT = pygame.event.custom_type()
BATTLE_EDITOR_SCENE_EVENT = pygame.event.custom_type()
TEST_EDITOR_SCENE_EVENT = pygame.event.custom_type()
PREVIOUS_SCENE_EVENT = pygame.event.custom_type()

class PyGameEvent(BaseModel):
    """Base class for pygame events."""

    @property
    @abstractmethod
    def _type(self) -> int:
        pass

    def to_event(self) -> pygame.event.Event:
        """Convert the pydantic model to a pygame event."""
        return pygame.event.Event(self._type, **self.model_dump())

class SetupBattleSceneEvent(PyGameEvent):
    """Event for setting up a battle."""
    ally_placements: List[Tuple[UnitType, Tuple[int, int]]]
    battle_id: str
    play_tip_sound: bool

    @property
    def _type(self) -> int:
        return SETUP_BATTLE_SCENE_EVENT

class BattleSceneEvent(PyGameEvent):
    """Event for starting a battle."""
    ally_placements: List[Tuple[UnitType, Tuple[int, int]]]
    enemy_placements: List[Tuple[UnitType, Tuple[int, int]]]
    battle_id: Optional[str]
    sandbox_mode: bool

    @property
    def _type(self) -> int:
        return BATTLE_SCENE_EVENT

class SandboxSceneEvent(PyGameEvent):
    """Event for starting a sandbox battle."""
    ally_placements: List[Tuple[UnitType, Tuple[int, int]]]
    enemy_placements: List[Tuple[UnitType, Tuple[int, int]]]
    battle_id: Optional[str]

    @property
    def _type(self) -> int:
        return SANDBOX_SCENE_EVENT


class SelectBattleSceneEvent(PyGameEvent):
    """Event for selecting a battle."""

    @property
    def _type(self) -> int:
        return SELECT_BATTLE_SCENE_EVENT


class BattleEditorSceneEvent(PyGameEvent):
    """Event for starting the battle editor."""

    @property
    def _type(self) -> int:
        return BATTLE_EDITOR_SCENE_EVENT

class TestEditorSceneEvent(BaseModel):
    """Event for switching to the test editor scene."""
    
    def to_event(self) -> pygame.event.Event:
        """Convert to pygame event."""
        return pygame.event.Event(TEST_EDITOR_SCENE_EVENT, self.model_dump())

class PreviousSceneEvent(PyGameEvent):
    """Event for returning to the previous scene."""

    @property
    def _type(self) -> int:
        return PREVIOUS_SCENE_EVENT
