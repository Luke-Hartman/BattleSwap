from enum import Enum, auto
from typing import Optional

import esper

from components.position import Position
from components.team import Team, TeamType
from components.unit_state import State, UnitState
from components.unit_type import UnitType, UnitTypeComponent

from typing import List, Tuple
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
from processors.movement_processor import MovementProcessor
from processors.nudge_processor import NudgeProcessor
from processors.orientation_processor import OrientationProcessor
from processors.position_processor import PositionProcessor
from processors.pursuing_processor import PursuingProcessor
from processors.rotation_processor import RotationProcessor
from processors.status_effect_processor import StatusEffectProcessor
from processors.targetting_processor import TargettingProcessor
from processors.unique_processor import UniqueProcessor
from entities.units import create_unit

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
        def _add_if_new(processor: esper.Processor):
            if esper.get_processor(type(processor)) is None:
                esper.add_processor(processor)

        _add_if_new(TargettingProcessor())
        _add_if_new(IdleProcessor())
        _add_if_new(FleeingProcessor())
        _add_if_new(AbilityProcessor())
        _add_if_new(PursuingProcessor())
        _add_if_new(DeadProcessor())
        _add_if_new(AuraProcessor())
        _add_if_new(MovementProcessor())
        _add_if_new(LobbedProcessor())
        _add_if_new(CollisionProcessor(hex_coords))
        _add_if_new(AttachedProcessor())
        _add_if_new(ExpirationProcessor())
        _add_if_new(StatusEffectProcessor())
        _add_if_new(AnimationProcessor())
        _add_if_new(PositionProcessor())
        _add_if_new(NudgeProcessor())
        _add_if_new(OrientationProcessor())
        _add_if_new(RotationProcessor())
        _add_if_new(UniqueProcessor())
        _add_if_new(DyingProcessor())
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
        for ent, (unit_state, team) in esper.get_components(UnitState, Team):
            if team.type == TeamType.TEAM1 and unit_state.state != State.DEAD:
                team1_alive = True
            elif team.type == TeamType.TEAM2 and unit_state.state != State.DEAD:
                team2_alive = True
            if team1_alive and team2_alive:
                break

        if team1_alive and not team2_alive:
            self.battle_outcome = BattleOutcome.TEAM1_VICTORY
        elif not team1_alive and team2_alive:
            self.battle_outcome = BattleOutcome.TEAM2_VICTORY
        elif not team1_alive and not team2_alive:
            self.battle_outcome = BattleOutcome.TEAM1_VICTORY
        return self.battle_outcome

def simulate_battle(
    ally_placements: List[Tuple[UnitType, Tuple[int, int]]],
    enemy_placements: List[Tuple[UnitType, Tuple[int, int]]],
    max_duration: float,
) -> BattleOutcome:
    previous_world = esper.current_world
    esper.switch_world("simulation")
    for unit_type, position in ally_placements:
        create_unit(x=position[0], y=position[1], unit_type=unit_type, team=TeamType.TEAM1)
    for unit_type, position in enemy_placements:
        create_unit(x=position[0], y=position[1], unit_type=unit_type, team=TeamType.TEAM2)
    outcome = None
    auto_battle = AutoBattle(max_duration, hex_coords=(0, 0))
    while outcome is None:
        esper.process(1/60)
        outcome = auto_battle.update(1/60)
    esper.switch_world(previous_world)
    esper.delete_world("simulation")
    return outcome