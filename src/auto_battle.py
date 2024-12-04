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
from processors.movement_processor import MovementProcessor
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

def get_unit_placements(team_type: TeamType) -> List[Tuple[UnitType, Tuple[int, int]]]:
    return [
        (unit_type.type, (pos.x, pos.y))
        for ent, (unit_type, team, pos) in esper.get_components(UnitTypeComponent, Team, Position)
        if team.type == team_type
    ]

class AutoBattle:

    def __init__(
        self,
        ally_placements: List[Tuple[UnitType, Tuple[int, int]]],
        enemy_placements: List[Tuple[UnitType, Tuple[int, int]]],
        max_duration: float,
    ):
        for unit_type, position in ally_placements:
            create_unit(x=position[0], y=position[1], unit_type=unit_type, team=TeamType.TEAM1)
        for unit_type, position in enemy_placements:
            create_unit(x=position[0], y=position[1], unit_type=unit_type, team=TeamType.TEAM2)
        unique_processor = UniqueProcessor()
        targetting_processor = TargettingProcessor()
        idle_processor = IdleProcessor()
        fleeing_processor = FleeingProcessor()
        ability_processor = AbilityProcessor()
        dead_processor = DeadProcessor()
        aura_processor = AuraProcessor()
        movement_processor = MovementProcessor()
        pursuing_processor = PursuingProcessor()
        collision_processor = CollisionProcessor()
        attached_processor = AttachedProcessor()
        expiration_processor = ExpirationProcessor()
        status_effect_processor = StatusEffectProcessor()
        animation_processor = AnimationProcessor()
        orientation_processor = OrientationProcessor()
        position_processor = PositionProcessor()
        rotation_processor = RotationProcessor()
        dying_processor = DyingProcessor()
        esper.add_processor(targetting_processor)
        esper.add_processor(idle_processor)
        esper.add_processor(fleeing_processor)
        esper.add_processor(ability_processor)
        esper.add_processor(pursuing_processor)
        esper.add_processor(dead_processor)
        esper.add_processor(aura_processor)
        esper.add_processor(movement_processor)
        esper.add_processor(collision_processor)
        esper.add_processor(attached_processor)
        esper.add_processor(expiration_processor)
        esper.add_processor(status_effect_processor)
        esper.add_processor(animation_processor)
        esper.add_processor(position_processor)
        esper.add_processor(orientation_processor)
        esper.add_processor(rotation_processor)
        esper.add_processor(unique_processor)
        esper.add_processor(dying_processor)
        self.remaining_time = max_duration
        self.battle_outcome = None

    def update(self, dt: float) -> Optional[BattleOutcome]:
        if self.battle_outcome is not None:
            return self.battle_outcome
        self.remaining_time -= dt
        if self.remaining_time <= 0:
            return BattleOutcome.TIMEOUT

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
    outcome = None
    auto_battle = AutoBattle(ally_placements, enemy_placements, max_duration)
    while outcome is None:
        esper.process(1/60)
        outcome = auto_battle.update(1/60)
    esper.switch_world(previous_world)
    esper.delete_world("simulation")
    return outcome