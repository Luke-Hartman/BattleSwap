"""
Main game module for Battle Swap.

This module initializes the game, sets up the display, creates processors,
and runs the main game loop.
"""

import pygame
from CONSTANTS import (
    BATTLEFIELD_WIDTH, 
    BATTLEFIELD_HEIGHT
)
from camera import Camera
from entities.units import load_sprite_sheets
from handlers.combat_handler import CombatHandler
from handlers.state_machine import StateMachine
from progress_manager import ProgressManager
from scenes.scene_manager import SceneManager
from visuals import load_visual_sheets

# Initialize Pygame
pygame.init()

# Set up the display
# Use the full screen
screen = pygame.display.set_mode(flags=pygame.FULLSCREEN)
pygame.display.set_caption("Battle Swap")

# Load sprite sheets
load_sprite_sheets()
load_visual_sheets()

combat_handler = CombatHandler()
state_machine = StateMachine()

# Main game loop
running = True
clock = pygame.time.Clock()

# Get screen width and height
screen_width = pygame.display.Info().current_w
screen_height = pygame.display.Info().current_h

# Initialize camera centered on battlefield
initial_camera_x = (BATTLEFIELD_WIDTH - screen_width) // 2
initial_camera_y = (BATTLEFIELD_HEIGHT - screen_height) // 2
camera = Camera(screen_width, screen_height)
camera.x = initial_camera_x
camera.y = initial_camera_y

progress_manager = ProgressManager()
scene_manager = SceneManager(screen, camera, progress_manager)

while running:
    dt = clock.tick(60) / 1000.0  # Convert to seconds
    events = pygame.event.get()
    # Escape key quits the game
    for event in events:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
    if not running:
        break
    running = scene_manager.update(dt, events)
    pygame.display.flip()

pygame.quit()
