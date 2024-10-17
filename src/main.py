"""
Main game module for Battle Swap.

This module initializes the game, sets up the display, creates processors,
and runs the main game loop.
"""

import esper
import pygame
import random
from components.team import TeamType
from processors.rendering_processor import RenderingProcessor
from processors.animation_processor import AnimationProcessor
from processors.movement_processor import MovementProcessor
from processors.pursuing_processor import PursuingProcessor
from processors.targeting_processor import TargetingProcessor
from handlers.attack_handler import AttackHandler
from handlers.state_machine import StateMachine
from entities.units import create_mage, create_swordsman, create_archer, load_sprite_sheets
from processors.collision_processor import CollisionProcessor
from entities.projectiles import load_projectile_sheets

# Initialize Pygame
pygame.init()

# Set up the display
SCREEN_WIDTH = 800  # pixels
SCREEN_HEIGHT = 600  # pixels
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

# Function to add random jitter to positions
def add_jitter(x, y, x_jitter=30, y_jitter=SCREEN_HEIGHT // 2 - 100):
    return x + random.randint(-x_jitter, x_jitter), y + random.randint(-y_jitter, y_jitter)
n = 2
# Create team 1 entities (left side, facing right)
for i in range(n):
    # Front line (swordsmen)
    x, y = add_jitter(150, SCREEN_HEIGHT // 2)
    create_swordsman(x, y, TeamType.TEAM1)
    # Middle line (archers)
    x, y = add_jitter(100, SCREEN_HEIGHT // 2)
    create_archer(x, y, TeamType.TEAM1)
    # Back line (mages)
    x, y = add_jitter(150, SCREEN_HEIGHT // 2)
    create_mage(x, y, TeamType.TEAM1)

# Create team 2 entities (right side, facing left)
for i in range(n):
    # Front line (swordsmen)
    x, y = add_jitter(SCREEN_WIDTH - 150, SCREEN_HEIGHT // 2)
    create_swordsman(x, y, TeamType.TEAM2)
    # Middle line (archers)
    x, y = add_jitter(SCREEN_WIDTH - 100, SCREEN_HEIGHT // 2)
    create_archer(x, y, TeamType.TEAM2)
    # Back line (mages)
    x, y = add_jitter(SCREEN_WIDTH - 150, SCREEN_HEIGHT // 2)
    create_mage(x, y, TeamType.TEAM2)


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
