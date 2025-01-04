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
from scenes.scene_manager import SceneManager
from time_manager import time_manager
from visuals import load_visual_sheets
from game_constants import gc
# Initialize Pygame
pygame.init()

# Set up the display
# Use the full screen
screen = pygame.display.set_mode(flags=pygame.FULLSCREEN)
pygame.display.set_caption("Battle Swap")

# Initialize font for FPS counter
fps_font = pygame.font.SysFont('Arial', 30)

# Load sprite sheets
load_sprite_sheets()
load_visual_sheets()

combat_handler = CombatHandler()
state_machine = StateMachine()
sound_handler = SoundHandler()

# Main game loop
running = True
clock = pygame.time.Clock()

scene_manager = SceneManager(screen)

while running:
    dt = clock.tick(time_manager.max_fps) / 1000
    events = pygame.event.get()

    # Escape key quits the game
    for event in events:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
    if not running:
        break
    running = scene_manager.update(dt, events)

    # # Render FPS counter
    # fps_text = fps_font.render(f'FPS: {int(clock.get_fps())}', True, (255, 255, 255))
    # fps_rect = fps_text.get_rect(topright=(screen.get_width() - 10, 10))
    # screen.blit(fps_text, fps_rect)
    
    pygame.display.flip()

pygame.quit()
