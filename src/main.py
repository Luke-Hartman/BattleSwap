"""
Main game module for Battle Swap.

This module initializes the game, sets up the display, creates processors,
and runs the main game loop.
"""

import esper
import pygame
import os
from components.team import TeamType
from processors.rendering_processor import RenderingProcessor
from processors.animation_processor import AnimationProcessor
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
esper.add_processor(rendering_processor)
esper.add_processor(AnimationProcessor())

# Create team 1 entities (right-facing)
for i in range(3):
    create_swordsman(50 + i * 100, SCREEN_HEIGHT // 2 - 50, TeamType.TEAM1, swordsman_sheet)
    create_archer(50 + i * 100, SCREEN_HEIGHT // 2 + 50, TeamType.TEAM1, archer_sheet)

# Create team 2 entities (left-facing)
for i in range(3):
    create_swordsman(SCREEN_WIDTH - 50 - i * 100, SCREEN_HEIGHT // 2 - 50, TeamType.TEAM2, swordsman_sheet)
    create_archer(SCREEN_WIDTH - 50 - i * 100, SCREEN_HEIGHT // 2 + 50, TeamType.TEAM2, archer_sheet)

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
