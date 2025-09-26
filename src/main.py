"""
Main game module for Battle Swap.

This module initializes the game, sets up the display, creates processors,
and runs the main game loop.
"""

import argparse
import sys
import pygame
from entities.units import load_sprite_sheets
from entities.spells import load_spell_icons
from entities.items import load_item_icons
from handlers.combat_handler import CombatHandler
from handlers.sound_handler import SoundHandler
from handlers.state_machine import StateMachine
from scenes.scene_manager import scene_manager
from selected_unit_manager import selected_unit_manager
import timing
from visuals import load_visual_sheets
from info_mode_manager import info_mode_manager
#import steam

# Initialize Pygame
pygame.init()

# Initialize Steamworks
#steam.init_steam()

# Set up the display
# Use the full screen

# This is slightly awkward, but it let's us
# 1. Get the correct screen size
# 2. Use the "SCALED" flag, which is apparently required for the steam overlay
screen = pygame.display.set_mode((0, 0),pygame.FULLSCREEN)
screen_width, screen_height = screen.get_size()
screen = pygame.display.set_mode(
    (screen_width, screen_height),
    pygame.SCALED | pygame.FULLSCREEN
)
pygame.display.set_caption("Battle Swap")

# Initialize font for FPS counter
fps_font = pygame.font.SysFont('Arial', 30)

# Load sprite sheets
load_sprite_sheets()
load_spell_icons()
load_item_icons()
load_visual_sheets()

combat_handler = CombatHandler()
state_machine = StateMachine()
sound_handler = SoundHandler()


parser = argparse.ArgumentParser()
parser.add_argument("--no_dev", action="store_true", default=False)
args = parser.parse_args()

scene_manager.initialize(screen, developer_mode=not args.no_dev)
selected_unit_manager.initialize(scene_manager.manager)

# Main game loop
running = True
clock = pygame.time.Clock()
while running:
    dt = clock.tick(timing.get_max_fps()) / 1000
    events = pygame.event.get()

    # Process modifier key events for info mode before scene processing
    for event in events:
        if event.type == pygame.KEYDOWN:
            # Check for the appropriate modifier key based on platform
            modifier_pressed = False
            if sys.platform == 'darwin':
                # macOS: Use Command key
                modifier_pressed = event.key == pygame.K_LMETA or event.key == pygame.K_RMETA
            else:
                # Windows/Linux: Use Alt key
                modifier_pressed = event.key == pygame.K_LALT or event.key == pygame.K_RALT
                
            if modifier_pressed:
                old_info_mode = info_mode_manager.info_mode
                info_mode_manager.info_mode = not info_mode_manager.info_mode
                
                # Handle mode transitions
                if old_info_mode and not info_mode_manager.info_mode:
                    # Exiting info mode - clear all cards
                    selected_unit_manager.clear_all_cards()
                elif not old_info_mode and info_mode_manager.info_mode:
                    # Entering info mode - no special handling needed with unified cards list
                    pass
                
        # Process selected unit manager events (for future interactive features)
        selected_unit_manager.process_events(event)

    running = scene_manager.update(dt, events)
    
    # # Render FPS counter
    # fps_text = fps_font.render(f'FPS: {int(clock.get_fps())}', True, (255, 255, 255))
    # fps_rect = fps_text.get_rect(topright=(screen.get_width() - 10, 10))
    # screen.blit(fps_text, fps_rect)
    
    pygame.display.flip()
    timing.tick()

pygame.quit()
