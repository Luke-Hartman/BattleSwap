"""Conditions that a unit may or may not meet."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Type
import math

import esper

from components.ammo import Ammo
from components.entity_memory import EntityMemory
from components.health import Health
from components.hitbox import Hitbox
from components.immunity import ImmuneToZombieInfection
from components.orientation import Orientation
from components.position import Position
from components.stance import Stance
from components.status_effect import StatusEffects, ZombieInfection
from components.team import Team, TeamType
from components.unit_state import State, UnitState
from components.unit_type import UnitType, UnitTypeComponent
from components.airborne import Airborne

class UnitCondition(ABC):
    """A condition that a unit may or may not meet."""

    @abstractmethod
    def check(self, entity: int) -> bool:
        """Check if the condition is met for the given entity."""

@dataclass
class Always(UnitCondition):
    """The condition that is always met."""

    def check(self, entity: int) -> bool:
        return True

@dataclass
class Never(UnitCondition):
    """The condition that is never met."""

    def check(self, entity: int) -> bool:
        return False

@dataclass
class Not(UnitCondition):
    """The negation of the given condition."""

    condition: UnitCondition
    """The condition to negate."""

    def check(self, entity: int) -> bool:
        return not self.condition.check(entity)

@dataclass
class All(UnitCondition):
    """The conjunction of the given conditions."""

    conditions: List[UnitCondition]
    """The conditions to check."""

    def check(self, entity: int) -> bool:
        return all(condition.check(entity) for condition in self.conditions)

@dataclass
class Any(UnitCondition):
    """The disjunction of the given conditions."""

    conditions: List[UnitCondition]
    """The conditions to check."""

    def check(self, entity: int) -> bool:
        return any(condition.check(entity) for condition in self.conditions)

@dataclass
class Alive(UnitCondition):
    """The unit is alive."""

    def check(self, entity: int) -> bool:
        unit_state = esper.try_component(entity, UnitState)
        return unit_state is not None and unit_state.state != State.DEAD

@dataclass
class Grounded(UnitCondition):
    """The unit is grounded."""

    def check(self, entity: int) -> bool:
        return not esper.has_component(entity, Airborne)

@dataclass
class IsEntity(UnitCondition):
    """The unit is the given entity."""

    entity: int
    """The entity to check against."""

    def check(self, entity: int) -> bool:
        return entity == self.entity

@dataclass
class OnTeam(UnitCondition):
    """The unit is on the given team."""

    team: TeamType
    """The team to check against."""

    def check(self, entity: int) -> bool:
        team = esper.try_component(entity, Team)
        return team is not None and team.type == self.team


@dataclass
class HealthBelowPercent(UnitCondition):
    """The unit has less than `percent` health."""

    percent: float
    """The percent of health below which the condition is met."""

    def check(self, entity: int) -> bool:
        health = esper.try_component(entity, Health)
        return health is not None and health.current / health.maximum < self.percent

@dataclass
class MaxHealthAbove(UnitCondition):
    """The unit has at least `health` health."""

    health: float
    """The health to check against."""

    def check(self, entity: int) -> bool:
        health = esper.try_component(entity, Health)
        return health is not None and health.maximum >= self.health


@dataclass
class MaximumDistanceFromEntity(UnitCondition):
    """The unit is within a certain distance from the given entity."""

    entity: int
    """The entity to check against."""

    distance: float
    """The maximum distance within which the condition is met."""

    y_bias: Optional[float]
    """The y-bias to apply to the distance check."""

    use_hitbox: bool = True
    """Whether to use the hitbox to determine the distance."""

    def check(self, entity: int) -> bool:
        position = esper.try_component(self.entity, Position)
        other_position = esper.try_component(entity, Position)
        if position is None or other_position is None:
            return False
        if self.use_hitbox:
            other_hitbox = esper.try_component(entity, Hitbox)
            if other_hitbox is None:
                return False
            radius = min(other_hitbox.height/2, other_hitbox.width/2)
            distance = self.distance + radius
        else:
            distance = self.distance
        return position.distance(other_position, self.y_bias) <= distance

@dataclass
class MinimumDistanceFromEntity(UnitCondition):
    """The unit is at least  a certain distance from the given entity."""

    entity: int
    """The entity to check against."""

    distance: float
    """The minimum distance within which the condition is met."""

    y_bias: Optional[float]
    """The y-bias to apply to the distance check."""

    def check(self, entity: int) -> bool:
        position = esper.try_component(self.entity, Position)
        other_position = esper.try_component(entity, Position)
        if position is None or other_position is None:
            return False
        return position.distance(other_position, self.y_bias) >= self.distance

@dataclass
class MaximumAngleFromEntity(UnitCondition):
    """The unit is within a certain angle from the given entity."""

    entity: int
    """The entity to check against."""

    maximum_angle: float
    """The maximum angle (in radians) within which the condition is met."""

    def check(self, entity: int) -> bool:
        position = esper.try_component(self.entity, Position)
        other_position = esper.try_component(entity, Position)
        if position is None or other_position is None:
            return False
        
        angle = math.atan2(
            abs(other_position.y - position.y),
            abs(other_position.x - position.x)
        )
        return abs(angle) <= self.maximum_angle

@dataclass
class MaximumDistanceFromDestination(UnitCondition):
    """The unit is within a certain distance from their destination."""

    distance: float
    """The maximum distance within which the condition is met."""

    y_bias: Optional[float] = None
    """The y-bias to apply to the distance check."""

    def check(self, entity: int) -> bool:
        from components.destination import Destination
        position = esper.component_for_entity(entity, Position)
        destination = esper.component_for_entity(entity, Destination)
        team = esper.component_for_entity(entity, Team)
        orientation = esper.component_for_entity(entity, Orientation)
        target = destination.target_strategy.target
        target_position = esper.component_for_entity(target, Position)
        destination_position_x = target_position.x + destination.get_x_offset(team.type, orientation.facing)
        destination_position_y = target_position.y
        return position.distance(Position(destination_position_x, destination_position_y), self.y_bias) <= self.distance

@dataclass
class InStance(UnitCondition):
    """The unit is in the given stance."""

    stance: int
    """The required stance."""

    def check(self, entity: int) -> bool:
        return esper.component_for_entity(entity, Stance).stance == self.stance

@dataclass
class AmmoEquals(UnitCondition):
    """The unit has the given amount of ammo."""

    amount: int
    """The amount of ammo to check against."""

    def check(self, entity: int) -> bool:
        return esper.component_for_entity(entity, Ammo).current == self.amount

@dataclass
class RememberedBy(UnitCondition):
    """The unit is remembered by the given entity."""

    entity: int
    """The entity to check against."""

    def check(self, entity: int) -> bool:
        memory = esper.try_component(self.entity, EntityMemory)
        return memory is not None and memory.entity == entity

@dataclass
class RememberedSatisfies(UnitCondition):
    """Condition that the remembered entity must satisfy."""

    condition: UnitCondition
    """The condition that the remembered entity must satisfy."""

    def check(self, entity: int) -> bool:
        memory = esper.try_component(entity, EntityMemory)
        return memory is not None and self.condition.check(memory.entity)

@dataclass
class IsUnitType(UnitCondition):
    """The unit is of the given type."""

    unit_type: UnitType
    """The type of unit to check against."""

    def check(self, entity: int) -> bool:
        unit_type = esper.try_component(entity, UnitTypeComponent)
        return unit_type is not None and unit_type.type == self.unit_type

@dataclass
class Infected(UnitCondition):
    """The unit is infected with a zombie infection."""

    def check_return_team(self, entity: int) -> Optional[TeamType]:
        if not esper.has_component(entity, ImmuneToZombieInfection):
            status_effects = esper.component_for_entity(entity, StatusEffects)
            for effect in status_effects.active_effects():
                if isinstance(effect, ZombieInfection):
                    return effect.team
        return None

    def check(self, entity: int) -> bool:
        return self.check_return_team(entity) is not None


@dataclass
class HasComponent(UnitCondition):
    """The unit has the given component."""

    component: Type
    """The component to check against."""

    def check(self, entity: int) -> bool:
        return esper.has_component(entity, self.component)
