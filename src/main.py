"""
Main game module for Battle Swap.

This module initializes the game, sets up the display, creates processors,
and runs the main game loop.
"""

import pygame
from CONSTANTS import SCREEN_HEIGHT, SCREEN_WIDTH
from battles import battles
from entities.units import load_sprite_sheets
from entities.projectiles import load_projectile_sheets
from handlers.attack_handler import AttackHandler
from handlers.state_machine import StateMachine
from scenes.scene_manager import SceneManager

# Initialize Pygame
pygame.init()

# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Battle Swap")

# Load sprite sheets
load_sprite_sheets()
load_projectile_sheets()
        
attack_handler = AttackHandler()
state_machine = StateMachine()

# Main game loop
running = True
clock = pygame.time.Clock()

scene_manager = SceneManager(screen)

while running:
    dt = clock.tick(60) / 1000.0  # Convert to seconds
    events = pygame.event.get()
    running = scene_manager.update(dt, events)
    pygame.display.flip()

pygame.quit()
