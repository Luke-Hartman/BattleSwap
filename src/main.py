"""
Main game module for Battle Swap.

This module initializes the game, sets up the display, creates processors,
and runs the main game loop.
"""

import pygame
from camera import Camera
from entities.units import load_sprite_sheets
from handlers.combat_handler import CombatHandler
from handlers.sound_handler import SoundHandler
from handlers.state_machine import StateMachine
from progress_manager import ProgressManager
from scenes.scene_manager import SceneManager
from visuals import load_visual_sheets
from game_constants import gc
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
sound_handler = SoundHandler()

# Main game loop
running = True
clock = pygame.time.Clock()

# Get screen width and height
screen_width = pygame.display.Info().current_w
screen_height = pygame.display.Info().current_h

# Initialize camera centered on battlefield
initial_camera_x = (gc.BATTLEFIELD_WIDTH - screen_width) // 2
initial_camera_y = (gc.BATTLEFIELD_HEIGHT - screen_height) // 2
camera = Camera(screen_width, screen_height)
camera.x = initial_camera_x
camera.y = initial_camera_y

progress_manager = ProgressManager()
scene_manager = SceneManager(screen, camera, progress_manager, sound_handler)

while running:
    clock.tick(60)
    events = pygame.event.get()
    # Escape key quits the game
    for event in events:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
    if not running:
        break
    running = scene_manager.update(1/60, events)
    pygame.display.flip()

pygame.quit()
