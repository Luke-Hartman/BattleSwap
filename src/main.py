"""
Main game module for Battle Swap.

This module initializes the game, sets up the display, creates processors,
and runs the main game loop.
"""

import pygame
from entities.units import load_sprite_sheets
from handlers.combat_handler import CombatHandler
from handlers.sound_handler import SoundHandler
from handlers.state_machine import StateMachine
from scenes.scene_manager import SceneManager
from visuals import load_visual_sheets
from game_constants import gc
import steam

# Initialize Pygame
pygame.init()

# Initialize Steamworks
steam.init_steam()

# Set up the display
# Use the full screen

# This is slightly awkward, but it let's us
# 1. Get the correct screen size
# 2. Use the "SCALED" flag, which is apparently required for the steam overlay
screen = pygame.display.set_mode((0, 0),pygame.FULLSCREEN)
screen_width, screen_height = screen.get_size()
screen = pygame.display.set_mode(
    (screen_width, screen_height),
    pygame.SCALED
)
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

    # # Render FPS counter
    # fps_text = fps_font.render(f'FPS: {int(clock.get_fps())}', True, (255, 255, 255))
    # fps_rect = fps_text.get_rect(topright=(screen.get_width() - 10, 10))
    # screen.blit(fps_text, fps_rect)
    
    pygame.display.flip()

pygame.quit()
