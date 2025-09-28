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
from components.unusable_corpse import UnusableCorpse
from components.orientation import Orientation
from components.position import Position
from components.stance import Stance
from components.status_effect import StatusEffects, ZombieInfection
from components.team import Team, TeamType
from components.unit_state import State, UnitState
from components.unit_type import UnitType, UnitTypeComponent
from components.airborne import Airborne
from components.armor import Armor, ArmorLevel

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
        for condition in self.conditions:
            if not condition.check(entity):
                return False
        return True

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
    """The unit is within a certain distance to any point on the given entity."""

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
        if self.use_hitbox and (other_hitbox := esper.try_component(entity, Hitbox)):
            half_width = other_hitbox.width / 2
            half_height = other_hitbox.height / 2
            
            # You can find the nearest point on the other's hitbox by clamping the entity's position
            # to the other's hitbox
            nearest_x = max(other_position.x - half_width, min(position.x, other_position.x + half_width))
            nearest_y = max(other_position.y - half_height, min(position.y, other_position.y + half_height))
            other_position = Position(nearest_x, nearest_y)

        return position.distance(other_position, self.y_bias) <= self.distance

@dataclass
class MinimumDistanceFromEntity(UnitCondition):
    """The unit is at least a certain distance from every point on the given entity."""

    entity: int
    """The entity to check against."""

    distance: float
    """The minimum distance within which the condition is met."""

    y_bias: Optional[float]
    """The y-bias to apply to the distance check."""

    use_hitbox: bool = True
    """Whether to use the hitbox to determine the distance."""

    def check(self, entity: int) -> bool:
        position = esper.try_component(self.entity, Position)
        other_position = esper.try_component(entity, Position)
        if position is None or other_position is None:
            return False
        if self.use_hitbox and (other_hitbox := esper.try_component(entity, Hitbox)):
            half_width = other_hitbox.width / 2
            half_height = other_hitbox.height / 2

            # other_position is the midpoint between position and opposite_position 
            offset_x = position.x - other_position.x
            offset_y = position.y - other_position.y
            opposite_position = Position(
                other_position.x - offset_x,
                other_position.y - offset_y
            )

            # The farthest point on the other's hitbox can be found by clamping opposite_position to the hitbox
            farthest_x = max(other_position.x - half_width, min(opposite_position.x, other_position.x + half_width))
            farthest_y = max(other_position.y - half_height, min(opposite_position.y, other_position.y + half_height))
            other_position = Position(farthest_x, farthest_y)
        return position.distance(other_position, self.y_bias) > self.distance

@dataclass
class MaximumAngleFromEntity(UnitCondition):
    """The unit is within a certain angle from the given entity."""

    entity: int
    """The entity to check against."""

    maximum_angle: float
    """The maximum angle (in radians) within which the condition is met."""

    def check(self, entity: int) -> bool:
        # TODO: Use hitbox
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
    """The unit's position is within a certain distance from their destination."""

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
        return memory is not None and esper.entity_exists(memory.entity) and self.condition.check(memory.entity)

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

    def get_active_zombie_infection(self, entity: int) -> Optional[ZombieInfection]:
        status_effects = esper.component_for_entity(entity, StatusEffects)
        for effect in status_effects.active_effects():
            if isinstance(effect, ZombieInfection):
                return effect
        return None

    def check(self, entity: int) -> bool:
        return self.get_active_zombie_infection(entity) is not None


@dataclass
class HasComponent(UnitCondition):
    """The unit has the given component."""

    component: Type
    """The component to check against."""

    def check(self, entity: int) -> bool:
        return esper.has_component(entity, self.component)


@dataclass
class HasStatusEffect(UnitCondition):
    """The unit has the given status effect."""

    status_effect_class: Type
    """The class of status effect to check for."""

    def check(self, entity: int) -> bool:
        if not esper.has_component(entity, StatusEffects):
            return False
        status_effects = esper.component_for_entity(entity, StatusEffects)
        return any(isinstance(effect, self.status_effect_class) for effect in status_effects.active_effects())


@dataclass
class NotHeavilyArmored(UnitCondition):
    """The unit is not heavily armored (either has no armor or normal armor)."""

    def check(self, entity: int) -> bool:
        if not esper.has_component(entity, Armor):
            return True  # No armor means not heavily armored
        armor = esper.component_for_entity(entity, Armor)
        return armor.level != ArmorLevel.HEAVILY
