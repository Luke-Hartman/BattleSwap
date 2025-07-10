"""Module for managing test battles."""
import os
import sys
import pygame
from auto_battle import simulate_battle, BattleOutcome
from battles import get_battles
from entities.units import load_sprite_sheets
from handlers.combat_handler import CombatHandler
from handlers.state_machine import StateMachine
from visuals import load_visual_sheets
from unit_values import unit_values

def run_tests() -> bool:
    """Run all test battles and return True if all tests pass."""
    os.environ['SDL_VIDEODRIVER'] = 'dummy'

    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Battle Swap")
    load_sprite_sheets()
    load_visual_sheets()
    combat_handler = CombatHandler()
    state_machine = StateMachine()

    failed = []
    for battle in get_battles():
        if battle.is_test:
            outcome = simulate_battle(battle.allies, battle.enemies, max_duration=60)
            print(f"{battle.id}: {outcome}")
            if outcome != BattleOutcome.TEAM1_VICTORY:
                failed.append(battle.id)
    
    if failed:
        print(f"Failed tests: {failed}", file=sys.stderr)
        return False

    failed = False
    for battle in get_battles():
        if battle.best_solution is not None:
            points_used = sum(unit_values[unit_type] for unit_type, _ in battle.best_solution)
            # Run a simulation to check that the best_solution is a valid solution
            outcome = simulate_battle(battle.best_solution, battle.enemies, max_duration=float("inf"))
            print(f"{battle.id}: {outcome}")
            if outcome != BattleOutcome.TEAM1_VICTORY:
                print(f"Battle {battle.id} has a best_solution that doesn't win.")
                failed = True
    return not failed

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)

