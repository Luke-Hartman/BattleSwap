#!/usr/bin/env python3
"""
Demonstration of the Upgrade System

This script shows how to use the new upgrade system in BattleSwap.
Run this script to see the upgrade window in action.
"""

import pygame
import pygame_gui
import sys
import os

# Add the src directory to the path so we can import from it
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from components.unit_type import UnitType
from ui_components.upgrade_window import UpgradeWindow
from upgrade_manager import upgrade_manager

def main():
    """Main demonstration function."""
    # Initialize Pygame
    pygame.init()
    
    # Set up the display
    screen = pygame.display.set_mode((1200, 800))
    pygame.display.set_caption("BattleSwap - Upgrade System Demo")
    
    # Create UI manager
    manager = pygame_gui.UIManager((1200, 800))
    
    # Create upgrade window for a Core Archer
    upgrade_window = UpgradeWindow(manager, UnitType.CORE_ARCHER)
    
    # Main game loop
    clock = pygame.time.Clock()
    running = True
    
    print("=== BattleSwap Upgrade System Demo ===")
    print(f"Starting with {upgrade_manager.get_upgrade_points()} upgrade points")
    print("Click on upgrade buttons to purchase them!")
    print("Press ESC to exit")
    
    while running:
        time_delta = clock.tick(60) / 1000.0
        
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_1:
                    # Switch to different unit types for testing
                    upgrade_window.close()
                    upgrade_window = UpgradeWindow(manager, UnitType.CORE_WIZARD)
                elif event.key == pygame.K_2:
                    upgrade_window.close()
                    upgrade_window = UpgradeWindow(manager, UnitType.CRUSADER_BLACK_KNIGHT)
                elif event.key == pygame.K_3:
                    upgrade_window.close()
                    upgrade_window = UpgradeWindow(manager, UnitType.ZOMBIE_BRUTE)
                elif event.key == pygame.K_p:
                    # Add 100 upgrade points for testing
                    upgrade_manager.add_upgrade_points(100)
                    upgrade_window.close()
                    upgrade_window = UpgradeWindow(manager, upgrade_window.unit_type)
            
            # Let the upgrade window handle events
            if upgrade_window.is_alive():
                upgrade_window.handle_event(event)
            
            # Process UI events
            manager.process_events(event)
        
        # Update
        manager.update(time_delta)
        
        # Check if upgrade window was closed
        if not upgrade_window.is_alive():
            print("Upgrade window closed. Opening new one...")
            upgrade_window = UpgradeWindow(manager, UnitType.CORE_ARCHER)
        
        # Render
        screen.fill((30, 30, 40))  # Dark background
        manager.draw_ui(screen)
        
        # Draw instructions
        font = pygame.font.Font(None, 24)
        instructions = [
            "BattleSwap Upgrade System Demo",
            f"Current Upgrade Points: {upgrade_manager.get_upgrade_points()}",
            "",
            "Controls:",
            "• Click upgrade buttons to purchase",
            "• Press 1 for Wizard upgrades",
            "• Press 2 for Black Knight upgrades", 
            "• Press 3 for Zombie Brute upgrades",
            "• Press P to add 100 upgrade points",
            "• Press ESC to exit"
        ]
        
        y_offset = 10
        for instruction in instructions:
            if instruction:  # Skip empty lines
                text_surface = font.render(instruction, True, (255, 255, 255))
                screen.blit(text_surface, (10, y_offset))
            y_offset += 25
        
        pygame.display.flip()
    
    # Cleanup
    pygame.quit()
    
    # Print final state
    print("\n=== Final Upgrade State ===")
    print(f"Remaining upgrade points: {upgrade_manager.get_upgrade_points()}")
    
    for unit_type in UnitType:
        owned_upgrades = upgrade_manager.get_owned_upgrades(unit_type)
        if owned_upgrades:
            print(f"{unit_type.name}: {owned_upgrades}")
            effects = upgrade_manager.get_upgrade_effects(unit_type)
            if effects:
                print(f"  Effects: {effects}")


if __name__ == "__main__":
    main()