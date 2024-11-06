"""Effect creation module for Battle Swap."""

from enum import Enum, auto
import esper
import pygame
import os
from CONSTANTS import CRUSADER_CLERIC_HEALING_EFFECT_DURATION, TINY_RPG_SCALE
from components.animation import AnimationState, AnimationType
from components.attached import Attached
from components.expiration import Expiration
from components.position import Position
from components.sprite_sheet import SpriteSheet

effect_sheets: dict[AnimationType, pygame.Surface] = {}

class EffectType(Enum):
    HEALING = auto()

def load_effect_sheets():
    """Load all effect sprite sheets."""
    effect_paths = {
        EffectType.HEALING: os.path.join("assets", "units", "CrusaderCleric.png")
    }
    for effect_type, path in effect_paths.items():
        effect_sheets[effect_type] = pygame.image.load(path).convert_alpha()

def create_healing_effect(entity: int):
    """Create a healing effect."""
    effect_entity = esper.create_entity()
    position = esper.component_for_entity(entity, Position)
    esper.add_component(effect_entity, Position(x=position.x, y=position.y))
    esper.add_component(effect_entity, Attached(entity=entity))
    esper.add_component(effect_entity, Expiration(time_left=CRUSADER_CLERIC_HEALING_EFFECT_DURATION))
    esper.add_component(effect_entity, SpriteSheet(
        surface=effect_sheets[EffectType.HEALING],
        frame_width=100,
        frame_height=100,
        scale=TINY_RPG_SCALE,
        frames={AnimationType.IDLE: 4},
        rows={AnimationType.IDLE: 5},
        animation_durations={AnimationType.IDLE: CRUSADER_CLERIC_HEALING_EFFECT_DURATION},
        sprite_center_offset=(0, 0),
    ))
    esper.add_component(effect_entity, AnimationState(type=AnimationType.IDLE))
    return effect_entity
