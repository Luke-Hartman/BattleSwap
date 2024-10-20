"""
Main game module for Battle Swap.

This module initializes the game, sets up the display, creates processors,
and runs the main game loop.
"""

import esper
import pygame
from CONSTANTS import SCREEN_HEIGHT, SCREEN_WIDTH
from battles import battles
from processors.rendering_processor import RenderingProcessor
from processors.animation_processor import AnimationProcessor
from processors.movement_processor import MovementProcessor
from processors.pursuing_processor import PursuingProcessor
from processors.targeting_processor import TargetingProcessor
from handlers.attack_handler import AttackHandler
from handlers.state_machine import StateMachine
from entities.units import load_sprite_sheets
from processors.collision_processor import CollisionProcessor
from entities.projectiles import load_projectile_sheets

# Initialize Pygame
pygame.init()

# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Battle Swap")

# Load sprite sheets
load_sprite_sheets()
load_projectile_sheets()

# Create processors
rendering_processor = RenderingProcessor(screen)
animation_processor = AnimationProcessor()
movement_processor = MovementProcessor()
pursuing_processor = PursuingProcessor()
targeting_processor = TargetingProcessor()
collision_processor = CollisionProcessor(screen)  # Pass the screen here

# Create event handlers
attack_handler = AttackHandler()
state_machine = StateMachine()

esper.add_processor(targeting_processor)
esper.add_processor(pursuing_processor)
esper.add_processor(movement_processor)
esper.add_processor(animation_processor)
esper.add_processor(rendering_processor)
esper.add_processor(collision_processor)

battles["tutorial_1"]()

# Main game loop
running = True
clock = pygame.time.Clock()

while running:
    dt = clock.tick(60) / 1000.0  # Convert to seconds

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    esper.process(dt)

pygame.quit()
