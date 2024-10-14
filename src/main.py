"""
Main game module for Battle Swap.

This module initializes the game, sets up the display, creates processors,
and runs the main game loop.
"""

import esper
import pygame
import os
import random
from components.team import TeamType
from processors.rendering_processor import RenderingProcessor
from processors.animation_processor import AnimationProcessor
from processors.movement_processor import MovementProcessor
from processors.pursuing_processor import PursuingProcessor
from processors.targeting_processor import TargetingProcessor
from handlers.attack_handler import AttackHandler
from state_machine import StateMachine
from units import create_swordsman, create_archer

# Initialize Pygame
pygame.init()

# Set up the display
SCREEN_WIDTH = 800  # pixels
SCREEN_HEIGHT = 600  # pixels
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Battle Swap")

# Load the sprite sheets
swordsman_path = os.path.join("assets", "MinifolksHumans", "Without Outline", "MiniSwordMan.png")
swordsman_sheet = pygame.image.load(swordsman_path).convert_alpha()

archer_path = os.path.join("assets", "MinifolksHumans", "Without Outline", "MiniArcherMan.png")
archer_sheet = pygame.image.load(archer_path).convert_alpha()

# Create processors
rendering_processor = RenderingProcessor(screen)
animation_processor = AnimationProcessor()
movement_processor = MovementProcessor()
pursuing_processor = PursuingProcessor()
targeting_processor = TargetingProcessor()

# Create event handlers
attack_handler = AttackHandler()
state_machine = StateMachine()

esper.add_processor(targeting_processor)
esper.add_processor(pursuing_processor)
esper.add_processor(movement_processor)
esper.add_processor(animation_processor)
esper.add_processor(rendering_processor)

# Function to add random jitter to positions
def add_jitter(x, y, max_jitter=20):
    return x + random.randint(-max_jitter, max_jitter), y + random.randint(-max_jitter, max_jitter)

# Vertical spacing between units (doubled)
VERTICAL_SPACING = 150  # pixels

# Create team 1 entities (left side, facing right)
for i in range(3):
    # Front line (swordsmen)
    x, y = add_jitter(100, SCREEN_HEIGHT // 2 - VERTICAL_SPACING + i * VERTICAL_SPACING)
    create_swordsman(x, y, TeamType.TEAM1, swordsman_sheet)
    # Back line (archers)
    x, y = add_jitter(50, SCREEN_HEIGHT // 2 - VERTICAL_SPACING + i * VERTICAL_SPACING)
    create_archer(x, y, TeamType.TEAM1, archer_sheet)

# Create team 2 entities (right side, facing left)
for i in range(3):
    # Front line (swordsmen)
    x, y = add_jitter(SCREEN_WIDTH - 100, SCREEN_HEIGHT // 2 - VERTICAL_SPACING + i * VERTICAL_SPACING)
    create_swordsman(x, y, TeamType.TEAM2, swordsman_sheet)
    # Back line (archers)
    x, y = add_jitter(SCREEN_WIDTH - 50, SCREEN_HEIGHT // 2 - VERTICAL_SPACING + i * VERTICAL_SPACING)
    create_archer(x, y, TeamType.TEAM2, archer_sheet)

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
