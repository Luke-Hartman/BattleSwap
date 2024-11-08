"""Reusable visual effects."""

import esper
from components.animation import AnimationState, AnimationType
from components.attached import Attached
from components.expiration import Expiration
from components.position import Position
from visuals import create_visual_spritesheet, Visual

def create_healing_effect(entity: int):
    """Create a healing effect."""
    effect_entity = esper.create_entity()
    position = esper.component_for_entity(entity, Position)
    duration = 1
    esper.add_component(effect_entity, Position(x=position.x, y=position.y))
    esper.add_component(effect_entity, Attached(entity=entity))
    esper.add_component(effect_entity, Expiration(time_left=duration))
    esper.add_component(effect_entity, create_visual_spritesheet(Visual.Healing))
    esper.add_component(effect_entity, AnimationState(type=AnimationType.IDLE))
    return effect_entity
