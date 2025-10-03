from enum import Enum, auto
from typing import Any, Callable, Optional, Tuple, List, Union

import esper

from components.position import Position
from components.team import Team, TeamType
from components.unit_state import State, UnitState
from components.unit_tier import UnitTier
from components.unit_type import UnitType, UnitTypeComponent
from components.corpse_timer import CorpseTimer
from game_constants import gc
from entities.items import ItemType

from corruption_powers import CorruptionPower
from processors.ability_processor import AbilityProcessor
from processors.attached_processor import AttachedProcessor
from processors.aura_processor import AuraProcessor
from processors.collision_processor import CollisionProcessor
from processors.dead_processor import DeadProcessor
from processors.dying_processor import DyingProcessor
from processors.expiration_processor import ExpirationProcessor
from processors.fleeing_processor import FleeingProcessor
from processors.idle_processor import IdleProcessor
from processors.animation_processor import AnimationProcessor
from processors.lobbed_processor import LobbedProcessor
from processors.velocity_processor import VelocityProcessor
from processors.nudge_processor import NudgeProcessor
from processors.orientation_processor import OrientationProcessor
from processors.position_processor import PositionProcessor
from processors.pursuing_processor import PursuingProcessor
from processors.rotation_processor import RotationProcessor

from processors.status_effect_processor import StatusEffectProcessor
from processors.targetting_processor import TargettingProcessor
from processors.unique_processor import UniqueProcessor
from entities.units import create_unit
from processors.visual_link_processor import VisualLinkProcessor
from processors.repeat_processor import RepeatProcessor
from processors.spell_effects_processor import SpellEffectsProcessor
from processors.volley_projectile_processor import VolleyProjectileProcessor

class BattleOutcome(Enum):
    TEAM1_VICTORY = auto()
    TEAM2_VICTORY = auto()
    TIMEOUT = auto()



class AutoBattle:

    def __init__(
        self,
        max_duration: float,
        hex_coords: Tuple[int, int],
    ):
        def _add_or_replace(processor: esper.Processor):
            if esper.get_processor(type(processor)) is not None:
                esper.remove_processor(type(processor))
            esper.add_processor(processor)

        _add_or_replace(TargettingProcessor())
        _add_or_replace(IdleProcessor())
        _add_or_replace(FleeingProcessor())
        _add_or_replace(AbilityProcessor())
        _add_or_replace(PursuingProcessor())
        _add_or_replace(DeadProcessor())
        _add_or_replace(AuraProcessor())
        _add_or_replace(VelocityProcessor())
        _add_or_replace(LobbedProcessor())
        _add_or_replace(CollisionProcessor(hex_coords))
        _add_or_replace(AttachedProcessor())
        _add_or_replace(ExpirationProcessor())
        _add_or_replace(StatusEffectProcessor())
        _add_or_replace(AnimationProcessor())
        _add_or_replace(PositionProcessor())
        _add_or_replace(VisualLinkProcessor())
        _add_or_replace(RepeatProcessor())
        _add_or_replace(NudgeProcessor())
        _add_or_replace(OrientationProcessor())
        _add_or_replace(RotationProcessor())
        _add_or_replace(UniqueProcessor())
        _add_or_replace(DyingProcessor())
        _add_or_replace(SpellEffectsProcessor())
        _add_or_replace(VolleyProjectileProcessor())
        self.remaining_time = max_duration
        self.battle_outcome = None

    def update(self, dt: float) -> Optional[BattleOutcome]:
        if self.battle_outcome is not None:
            return self.battle_outcome
        self.remaining_time -= dt
        if self.remaining_time <= 0:
            self.battle_outcome = BattleOutcome.TIMEOUT
            return self.battle_outcome

        team1_alive = False
        team2_alive = False
        team1_all_dead_long_enough = True
        team2_all_dead_long_enough = True
        
        # Check each unit to determine alive status and if teams have been dead long enough
        for ent, (unit_state, team) in esper.get_components(UnitState, Team):
            if team.type == TeamType.TEAM1:
                if unit_state.state != State.DEAD:
                    team1_alive = True
                    team1_all_dead_long_enough = False
                elif esper.has_component(ent, CorpseTimer):
                    corpse_timer = esper.component_for_entity(ent, CorpseTimer)
                    if corpse_timer.time_dead < gc.CORPSE_TIMER_DURATION:
                        team1_all_dead_long_enough = False
            elif team.type == TeamType.TEAM2:
                if unit_state.state != State.DEAD:
                    team2_alive = True
                    team2_all_dead_long_enough = False
                elif esper.has_component(ent, CorpseTimer):
                    corpse_timer = esper.component_for_entity(ent, CorpseTimer)
                    if corpse_timer.time_dead < gc.CORPSE_TIMER_DURATION:
                        team2_all_dead_long_enough = False

        # Check if battle should end (either team has been dead long enough)
        if team1_all_dead_long_enough or team2_all_dead_long_enough:
            # Case 1: Team with living units wins
            if team2_alive:
                assert not team1_alive
                self.battle_outcome = BattleOutcome.TEAM2_VICTORY
            elif team1_alive:
                assert not team2_alive
                self.battle_outcome = BattleOutcome.TEAM1_VICTORY
            # Case 2: Team 1 wins if both teams are dead
            else:
                assert not team1_alive and not team2_alive
                self.battle_outcome = BattleOutcome.TEAM1_VICTORY
        return self.battle_outcome

def simulate_battle(
    ally_placements: List[Tuple[UnitType, Tuple[float, float], List]],
    enemy_placements: List[Tuple[UnitType, Tuple[float, float], List]],
    max_duration: float,
    corruption_powers: Optional[List[CorruptionPower]] = None,
    spell_placements: Optional[List[Tuple]] = None,
    post_battle_callback: Optional[Callable[[BattleOutcome], Any]] = None,
) -> Union[BattleOutcome, Tuple[BattleOutcome, Any]]:
    """Simulate a battle between two teams.
    
    Args:
        ally_placements: List of (unit_type, position, items) tuples for team 1.
        enemy_placements: List of (unit_type, position, items) tuples for team 2.
        max_duration: Maximum duration for the battle in seconds.
        corruption_powers: Optional list of corruption powers to apply to units.
        spell_placements: Optional list of (spell_type, position, team) tuples for spells.
        post_battle_callback: Optional callback to be called after the battle.
    
    Returns:
        The outcome of the battle, or a tuple of (outcome, post_battle_callback_result)
        if the callback is provided.
    """
    previous_world = esper.current_world
    esper.switch_world("simulation")
    # TODO: THIS IS A HACK - I HAVE HARDCODED THE ALLY AND ENEMY TIERS.

    # Create units for both teams
    for unit_type, position, items in ally_placements:
        create_unit(x=position[0], y=position[1], unit_type=unit_type, team=TeamType.TEAM1, corruption_powers=corruption_powers, tier=UnitTier.ELITE, items=items)
    for unit_type, position, items in enemy_placements:
        create_unit(x=position[0], y=position[1], unit_type=unit_type, team=TeamType.TEAM2, corruption_powers=corruption_powers, tier=UnitTier.ELITE, items=items)
    
    # Create spells if provided
    if spell_placements:
        from entities.spells import create_spell
        for spell_type, position, team_value in spell_placements:
            team = TeamType(team_value)
            create_spell(x=position[0], y=position[1], spell_type=spell_type, team=team, corruption_powers=corruption_powers)
    
    # Run the battle simulation
    outcome = None
    auto_battle = AutoBattle(max_duration, hex_coords=(0, 0))
    while outcome is None:
        esper.process(1/30)
        outcome = auto_battle.update(1/30)
    
    if post_battle_callback is not None:
        post_battle_callback_result = post_battle_callback(outcome)
    else:
        post_battle_callback_result = None

    # Switch back to the previous world
    esper.switch_world(previous_world)
    esper.delete_world("simulation")
    
    if post_battle_callback is not None:
        return outcome, post_battle_callback_result
    else:
        return outcome

def simulate_battle_with_dependencies(
    ally_placements: List[Tuple[UnitType, Tuple[float, float], List]],
    enemy_placements: List[Tuple[UnitType, Tuple[float, float], List]],
    max_duration: float,
    corruption_powers: Optional[List[CorruptionPower]] = None,
    spell_placements: Optional[List[Tuple]] = None,
    post_battle_callback: Optional[Callable[[BattleOutcome], Any]] = None,
) -> Union[BattleOutcome, Tuple[BattleOutcome, Any]]:
    import os
    import pygame
    from handlers.combat_handler import CombatHandler
    from handlers.state_machine import StateMachine
    from visuals import load_visual_sheets
    from entities.units import load_sprite_sheets
    from entities.spells import load_spell_icons
    from entities.items import load_item_icons

    os.environ['SDL_VIDEODRIVER'] = 'dummy'
    pygame.display.init()
    pygame.display.set_mode((800, 600))
    load_sprite_sheets()
    load_spell_icons()
    load_item_icons()
    load_visual_sheets()
    combat_handler = CombatHandler()
    state_machine = StateMachine()
    return simulate_battle(ally_placements, enemy_placements, max_duration, corruption_powers, spell_placements, post_battle_callback)