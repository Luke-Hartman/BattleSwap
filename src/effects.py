from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
import math
import random
from typing import Callable, List, Optional, Tuple, Union

import esper

from components.ammo import Ammo
from components.angle import Angle
from components.animation import AnimationState, AnimationType
from components.aoe import AoE
from components.armor import Armor
from components.attached import Attached
from components.aura import Aura
from components.dying import Dying
from components.entity_memory import EntityMemory
from components.expiration import Expiration
from components.health import Health
from components.orientation import FacingDirection, Orientation
from components.position import Position
from components.projectile import Projectile
from components.stance import Stance
from components.status_effect import CrusaderCommanderEmpowered, StatusEffect, StatusEffects
from components.team import Team
from components.unique import Unique
from components.velocity import Velocity
from events import PLAY_SOUND, PlaySoundEvent, emit_event
from visuals import Visual, create_visual_spritesheet
from unit_condition import UnitCondition


class Recipient(Enum):
    """The recipient of an effect."""

    TARGET = auto()
    """The unit that is targetted/hit."""
    PARENT = auto()
    """The parent of the effect."""
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

    on_kill_effects: Optional[List[Effect]] = None
    """Effects to apply when the target is killed."""

    def apply(self, owner: Optional[int], parent: int, target: int) -> None:
        if self.recipient == Recipient.OWNER:
            assert owner is not None
            recipient = owner
        elif self.recipient == Recipient.PARENT:
            recipient = parent
        elif self.recipient == Recipient.TARGET:
            recipient = target
        else:
            raise ValueError(f"Invalid recipient: {self.recipient}")

        # Apply buffs/debuffs from the owner to the damage
        damage = self.damage
        applied_gold_knight_empowered = False
        if owner and esper.entity_exists(owner):
            status_effects = esper.component_for_entity(owner, StatusEffects)
            for status_effect in status_effects.active_effects():
                if isinstance(status_effect, CrusaderCommanderEmpowered) and not applied_gold_knight_empowered:
                    damage *= 1 + status_effect.damage_percentage
                    applied_gold_knight_empowered = True

        # Apply armor to the damage
        recipient_health = esper.component_for_entity(recipient, Health)
        recipient_armor = esper.try_component(recipient, Armor)
        if recipient_armor:
            damage = recipient_armor.calculate_damage_after_armor(damage)
            emit_event(PLAY_SOUND, event=PlaySoundEvent(filename=f"sword_hitting_armor{random.randint(1, 4)}.wav", volume=0.50))
        else:
            emit_event(PLAY_SOUND, event=PlaySoundEvent(filename="arrow_hitting_flesh.wav", volume=0.50))
        if recipient_health is None:
            raise AssertionError("Recipient has no health component")

        # Apply the damage
        previous_health = recipient_health.current
        recipient_health.current = max(recipient_health.current - damage, 0)
        if recipient_health.current == 0 and previous_health > 0:
            esper.add_component(recipient, Dying())
            if self.on_kill_effects:
                for effect in self.on_kill_effects:
                    effect.apply(owner, parent, recipient)


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
        elif self.recipient == Recipient.PARENT:
            recipient = parent
        elif self.recipient == Recipient.TARGET:
            recipient = target
        else:
            raise ValueError(f"Invalid recipient: {self.recipient}")

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

    location: Recipient
    """The location of the AoE."""

    visual_frames: Optional[Tuple[int, int]] = None
    """The frames of the visual of the AoE."""

    on_create: Optional[Callable[[int], None]] = None
    """Function to call when the AoE is created."""

    def apply(self, owner: Optional[int], parent: int, target: int) -> None:
        entity = esper.create_entity()
        if self.location == Recipient.OWNER:
            recipient = owner
        elif self.location == Recipient.PARENT:
            recipient = parent
        elif self.location == Recipient.TARGET:
            recipient = target
        else:
            raise ValueError(f"Invalid location: {self.location}")
        position = esper.component_for_entity(recipient, Position)
        team = esper.component_for_entity(recipient, Team)
        orientation = esper.try_component(recipient, Orientation)
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
            duration=self.duration + 1/30,
            frames=self.visual_frames
        ))
        esper.add_component(entity, AnimationState(type=AnimationType.IDLE))
        esper.add_component(entity, Expiration(time_left=self.duration))
        if orientation is not None:
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
        angle = math.atan2(dy, dx)
        if parent_orientation.facing == FacingDirection.LEFT:
            angle = math.pi + angle

        esper.add_component(entity, Position(x=projectile_x, y=projectile_y))
        esper.add_component(entity, Velocity(x=velocity_x, y=velocity_y))
        esper.add_component(entity, Angle(angle=angle))
        esper.add_component(entity, Orientation(facing=parent_orientation.facing))
        esper.add_component(entity, Team(type=parent_team.type))
        esper.add_component(entity, Projectile(effects=self.effects, owner=owner))
        esper.add_component(entity, create_visual_spritesheet(self.visual))
        esper.add_component(entity, AnimationState(type=AnimationType.IDLE))
        if self.on_create:
            self.on_create(entity)


@dataclass
class CreatesTemporaryAura(Effect):
    """Effect creates a temporary aura attached to the target."""

    radius: float
    """The radius of the aura."""

    duration: float
    """The duration of the aura."""

    effects: List[Effect]
    """The effects of the aura."""

    color: Tuple[int, int, int]
    """The color of the aura."""

    period: float
    """The period of the aura."""

    owner_condition: "UnitCondition"
    """Condition that determines whether the aura is active."""

    unit_condition: "UnitCondition"
    """Condition that determines which units are affected by the aura."""

    recipient: Recipient
    """The recipient of the effect."""

    unique_key: Optional[str]
    """The key of the unique component to attach to the aura."""

    on_death: Optional[Callable[[int], None]] = None
    """The action to take when the recipient dies."""

    def apply(self, owner: Optional[int], parent: int, target: int) -> None:
        if self.recipient == Recipient.OWNER:
            recipient = owner
        elif self.recipient == Recipient.PARENT:
            recipient = parent
        elif self.recipient == Recipient.TARGET:
            recipient = target
        else:
            raise ValueError(f"Invalid recipient: {self.recipient}")
        entity = esper.create_entity()
        esper.add_component(
            entity,
            Aura(
                owner=owner,
                radius=self.radius,
                effects=self.effects,
                color=self.color,
                period=self.period,
                owner_condition=self.owner_condition,
                unit_condition=self.unit_condition
            )
        )
        esper.add_component(entity, Expiration(time_left=self.duration))
        esper.add_component(entity, Attached(entity=recipient, on_death=self.on_death))
        position = esper.component_for_entity(recipient, Position)
        esper.add_component(entity, Position(x=position.x, y=position.y))
        if self.unique_key:
            esper.add_component(entity, Unique(key=self.unique_key))


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
        elif self.recipient == Recipient.PARENT:
            recipient = parent
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

    on_death: Optional[Callable[[int], None]] = None
    """The action to take when the recipient dies."""

    unique_key: Optional[Callable[[int], str]] = None
    """The key of the unique component to attach to the effect."""

    offset: Optional[Callable[[int], Tuple[int, int]]] = None
    """The offset of the effect from the target's position."""

    random_starting_frame: bool = False
    """Whether the effect should start on a random frame."""

    layer: int = 0
    """The layer of the effect."""

    def apply(self, owner: Optional[int], parent: int, target: int) -> None:
        entity = esper.create_entity()
        position = esper.component_for_entity(target, Position)
        team = esper.component_for_entity(target, Team)
        if self.offset:
            offset = self.offset(target)
        else:
            offset = (0, 0)
        esper.add_component(entity, Position(x=position.x + offset[0], y=position.y + offset[1]))
        esper.add_component(entity, Team(type=team.type))
        esper.add_component(entity, Attached(entity=target, on_death=self.on_death, offset=offset))
        sprite_sheet = create_visual_spritesheet(
            visual=self.visual,
            scale=self.scale,
            duration=self.animation_duration,
            layer=self.layer
        )
        esper.add_component(entity, sprite_sheet)
        if self.random_starting_frame:
            time_elapsed = random.random() * self.animation_duration
        else:
            time_elapsed = 0
        esper.add_component(entity, AnimationState(type=AnimationType.IDLE, time_elapsed=time_elapsed))
        esper.add_component(entity, Expiration(time_left=self.expiration_duration))
        if self.unique_key:
            esper.add_component(entity, Unique(key=self.unique_key(target)))

@dataclass
class AttachToTarget(Effect):
    """Effect attaches the parent to the target."""

    offset: Tuple[int, int]
    """The offset of the parent from the target's position."""

    on_death: Optional[Callable[[int], None]] = None
    """The action to take when the recipient dies."""

    def apply(self, owner: Optional[int], parent: int, target: int) -> None:
        esper.add_component(parent, Attached(entity=target, on_death=self.on_death, offset=self.offset))

@dataclass
class RememberTarget(Effect):
    """Effect stores the target in the parent's entity memory."""

    def apply(self, owner: Optional[int], parent: int, target: int) -> None:
        esper.add_component(parent, EntityMemory(entity=target))

@dataclass
class Forget(Effect):
    """Effect forgets the remembered unit in the parent's entity memory."""

    def apply(self, owner: Optional[int], parent: int, target: int) -> None:
        esper.remove_component(parent, EntityMemory)

@dataclass
class SoundEffect:
    """A sound effect."""

    filename: str
    """The filename of the sound effect."""

    volume: float
    """The volume of the sound effect."""

@dataclass
class PlaySound(Effect):
    """Effect plays a sound."""

    sound_effects: Union[SoundEffect, List[Tuple[SoundEffect, float]]]
    """The sound effects to play and the weight for each sound effect to be chosen."""

    def apply(self, owner: Optional[int], parent: int, target: int) -> None:
        if isinstance(self.sound_effects, SoundEffect):
            sound_effect = self.sound_effects
        else:
            sound_effect = random.choices(
                [sound_effect for sound_effect, _ in self.sound_effects],
                weights=[weight for _, weight in self.sound_effects]
            )[0]
        emit_event(PLAY_SOUND, event=PlaySoundEvent(filename=sound_effect.filename, volume=sound_effect.volume))

@dataclass
class StanceChange(Effect):
    """Effect changes the stance of the owner."""

    stance: int
    """The stance to change to."""

    def apply(self, owner: Optional[int], parent: int, target: int) -> None:
        if owner is None:
            raise ValueError("Owner is required for StanceChange effect")
        esper.component_for_entity(owner, Stance).stance = self.stance

@dataclass
class IncreaseAmmo(Effect):
    """Effect increases the ammo of the owner."""

    amount: int
    """The amount of ammo to increase. Can be negative."""

    def apply(self, owner: Optional[int], parent: int, target: int) -> None:
        if owner is None:
            raise ValueError("Owner is required for IncreaseAmmo effect")
        ammo = esper.component_for_entity(owner, Ammo)
        ammo.current = max(min(ammo.current + self.amount, ammo.max), 0)
