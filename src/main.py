"""
Main game module for Battle Swap.

This module initializes the game, sets up the display, creates processors,
and runs the main game loop.
"""

import esper
import pygame
import os
from components.position import Position
from components.animation import AnimationState, AnimationType
from components.sprite_sheet import SpriteSheet
from processors.rendering_processor import RenderingProcessor
from processors.animation_processor import AnimationProcessor

# Initialize Pygame
pygame.init()

# Set up the display
SCREEN_WIDTH = 800  # pixels
SCREEN_HEIGHT = 600  # pixels
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Battle Swap")

# Load the sprite sheet
swordsman_path = os.path.join("assets", "MinifolksHumans", "Without Outline", "MiniSwordMan.png")
swordsman_sheet = pygame.image.load(swordsman_path).convert_alpha()

# Create processors
rendering_processor = RenderingProcessor(screen)
esper.add_processor(rendering_processor)
esper.add_processor(AnimationProcessor())

# Create some entities
for i in range(5):
    entity = esper.create_entity()
    esper.add_component(entity, Position(x=50 + i * 100, y=SCREEN_HEIGHT // 2))
    esper.add_component(entity, AnimationState(type=AnimationType.IDLE))
    esper.add_component(entity, SpriteSheet(
        surface=swordsman_sheet,
        frame_width=32,
        frame_height=32,
        scale=4,
        frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ATTACKING: 6, AnimationType.DYING: 4},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ATTACKING: 3, AnimationType.DYING: 5},
        animation_durations={AnimationType.IDLE: 0.8, AnimationType.WALKING: 0.6, AnimationType.ATTACKING: 0.6, AnimationType.DYING: 0.8}
    ))

# Main game loop
running = True
clock = pygame.time.Clock()

while running:
    dt = clock.tick(60) / 1000.0  # Convert to seconds

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Process all systems
    esper.process(dt)

pygame.quit()
