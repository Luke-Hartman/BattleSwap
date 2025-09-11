import warnings
from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
import math
import random
from typing import Callable, List, Optional, Tuple, Union

import esper
from pygame import Vector2
import numpy as np
from scipy.optimize import minimize

# Suppress the specific RuntimeWarning about values outside bounds during optimization
warnings.filterwarnings('ignore', message='Values in x were outside bounds during a minimize step, clipping to bounds', category=RuntimeWarning)

from components.ammo import Ammo
from components.angle import Angle
from components.angular_velocity import AngularVelocity
from components.animation import AnimationState, AnimationType
from components.aoe import CircleAoE, VisualAoE
from components.armor import Armor
from components.attached import Attached
from components.aura import Aura
from components.corruption import IncreasedDamageComponent
from components.dying import Dying
from components.entity_memory import EntityMemory
from components.expiration import Expiration
from components.forced_movement import ForcedMovement
from components.health import Health
from components.lobbed import Lobbed
from components.orientation import FacingDirection, Orientation
from components.position import Position
from components.projectile import Projectile
from components.stance import Stance
from components.status_effect import CrusaderBannerBearerEmpowered, Healing, StatusEffect, StatusEffects
from components.sprite_sheet import SpriteSheet
from components.team import Team, TeamType
from components.unit_tier import UnitTier
from components.unique import Unique
from components.unit_type import UnitType, UnitTypeComponent
from components.velocity import Velocity
from components.visual_link import VisualLink
from corruption_powers import CorruptionPower
from events import PLAY_SOUND, PlaySoundEvent, emit_event
from visuals import Visual, create_visual_spritesheet
from unit_condition import UnitCondition
from game_constants import gc
from components.airborne import Airborne
from components.status_effect import Invisible
from components.repeat import Repeat
from components.summoned import SummonedBy
from components.unit_state import State, UnitState

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
    def apply(self, owner: Optional[int], parent: Optional[int], target: Optional[int]) -> None:
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

    def apply(self, owner: Optional[int], parent: Optional[int], target: Optional[int]) -> None:
        if self.recipient == Recipient.OWNER:
            assert owner is not None
            recipient = owner
        elif self.recipient == Recipient.PARENT:
            assert parent is not None
            recipient = parent
        elif self.recipient == Recipient.TARGET:
            assert target is not None
            recipient = target
        else:
            raise ValueError(f"Invalid recipient: {self.recipient}")

        recipient_unit_state = esper.component_for_entity(recipient, UnitState)
        if recipient_unit_state.state == State.DEAD:
            return

        # Apply buffs/debuffs from the owner to the damage
        damage = self.damage
        applied_gold_knight_empowered = False
        if owner:
            status_effects = esper.component_for_entity(owner, StatusEffects)
            for status_effect in status_effects.active_effects():
                if isinstance(status_effect, CrusaderBannerBearerEmpowered) and not applied_gold_knight_empowered:
                    damage *= 1 + status_effect.damage_percentage
                    applied_gold_knight_empowered = True
            damage_component = esper.try_component(owner, IncreasedDamageComponent)
            if damage_component is not None:
                damage *= 1 + damage_component.increase_percent / 100

        # Apply armor to the damage
        recipient_health = esper.component_for_entity(recipient, Health)
        recipient_armor = esper.try_component(recipient, Armor)
        if recipient_armor:
            damage = recipient_armor.calculate_damage_after_armor(damage)
            emit_event(PLAY_SOUND, event=PlaySoundEvent(filename=f"sword_hitting_armor{random.randint(1, 4)}.wav", volume=0.50))
        else:
            # Calculate volume based on damage: 0.3 for 100 damage, 3.0 for 300+ damage
            volume = max(0.3, min(3.0, 0.3 + (damage - 100) * (3.0 - 0.3) / 200))
            emit_event(PLAY_SOUND, event=PlaySoundEvent(filename="arrow_hitting_flesh.wav", volume=volume))
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
class PlayVoice(Effect):
    """Effect plays a voice line."""
    
    voice_function: callable
    """The voice function to call."""
    
    unit_type: UnitType
    """The unit type to play the voice for."""
    
    def apply(self, owner: Optional[int], parent: Optional[int], target: Optional[int]) -> None:
        self.voice_function(self.unit_type)


@dataclass
class Heals(Effect):
    """Effect heals target."""

    amount: float
    """The amount healed."""

    recipient: Recipient
    """The recipient of the effect."""

    def apply(self, owner: Optional[int], parent: Optional[int], target: Optional[int]) -> None:
        if self.recipient == Recipient.OWNER:
            assert owner is not None
            recipient = owner
        elif self.recipient == Recipient.PARENT:
            assert parent is not None
            recipient = parent
        elif self.recipient == Recipient.TARGET:
            assert target is not None
            recipient = target
        else:
            raise ValueError(f"Invalid recipient: {self.recipient}")

        recipient_health = esper.component_for_entity(recipient, Health)
        recipient_health.current = min(recipient_health.current + self.amount, recipient_health.maximum)


@dataclass
class HealToFull(Effect):
    """Effect that creates a 1-second healing status effect equal to all missing health."""

    recipient: Recipient
    """The recipient of the effect."""

    def apply(self, owner: Optional[int], parent: Optional[int], target: Optional[int]) -> None:
        if self.recipient == Recipient.OWNER:
            assert owner is not None
            recipient = owner
        elif self.recipient == Recipient.PARENT:
            assert parent is not None
            recipient = parent
        elif self.recipient == Recipient.TARGET:
            assert target is not None
            recipient = target
        else:
            raise ValueError(f"Invalid recipient: {self.recipient}")
        
        # Calculate missing health
        health_component = esper.component_for_entity(recipient, Health)
        missing_health = health_component.maximum - health_component.current
        
        if missing_health > 0:
            # Create a healing status effect that heals all missing health over 1 second
            healing_status = Healing(time_remaining=1.0, dps=missing_health)
            status_effects = esper.component_for_entity(recipient, StatusEffects)
            status_effects.add(healing_status)


@dataclass
class HealPercentageMax(Effect):
    """Effect that creates a healing status effect equal to a percentage of maximum health over a duration."""

    recipient: Recipient
    """The recipient of the effect."""
    
    percentage: float
    """The percentage of maximum health to heal (0.0 to 1.0)."""
    
    duration: float = 1.0
    """The duration over which to heal in seconds."""

    def apply(self, owner: Optional[int], parent: Optional[int], target: Optional[int]) -> None:
        if self.recipient == Recipient.OWNER:
            assert owner is not None
            recipient = owner
        elif self.recipient == Recipient.PARENT:
            assert parent is not None
            recipient = parent
        elif self.recipient == Recipient.TARGET:
            assert target is not None
            recipient = target
        else:
            raise ValueError(f"Invalid recipient: {self.recipient}")
        
        # Calculate percentage of maximum health
        health_component = esper.component_for_entity(recipient, Health)
        heal_amount = health_component.maximum * self.percentage

        # Create a healing status effect that heals the percentage over the duration
        healing_status = Healing(time_remaining=self.duration, dps=heal_amount / self.duration)
        status_effects = esper.component_for_entity(recipient, StatusEffects)
        status_effects.add(healing_status)


@dataclass
class CreatesVisualAoE(Effect):
    """Effect creates a VisualAoE at the location of the parent."""

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

    def apply(self, owner: Optional[int], parent: Optional[int], target: Optional[int]) -> None:
        entity = esper.create_entity()
        if self.location == Recipient.OWNER:
            assert owner is not None
            recipient = owner
        elif self.location == Recipient.PARENT:
            assert parent is not None
            recipient = parent
        elif self.location == Recipient.TARGET:
            assert target is not None
            recipient = target
        else:
            raise ValueError(f"Invalid location: {self.location}")
        position = esper.component_for_entity(recipient, Position)
        team = esper.component_for_entity(recipient, Team)
        orientation = esper.try_component(recipient, Orientation)
        esper.add_component(entity, Position(x=position.x, y=position.y))
        esper.add_component(entity, Team(type=team.type))
        esper.add_component(entity, VisualAoE(
            effects=self.effects,
            owner=owner,
            unit_condition=self.unit_condition,
        ))
        esper.add_component(entity, create_visual_spritesheet(
            visual=self.visual,
            scale=self.scale,
            duration=self.duration + 1/30,
            frames=self.visual_frames,
            layer=2,
        ))
        esper.add_component(entity, AnimationState(type=AnimationType.IDLE))
        esper.add_component(entity, Expiration(time_left=self.duration))
        if orientation is not None:
            esper.add_component(entity, Orientation(facing=orientation.facing))
        if self.on_create:
            self.on_create(entity)


@dataclass
class CreatesCircleAoE(Effect):
    """Effect creates a CircleAoE at the specified location."""

    effects: List[Effect]
    """The effect of the AoE."""

    radius: float
    """The radius of the CircleAoE."""

    unit_condition: "UnitCondition"
    """Condition that determines which units are affected by the AoE."""

    location: Recipient
    """The location of the AoE."""

    def apply(self, owner: Optional[int], parent: Optional[int], target: Optional[int]) -> None:
        entity = esper.create_entity()
        if self.location == Recipient.OWNER:
            assert owner is not None
            recipient = owner
        elif self.location == Recipient.PARENT:
            assert parent is not None
            recipient = parent
        elif self.location == Recipient.TARGET:
            assert target is not None
            recipient = target
        else:
            raise ValueError(f"Invalid location: {self.location}")
        position = esper.component_for_entity(recipient, Position)
        team = esper.component_for_entity(recipient, Team)
        esper.add_component(entity, Position(x=position.x, y=position.y))
        esper.add_component(entity, Team(type=team.type))
        esper.add_component(entity, CircleAoE(
            effects=self.effects,
            owner=owner,
            unit_condition=self.unit_condition,
            radius=self.radius
        ))


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

    unit_condition: "UnitCondition"
    """Condition that determines which units can be hit by the projectile."""

    max_distance: Optional[float] = None
    """The maximum distance the projectile can travel before being automatically deleted."""

    pierce: int = 0
    """How many targets the projectile can pierce through. Decreases by 1 on each hit."""

    on_create: Optional[Callable[[int], None]] = None
    """Function to call when the projectile is created."""

    def apply(self, owner: Optional[int], parent: Optional[int], target: Optional[int]) -> None:
        assert parent is not None
        assert target is not None
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
        esper.add_component(entity, Projectile(effects=self.effects, owner=owner, unit_condition=self.unit_condition, pierce=self.pierce))
        esper.add_component(entity, create_visual_spritesheet(self.visual, layer=1))
        esper.add_component(entity, AnimationState(type=AnimationType.IDLE))
        if self.max_distance is not None:
            esper.add_component(entity, Expiration(time_left=self.max_distance / self.projectile_speed))
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

    def apply(self, owner: Optional[int], parent: Optional[int], target: Optional[int]) -> None:
        if self.recipient == Recipient.OWNER:
            assert owner is not None
            recipient = owner
        elif self.recipient == Recipient.PARENT:
            assert parent is not None
            recipient = parent
        elif self.recipient == Recipient.TARGET:
            assert target is not None
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

    def apply(self, owner: Optional[int], parent: Optional[int], target: Optional[int]) -> None:
        if self.recipient == Recipient.OWNER:
            assert owner is not None
            recipient = owner
        elif self.recipient == Recipient.PARENT:
            assert parent is not None
            recipient = parent
        elif self.recipient == Recipient.TARGET:
            assert target is not None
            recipient = target
        else:
            raise ValueError(f"Invalid recipient: {self.recipient}")
        recipient_status_effects = esper.component_for_entity(recipient, StatusEffects)
        recipient_status_effects.add(self.status_effect)
    
@dataclass
class RemoveInvisible(Effect):
    """Effect that removes the invisible status effect from the target."""

    recipient: Recipient
    """The recipient of the effect."""

    def apply(self, owner: Optional[int], parent: Optional[int], target: Optional[int]) -> None:
        if self.recipient == Recipient.OWNER:
            assert owner is not None
            recipient = owner
        elif self.recipient == Recipient.PARENT:
            assert parent is not None
            recipient = parent
        elif self.recipient == Recipient.TARGET:
            assert target is not None
            recipient = target
        else:
            raise ValueError(f"Invalid recipient: {self.recipient}")
        
        recipient_status_effects = esper.component_for_entity(recipient, StatusEffects)
        # Remove all invisible effects
        recipient_status_effects._status_by_type[Invisible].clear()
    
@dataclass
class IncreasesMaxHealthFromTarget(Effect):
    """Effect that permanently increases the maximum health of the owner by the target's maximum health."""

    recipient: Recipient
    """The recipient of the effect (should be OWNER)."""

    def apply(self, owner: Optional[int], parent: Optional[int], target: Optional[int]) -> None:
        if self.recipient == Recipient.OWNER:
            assert owner is not None
            recipient = owner
        elif self.recipient == Recipient.PARENT:
            assert parent is not None
            recipient = parent
        elif self.recipient == Recipient.TARGET:
            assert target is not None
            recipient = target
        else:
            raise ValueError(f"Invalid recipient: {self.recipient}")
        
        # Get the target's maximum health before they die
        if target is not None and esper.has_component(target, Health):
            target_health = esper.component_for_entity(target, Health)
            health_increase = target_health.maximum
            
            # Apply the health increase to the owner
            owner_health = esper.component_for_entity(recipient, Health)
            owner_health.maximum += health_increase

@dataclass
class CreatesAttachedVisual(Effect):
    """Effect creates a visual effect that is attached to the target."""

    recipient: Recipient
    """The recipient of the effect."""

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

    def apply(self, owner: Optional[int], parent: Optional[int], target: Optional[int]) -> None:
        if self.recipient == Recipient.OWNER:
            assert owner is not None
            recipient = owner
        elif self.recipient == Recipient.PARENT:
            assert parent is not None
            recipient = parent
        elif self.recipient == Recipient.TARGET:
            assert target is not None
            recipient = target
        else:
            raise ValueError(f"Invalid recipient: {self.recipient}")
        entity = esper.create_entity()
        position = esper.component_for_entity(recipient, Position)
        team = esper.component_for_entity(recipient, Team)
        if self.offset:
            offset = self.offset(recipient)
        else:
            offset = (0, 0)
        esper.add_component(entity, Position(x=position.x + offset[0], y=position.y + offset[1]))
        esper.add_component(entity, Team(type=team.type))
        esper.add_component(entity, Attached(entity=recipient, on_death=self.on_death, offset=offset))
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
            esper.add_component(entity, Unique(key=self.unique_key(recipient)))


@dataclass
class CreatesVisual(Effect):
    """Effect creates a visual effect at the location of the recipient with an optional duration."""

    recipient: Recipient
    """The recipient of the effect."""

    visual: Visual
    """The visual of the effect."""

    animation_duration: float
    """The duration of the animation loop."""

    scale: float
    """The scale of the effect."""

    duration: Optional[float] = None
    """The duration of the effect. If None, the effect is permanent."""

    offset: Optional[Callable[[int], Tuple[int, int]]] = None
    """The offset of the effect from the target's position."""

    random_starting_frame: bool = False
    """Whether the effect should start on a random frame."""

    layer: int = 0
    """The layer of the effect."""

    def apply(self, owner: Optional[int], parent: Optional[int], target: Optional[int]) -> None:
        if self.recipient == Recipient.OWNER:
            assert owner is not None
            recipient = owner
        elif self.recipient == Recipient.PARENT:
            assert parent is not None
            recipient = parent
        elif self.recipient == Recipient.TARGET:
            assert target is not None
            recipient = target
        else:
            raise ValueError(f"Invalid recipient: {self.recipient}")
            
        recipient_position = esper.component_for_entity(recipient, Position)
        team = esper.component_for_entity(recipient, Team)
        entity = esper.create_entity()
        
        esper.add_component(entity, Position(x=recipient_position.x, y=recipient_position.y))
        esper.add_component(entity, Team(type=team.type))
        esper.add_component(entity, create_visual_spritesheet(
            visual=self.visual,
            duration=self.duration,
            scale=self.scale,
            layer=self.layer
        ))
        
        if self.random_starting_frame:
            time_elapsed = random.random() * self.animation_duration
        else:
            time_elapsed = 0
        
        esper.add_component(entity, AnimationState(type=AnimationType.IDLE, time_elapsed=time_elapsed))
        if self.duration is not None:
            esper.add_component(entity, Expiration(time_left=self.duration))



@dataclass
class AttachToTarget(Effect):
    """Effect attaches the parent to the target."""

    offset: Tuple[int, int]
    """The offset of the parent from the target's position."""

    on_death: Optional[Callable[[int], None]] = None
    """The action to take when the recipient dies."""

    def apply(self, owner: Optional[int], parent: Optional[int], target: Optional[int]) -> None:
        assert parent is not None
        assert target is not None
        esper.add_component(parent, Attached(entity=target, on_death=self.on_death, offset=self.offset))


@dataclass
class RememberTarget(Effect):
    """Effect stores the target in the recipient's entity memory."""

    recipient: Recipient
    """The recipient of the effect."""

    def apply(self, owner: Optional[int], parent: Optional[int], target: Optional[int]) -> None:
        if self.recipient == Recipient.OWNER:
            assert owner is not None
            recipient = owner
        elif self.recipient == Recipient.PARENT:
            assert parent is not None
            recipient = parent
        elif self.recipient == Recipient.TARGET:
            assert target is not None
            recipient = target
        else:
            raise ValueError(f"Invalid recipient: {self.recipient}")
        esper.add_component(recipient, EntityMemory(entity=target))


@dataclass
class Forget(Effect):
    """Effect forgets the remembered unit in the recipient's entity memory."""

    recipient: Recipient
    """The recipient of the effect."""

    def apply(self, owner: Optional[int], parent: Optional[int], target: Optional[int]) -> None:
        if self.recipient == Recipient.OWNER:
            assert owner is not None
            recipient = owner
        elif self.recipient == Recipient.PARENT:
            assert parent is not None
            recipient = parent
        elif self.recipient == Recipient.TARGET:
            assert target is not None
            recipient = target
        else:
            raise ValueError(f"Invalid recipient: {self.recipient}")
        esper.remove_component(recipient, EntityMemory)

@dataclass
class SoundEffect:
    """A sound effect."""

    filename: str
    """The filename of the sound effect."""

    volume: float
    """The volume of the sound effect."""
    
    channel: Optional[str] = None
    """The channel to play the sound on. If None, uses a standard channel."""


@dataclass
class PlaySound(Effect):
    """Effect plays a sound."""

    sound_effects: Union[SoundEffect, List[Tuple[SoundEffect, float]]]
    """The sound effects to play and the weight for each sound effect to be chosen."""

    def apply(self, owner: Optional[int], parent: Optional[int], target: Optional[int]) -> None:
        if isinstance(self.sound_effects, SoundEffect):
            sound_effect = self.sound_effects
        else:
            sound_effect = random.choices(
                [sound_effect for sound_effect, _ in self.sound_effects],
                weights=[weight for _, weight in self.sound_effects]
            )[0]
        emit_event(PLAY_SOUND, event=PlaySoundEvent(
            filename=sound_effect.filename,
            volume=sound_effect.volume,
            channel=sound_effect.channel
        ))


@dataclass
class StanceChange(Effect):
    """Effect changes the stance of the owner."""

    stance: int
    """The stance to change to."""

    def apply(self, owner: Optional[int], parent: Optional[int], target: Optional[int]) -> None:    
        assert owner is not None
        esper.component_for_entity(owner, Stance).stance = self.stance


@dataclass
class IncreaseAmmo(Effect):
    """Effect increases the ammo of the owner."""

    amount: int
    """The amount of ammo to increase. Can be negative."""

    def apply(self, owner: Optional[int], parent: Optional[int], target: Optional[int]) -> None:
        assert owner is not None
        ammo = esper.component_for_entity(owner, Ammo)
        ammo.current = max(min(ammo.current + self.amount, ammo.max), 0)


def _calculate_minimum_angle(min_range: float, max_range: float, initial_velocity: float) -> float:
    """Calculate the minimum launch angle needed to reach the minimum range.
    
    For a given range R and initial velocity v, the angle θ is given by:
    R = (v^2/g) * sin(2θ)
    
    Solving for θ:
    θ = (1/2) * arcsin(R*g/v^2)
    
    Args:
        min_range: Minimum range to reach
        max_range: Maximum range to reach (used for initial velocity calculation)
        initial_velocity: Initial velocity magnitude
        
    Returns:
        Minimum launch angle in radians
    """
    if min_range <= 0:
        return 0.0
        
    sin_arg = (gc.GRAVITY * min_range) / (initial_velocity * initial_velocity)
    if sin_arg >= 1.0:
        # Minimum range is unreachable - use 45 degrees as fallback
        return math.pi/4
        
    return 0.5 * math.asin(sin_arg)

def _calculate_projectile_position(
    start: Vector2,
    launch_angle: float,  # vertical angle (theta)
    direction_angle: float,  # horizontal angle (phi)
    initial_velocity: float,
) -> Tuple[Vector2, float]:
    """Calculate where a projectile will land and how long it takes.
    
    Args:
        start: Starting position
        launch_angle: Angle of launch into the z dimension (radians)
        direction_angle: Angle of launch in x-y plane (radians)
        initial_velocity: Initial velocity magnitude
        
    Returns:
        Tuple of (landing position as Vector2, time to land)
    """
    # Initial velocity components
    vx = initial_velocity * math.cos(launch_angle) * math.cos(direction_angle)
    vy = initial_velocity * math.cos(launch_angle) * math.sin(direction_angle)
    vz = initial_velocity * math.sin(launch_angle)
    
    # Time to hit ground: 0 = vz*t - 0.5*g*t^2
    # Using quadratic formula, we want the positive root
    # t = (vz + sqrt(vz^2)) / g
    time_to_land = (vz + math.sqrt(vz * vz)) / gc.GRAVITY
    
    # Calculate landing position
    x = start.x + vx * time_to_land
    y = start.y + vy * time_to_land
    
    return Vector2(x, y), time_to_land

def calculate_target_position(
    start: Vector2,
    target_pos: Vector2,
    max_range: float,
    min_range: float,
    max_angle: float,
    target_velocity: Optional[Velocity] = None,
    smart: bool = False,
) -> Vector2:
    """Calculate the optimal target position for a trajectory.
    
    Args:
        start: Starting position
        target_pos: Initial target position
        max_range: Maximum range of the trajectory
        min_range: Minimum range of the trajectory
        max_angle: Maximum angle of the trajectory
        target_velocity: Optional velocity of the target
        smart: Whether the target position should be smart

    Returns:
        The calculated target position
    """
    if target_velocity is None:
        return target_pos

    if not smart:
        return target_pos

    assert 0 < max_angle <= math.pi/4

    # Calculate initial velocity needed to reach max_range
    # Using v = sqrt(g * R / sin(2θ)) where θ is max_angle
    initial_velocity = math.sqrt(gc.GRAVITY * max_range / math.sin(2 * max_angle))
    # Calculate minimum launch angle based on minimum range
    min_launch_angle = _calculate_minimum_angle(min_range, max_range, initial_velocity)
    
    # Initial direction towards current target position
    dx = target_pos.x - start.x
    dy = target_pos.y - start.y
    initial_direction = math.atan2(dy, dx)
    initial_launch = max_angle
    
    def objective(x: np.ndarray) -> float:
        """Calculate miss distance for given launch parameters."""
        launch_angle, direction_angle = x
        
        # Calculate where projectile will land and when
        projectile_pos, time_to_land = _calculate_projectile_position(
            start, launch_angle, direction_angle, initial_velocity
        )
        
        # Calculate where target will be when projectile lands
        target_future = Vector2(
            target_pos.x + target_velocity.x * time_to_land,
            target_pos.y + target_velocity.y * time_to_land
        )
        
        return (projectile_pos - target_future).length()
    
    # Try to find the optimal launch parameters
    result = minimize(
        objective,
        x0=[initial_launch, initial_direction],  # Initial guess
        method='SLSQP',
        bounds=[
            (min_launch_angle, max_angle),  # Launch angle between min and max
            (-math.pi, math.pi),  # Direction angle between -180 and 180 degrees
        ],
        options={'ftol': 1e-3}  # Looser tolerance for game purposes
    )
    
    if result.success:
        # Use the optimal parameters to set the target position
        launch_angle, direction_angle = result.x
        target_pos, _ = _calculate_projectile_position(
            start, launch_angle, direction_angle, initial_velocity
        )
        
    return target_pos


@dataclass
class CreatesLobbed(Effect):
    """Effect creates a lobbed entity towards the target."""

    effects: List[Effect]
    """The effects of the lobbed entity."""

    max_range: float
    """The maximum range of the lobbed entity."""

    visual: Visual
    """The visual of the lobbed entity."""

    offset: Tuple[float, float]
    """The offset of the lobbed entity from the parent's position."""

    min_range: float = 0.0
    """The minimum range of the lobbed entity."""

    max_angle: float = math.pi/4
    """The maximum angle of the lobbed entity."""

    smart: bool = False
    """Whether the lobbed entity should use smart targeting."""

    angular_velocity: float = 0.0
    """The rotation of the lobbed entity."""

    def apply(self, owner: Optional[int], parent: Optional[int], target: Optional[int]) -> None:
        assert parent is not None
        assert target is not None

        parent_position = esper.component_for_entity(parent, Position)
        target_position = esper.component_for_entity(target, Position)
        entity = esper.create_entity()
        parent_orientation = esper.try_component(parent, Orientation)
        parent_team = esper.component_for_entity(parent, Team)
        offset = Vector2(self.offset[0], self.offset[1])
        if parent_orientation is not None:
            offset.x *= parent_orientation.facing.value
            
        # Calculate start position
        start = Vector2(parent_position.x + offset.x, parent_position.y + offset.y)
        target_pos = Vector2(target_position.x, target_position.y)
        
        # Calculate trajectory
        target_pos = calculate_target_position(
            start=start,
            target_pos=target_pos,
            max_range=self.max_range,
            min_range=self.min_range,
            max_angle=self.max_angle,
            target_velocity=esper.try_component(target, Velocity),
            smart=self.smart,
        )
            
        esper.add_component(
            entity,
            Lobbed(
                start=start,
                target=target_pos,
                max_range=self.max_range,
                max_angle=self.max_angle,
                effects=self.effects + [Land()],
                owner=owner,
                destroy_on_arrival=True,
            )
        )
        esper.add_component(entity, Position(x=start.x, y=start.y))
        esper.add_component(entity, create_visual_spritesheet(self.visual, layer=1))
        esper.add_component(entity, AnimationState(type=AnimationType.IDLE))
        esper.add_component(entity, Team(type=parent_team.type))
        esper.add_component(entity, Orientation(facing=parent_orientation.facing))
        if self.angular_velocity != 0:
            esper.add_component(entity, AngularVelocity(self.angular_velocity * parent_orientation.facing.value))
        esper.add_component(entity, Angle(angle=0))


@dataclass
class Jump(Effect):
    """Effect makes the parent jump towards the target."""

    effects: List[Effect]
    """Effects to apply when landing."""

    max_range: float
    """The maximum range of the jump."""

    min_range: float = 0.0
    """The minimum range of the jump."""

    max_angle: float = math.pi/4
    """The maximum angle of the jump."""

    def apply(self, owner: Optional[int], parent: Optional[int], target: Optional[int]) -> None:
        assert parent is not None
        assert target is not None

        parent_position = esper.component_for_entity(parent, Position)
        target_position = esper.component_for_entity(target, Position)
        
        start = Vector2(parent_position.x, parent_position.y)
        target_pos = Vector2(target_position.x, target_position.y)
        
        target_pos = calculate_target_position(
            start=start,
            target_pos=target_pos,
            max_range=self.max_range,
            min_range=self.min_range,
            max_angle=self.max_angle,
            target_velocity=esper.try_component(target, Velocity),
            smart=True,
        )
        esper.add_component(
            parent,
            Lobbed(
                start=start,
                target=target_pos,
                max_range=self.max_range,
                max_angle=self.max_angle,
                effects=self.effects + [Land()],
                owner=owner,
                destroy_on_arrival=False,
            )
        )
        esper.add_component(parent, Airborne())
        if esper.has_component(parent, Orientation):
            orientation = esper.component_for_entity(parent, Orientation)
            orientation.facing = FacingDirection.RIGHT if target_pos.x > parent_position.x else FacingDirection.LEFT

class Land(Effect):
    """Effect lands the parent."""

    def apply(self, owner: Optional[int], parent: Optional[int], target: Optional[int]) -> None:
        assert parent is not None
        if esper.has_component(parent, Airborne):
            esper.remove_component(parent, Airborne)

@dataclass
class CreatesUnit(Effect):
    """Effect creates a unit by the location of the recipient."""

    recipient: Recipient
    """The recipient of the effect."""
    
    unit_type: UnitType
    """The unit type to create."""

    team: TeamType
    """The team of the unit."""

    offset: Tuple[int, int]
    """The offset of the unit from the recipient's position."""

    corruption_powers: Optional[List[CorruptionPower]]
    """The corruption powers to apply to the created unit."""
    
    batch_size: int = 1
    """The number of units to create in a batch. Defaults to 1 for single unit creation."""
    
    batch_spacing: int = 10
    """The spacing between units in a batch. Defaults to 10 units."""
    
    def apply(self, owner: Optional[int], parent: Optional[int], target: Optional[int]) -> None:
        if self.recipient == Recipient.OWNER:
            assert owner is not None
            recipient = owner
        elif self.recipient == Recipient.PARENT:
            assert parent is not None
            recipient = parent
        elif self.recipient == Recipient.TARGET:
            assert target is not None
            recipient = target
        else:
            raise ValueError(f"Invalid recipient: {self.recipient}")
        
        from entities.units import create_unit
        from progress_manager import progress_manager
        from components.unit_tier import UnitTier

        position = esper.component_for_entity(recipient, Position)
        
        # Determine the appropriate tier for the unit
        if self.team == TeamType.TEAM1 and progress_manager:
            # Player units should use their upgraded tier
            tier = progress_manager.get_unit_tier(self.unit_type)
        else:
            if self.corruption_powers is not None:
                tier = UnitTier.ELITE
            else:
                tier = UnitTier.BASIC
        
        # Calculate positions for batch creation
        if self.batch_size == 1:
            # Single unit creation (original behavior)
            positions = [(self.offset[0], self.offset[1])]
        else:
            # Batch creation - center the units vertically with spacing
            total_height = (self.batch_size - 1) * self.batch_spacing
            start_y = -total_height // 2
            positions = [(self.offset[0], start_y + i * self.batch_spacing) for i in range(self.batch_size)]
        
        # Create all units in the batch
        for offset_x, offset_y in positions:
            entity = create_unit(
                x=position.x + offset_x,
                y=position.y + offset_y,
                unit_type=self.unit_type,
                team=self.team,
                corruption_powers=self.corruption_powers,
                tier=tier
            )
            esper.add_component(entity, Team(type=self.team))
            # Tag the created unit with its summoner, if applicable
            if owner is not None:
                esper.add_component(entity, SummonedBy(summoner=owner))

@dataclass
class AddsForcedMovement(Effect):
    """Effect adds forced movement to the recipient."""

    recipient: Recipient
    """The recipient of the effect."""

    destination: Recipient
    """The destination of the forced movement."""

    speed: float
    """The speed of the forced movement."""

    offset_x: float
    """The x offset of the forced movement from the destination.
    
    Is relative to the destination's orientation.
    """

    offset_y: float
    """The y offset of the forced movement from the destination."""
    
    def apply(self, owner: Optional[int], parent: Optional[int], target: Optional[int]) -> None:
        if self.recipient == Recipient.OWNER:
            recipient = owner
        elif self.recipient == Recipient.PARENT:
            recipient = parent
        elif self.recipient == Recipient.TARGET:
            recipient = target
        else:
            raise ValueError(f"Invalid recipient: {self.recipient}")
        if self.destination == Recipient.OWNER:
            assert owner is not None
            destination = owner
        elif self.destination == Recipient.PARENT:
            assert parent is not None
            destination = parent
        elif self.destination == Recipient.TARGET:
            assert target is not None
            destination = target
        else:
            raise ValueError(f"Invalid destination: {self.destination}")
        destination_pos = esper.component_for_entity(destination, Position)
        destination_orientation = esper.component_for_entity(destination, Orientation)
        esper.add_component(recipient, ForcedMovement(
            destination_x=destination_pos.x + self.offset_x * destination_orientation.facing.value,
            destination_y=destination_pos.y + self.offset_y,
            speed=self.speed,
        ))

@dataclass
class CreatesVisualLink(Effect):
    """Effect creates a visual link between the start and other entities."""

    start_entity: Recipient
    """The start entity of the visual link."""

    other_entity: Recipient
    """The other entity of the visual link."""

    visual: Visual
    """The visual of the visual link."""

    tile_size: int
    """The tile size of the visual link."""

    entity_delete_condition: Optional[UnitCondition] = None
    """The condition that, if met, will remove the visual link."""

    other_entity_delete_condition: Optional[UnitCondition] = None
    """The condition that, if met, will remove the visual link."""

    def apply(self, owner: Optional[int], parent: Optional[int], target: Optional[int]) -> None:
        if self.start_entity == Recipient.OWNER:
            start_entity = owner
        elif self.start_entity == Recipient.PARENT:
            start_entity = parent
        elif self.start_entity == Recipient.TARGET:
            start_entity = target
        else:
            raise ValueError(f"Invalid start entity: {self.start_entity}")
        if self.other_entity == Recipient.OWNER:
            other_entity = owner
        elif self.other_entity == Recipient.PARENT:
            other_entity = parent
        elif self.other_entity == Recipient.TARGET:
            other_entity = target
        else:
            raise ValueError(f"Invalid other entity: {self.other_entity}")
        esper.add_component(start_entity, VisualLink(
            other_entity=other_entity,
            visual=self.visual,
            tile_size=self.tile_size,
            entity_delete_condition=self.entity_delete_condition,
            other_entity_delete_condition=self.other_entity_delete_condition,
        ))

@dataclass
class CreatesRepeat(Effect):
    """Effect creates a repeat component that continually applies effects at intervals."""

    recipient: Recipient
    """The recipient that gets the repeat component."""

    effects: List[Effect]
    """The effects to repeat."""

    interval: float
    """The interval between effect applications in seconds."""

    stop_condition: UnitCondition
    """The condition that, when met, stops the repeating effects."""

    def apply(self, owner: Optional[int], parent: Optional[int], target: Optional[int]) -> None:
        if self.recipient == Recipient.OWNER:
            recipient = owner
        elif self.recipient == Recipient.PARENT:
            recipient = parent
        elif self.recipient == Recipient.TARGET:
            recipient = target
        else:
            raise ValueError(f"Invalid recipient: {self.recipient}")
        
        esper.add_component(recipient, Repeat(
            effects=self.effects,
            interval=self.interval,
            stop_condition=self.stop_condition,
            owner=owner,
            parent=parent,
            target=target,
        ))


@dataclass
class Revive(Effect):
    """Effect that revives a dead unit."""
    
    team: TeamType
    """The team to revive the unit on."""
    
    corruption_powers: Optional[List[CorruptionPower]]
    """The corruption powers to apply to the revived unit."""
    
    tier: UnitTier
    """The tier to revive the unit at."""
    
    def apply(self, owner: Optional[int], parent: Optional[int], target: Optional[int]) -> None:
        if target is None:
            return
            
        # Get the dead unit's components
        unit_type = esper.component_for_entity(target, UnitTypeComponent).type
        position = esper.component_for_entity(target, Position)
        orientation = esper.component_for_entity(target, Orientation)
        
        # Hide the corpse (similar to zombie infection)
        if esper.has_component(target, SpriteSheet):
            esper.remove_component(target, SpriteSheet)
        
        # Create the revived unit
        from entities.units import create_unit
        
        # Create the unit with the same position and orientation
        revived_unit = create_unit(
            x=position.x,
            y=position.y,
            unit_type=unit_type,
            team=self.team,
            corruption_powers=self.corruption_powers,
            tier=self.tier,
            play_spawning=True,
            orientation=orientation.facing
        )
