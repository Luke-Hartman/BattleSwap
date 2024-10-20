import esper
import pygame
from battles import battles
from processors.collision_processor import CollisionProcessor
from processors.rendering_processor import RenderingProcessor
from processors.animation_processor import AnimationProcessor
from processors.movement_processor import MovementProcessor
from processors.pursuing_processor import PursuingProcessor
from processors.targeting_processor import TargetingProcessor
from scenes.scene import Scene


class BattleScene(Scene):
    """The scene for the battle."""

    def __init__(self, screen: pygame.Surface, battle: str):
        rendering_processor = RenderingProcessor(screen)
        animation_processor = AnimationProcessor()
        movement_processor = MovementProcessor()
        pursuing_processor = PursuingProcessor()
        targeting_processor = TargetingProcessor()
        collision_processor = CollisionProcessor(screen)
        esper.add_processor(pursuing_processor)
        esper.add_processor(movement_processor)
        esper.add_processor(animation_processor)
        esper.add_processor(rendering_processor)
        esper.add_processor(collision_processor)
        esper.add_processor(targeting_processor)
        battles[battle]()


    def update(self, time_delta: float, events: list[pygame.event.Event]) -> bool:
        """Update the battle scene."""
        for event in events:
            if event.type == pygame.QUIT:
                return False
        esper.process(time_delta)
        return True

