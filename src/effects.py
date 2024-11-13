from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
import math
from typing import Callable, List, Optional, Tuple

import esper

from components.animation import AnimationState, AnimationType
from components.aoe import AoE
from components.armor import Armor
from components.attached import Attached
from components.expiration import Expiration
from components.health import Health
from components.orientation import FacingDirection, Orientation
from components.position import Position
from components.projectile import Projectile
from components.status_effect import CrusaderBlackKnightDebuffed, CrusaderCommanderEmpowered, StatusEffect, StatusEffects
from components.team import Team
from components.velocity import Velocity
from events import KILLING_BLOW, KillingBlowEvent, emit_event
from visuals import Visual, create_visual_spritesheet
from unit_condition import UnitCondition


class Recipient(Enum):
    """The recipient of an effect."""

    TARGET = auto()
    """The unit that is targetted/hit."""
    OWNER = auto()
    """The unit that owns the ability."""


class Effect:
    """An effect that an ability has."""

    @abstractmethod
    def apply(self, owner: int, parent: int, target: int) -> None:
        """Apply the effect."""


@dataclass
class Damages(Effect):
    """Effect deals damage to target."""

    damage: float
    """The damage dealt."""

    recipient: Recipient
    """The recipient of the effect."""

    def apply(self, owner: Optional[int], parent: int, target: int) -> None:
        if self.recipient == Recipient.OWNER:
            assert owner is not None
            recipient = owner
        else:
            recipient = target
            assert recipient is not None

        # Apply buffs/debuffs from the owner to the damage
        damage = self.damage
        applied_gold_knight_empowered = False
        applied_black_knight_debuffed = False
        if owner and esper.entity_exists(owner):
            status_effects = esper.component_for_entity(owner, StatusEffects)
            for status_effect in status_effects.active_effects():
                if isinstance(status_effect, CrusaderCommanderEmpowered) and not applied_gold_knight_empowered:
                    damage *= 1 + status_effect.damage_percentage
                    applied_gold_knight_empowered = True
                elif isinstance(status_effect, CrusaderBlackKnightDebuffed) and not applied_black_knight_debuffed:
                    damage *= 1 - status_effect.damage_percentage
                    applied_black_knight_debuffed = True

        # Apply armor to the damage
        recipient_health = esper.component_for_entity(recipient, Health)
        recipient_armor = esper.try_component(recipient, Armor)
        if recipient_armor:
            damage = recipient_armor.calculate_damage_after_armor(damage)
        if recipient_health is None:
            raise AssertionError("Recipient has no health component")

        # Apply the damage
        previous_health = recipient_health.current
        recipient_health.current = max(recipient_health.current - damage, 0)
        if recipient_health.current == 0 and previous_health > 0:
            emit_event(KILLING_BLOW, event=KillingBlowEvent(recipient))


@dataclass
class Heals(Effect):
    """Effect heals target."""

    amount: float
    """The amount healed."""

    recipient: Recipient
    """The recipient of the effect."""

    def apply(self, owner: Optional[int], parent: int, target: int) -> None:
        if self.recipient == Recipient.OWNER:
            recipient = owner
        else:
            recipient = target

        recipient_health = esper.component_for_entity(recipient, Health)
        recipient_health.current = min(recipient_health.current + self.amount, recipient_health.maximum)


@dataclass
class CreatesAoE(Effect):
    """Effect creates an AoE at the location of the parent."""

    effects: List[Effect]
    """The effect of the AoE."""

    duration: float
    """The duration of the AoE."""

    scale: float
    """The scale of the AoE."""

    unit_condition: "UnitCondition"
    """Condition that determines which units are affected by the AoE."""

    visual: Visual
    """The visual of the AoE."""

    visual_frames: Optional[Tuple[int, int]] = None
    """The frames of the visual of the AoE."""

    on_create: Optional[Callable[[int], None]] = None
    """Function to call when the AoE is created."""

    def apply(self, owner: Optional[int], parent: int, target: int) -> None:
        entity = esper.create_entity()
        position = esper.component_for_entity(parent, Position)
        team = esper.component_for_entity(parent, Team)
        orientation = esper.component_for_entity(parent, Orientation)
        esper.add_component(entity, Position(x=position.x, y=position.y))
        esper.add_component(entity, Team(type=team.type))
        esper.add_component(entity, AoE(
            effects=self.effects,
            owner=owner,
            unit_condition=self.unit_condition
        ))
        esper.add_component(entity, create_visual_spritesheet(
            visual=self.visual,
            scale=self.scale,
            duration=self.duration,
            frames=self.visual_frames
        ))
        esper.add_component(entity, AnimationState(type=AnimationType.IDLE))
        esper.add_component(entity, Expiration(time_left=self.duration))
        esper.add_component(entity, Orientation(facing=orientation.facing))
        if self.on_create:
            self.on_create(entity)


@dataclass
class CreatesProjectile(Effect):
    """Effect creates a projectile at the location of the parent.
    
    The projectile will move towards the target.
    """

    effects: List[Effect]
    """The effect of the projectile."""

    projectile_speed: float
    """The speed of the projectile."""

    visual: Visual
    """The visual of the projectile."""

    projectile_offset_x: float
    """The x offset of the projectile from the parent's position, in pixels.
    
    (Assuming the parent is facing right)
    """

    projectile_offset_y: float
    """The y offset of the projectile from the parent's position, in pixels."""

    on_create: Optional[Callable[[int], None]] = None
    """Function to call when the projectile is created."""

    def apply(self, owner: Optional[int], parent: int, target: int) -> None:
        entity = esper.create_entity()
        parent_position = esper.component_for_entity(parent, Position)
        parent_orientation = esper.component_for_entity(parent, Orientation)
        parent_team = esper.component_for_entity(parent, Team)
        projectile_x = parent_position.x + self.projectile_offset_x * parent_orientation.facing.value
        projectile_y = parent_position.y + self.projectile_offset_y

        target_position = esper.component_for_entity(target, Position)
        dx = target_position.x - projectile_x
        dy = target_position.y - projectile_y
        distance = math.sqrt(dx**2 + dy**2)
        if distance > 0:
            velocity_x = (dx / distance) * self.projectile_speed
            velocity_y = (dy / distance) * self.projectile_speed
        else:
            velocity_x = self.projectile_speed
            velocity_y = 0

        esper.add_component(entity, Position(x=projectile_x, y=projectile_y))
        esper.add_component(entity, Velocity(x=velocity_x, y=velocity_y))
        esper.add_component(entity, Team(type=parent_team.type))
        esper.add_component(entity, Projectile(effects=self.effects, owner=owner))
        esper.add_component(entity, Orientation(facing=FacingDirection.LEFT if dx < 0 else FacingDirection.RIGHT))
        esper.add_component(entity, create_visual_spritesheet(self.visual))
        esper.add_component(entity, AnimationState(type=AnimationType.IDLE))
        if self.on_create:
            self.on_create(entity)


@dataclass
class AppliesStatusEffect(Effect):
    """Effect applies a status effect to the target."""

    status_effect: StatusEffect
    """The status effect applied."""

    recipient: Recipient
    """The recipient of the status effect."""

    def apply(self, owner: Optional[int], parent: int, target: int) -> None:
        if self.recipient == Recipient.OWNER:
            recipient = owner
        elif self.recipient == Recipient.TARGET:
            recipient = target
        else:
            raise ValueError(f"Invalid recipient: {self.recipient}")
        recipient_status_effects = esper.component_for_entity(recipient, StatusEffects)
        recipient_status_effects.add(self.status_effect)


@dataclass
class CreatesAttachedVisual(Effect):
    """Effect creates a visual effect that is attached to the target."""

    visual: Visual
    """The visual of the effect."""

    animation_duration: float
    """The duration of the animation of the effect."""

    expiration_duration: float
    """The duration of the effect."""

    scale: float
    """The scale of the effect."""

    def apply(self, owner: Optional[int], parent: int, target: int) -> None:
        entity = esper.create_entity()
        position = esper.component_for_entity(target, Position)
        team = esper.component_for_entity(target, Team)
        esper.add_component(entity, Position(x=position.x, y=position.y))
        esper.add_component(entity, Team(type=team.type))
        esper.add_component(entity, Attached(entity=target))
        esper.add_component(entity, create_visual_spritesheet(self.visual, self.animation_duration))
        esper.add_component(entity, AnimationState(type=AnimationType.IDLE))
        esper.add_component(entity, Expiration(time_left=self.expiration_duration))
