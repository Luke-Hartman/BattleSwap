"""Combat processor for the Battle Swap game."""

import esper
import math
from components.position import Position
from components.health import Health
from components.combat import Combat
from components.team import Team, TeamType
from components.animation import Animation

class CombatProcessor(esper.Processor):
    """Processor responsible for handling combat interactions."""

    def __init__(self, animation_processor):
        self.animation_processor = animation_processor
        self.battle_ended = False

    def process(self):
        """Process combat for all entities with Combat components."""
        if self.battle_ended:
            return

        combatants = list(esper.get_components(Position, Health, Combat, Team, Animation))
        
        if self.check_battle_end():
            return

        self.process_combat(combatants)

    def check_battle_end(self):
        """Check if the battle has ended."""
        alive_teams = {team.team_type for _, (health, team) in esper.get_components(Health, Team) 
                       if health.current_health > 0}

        if len(alive_teams) <= 1 and not self.battle_ended:
            self.battle_ended = True
            self.animation_processor.set_battle_ended(True)
            return True
        return False

    def process_combat(self, combatants):
        """Process combat for all combatants."""
        for ent1, (pos1, health1, combat1, team1, anim1) in combatants:
            if health1.current_health <= 0 or combat1.current_cooldown > 0:
                combat1.current_cooldown = max(0, combat1.current_cooldown - 1)
                continue

            target = self.find_target(ent1, pos1, combat1, team1, combatants)
            if target:
                self.perform_attack(ent1, combat1, anim1, target)

    def find_target(self, ent1, pos1, combat1, team1, combatants):
        """Find a valid target for the given entity."""
        for ent2, (pos2, health2, _, team2, _) in combatants:
            if ent1 == ent2 or team1.team_type == team2.team_type or health2.current_health <= 0:
                continue

            distance = math.sqrt((pos1.x - pos2.x)**2 + (pos1.y - pos2.y)**2)
            if distance <= combat1.attack_range:
                return ent2, health2
        return None

    def perform_attack(self, attacker, combat, anim, target):
        """Perform an attack on the target."""
        ent2, health2 = target
        health2.current_health -= combat.attack_damage
        combat.current_cooldown = combat.attack_cooldown
        anim.row = 3  # Assuming row 3 is the attack animation
        anim.current_frame = 0
