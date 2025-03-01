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
    return True

def check_all_battles_have_grades() -> bool:
    """Check that all battles have grades."""
    failed = False
    for battle in get_battles():
        if battle.grades is None and not battle.is_test:
            print(f"Battle {battle.id} has no grades", file=sys.stderr)
            failed = True
    return not failed

if __name__ == "__main__":
    success = run_tests() and check_all_battles_have_grades()
    sys.exit(0 if success else 1)

