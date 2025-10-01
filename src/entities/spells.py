"""Module for handling spells in the game."""

from enum import Enum
from typing import Dict, List, Tuple
import esper
import math
import pygame
import os
from components.position import Position
from components.team import Team, TeamType
from components.unit_type import UnitType
from components.unit_tier import UnitTier
from components.orientation import FacingDirection
from components.spell import SpellComponent
from components.spell_type import SpellType
from components.placing import Placing
from effects import Effect, CreatesUnit, Recipient
from game_constants import gc
from unit_condition import Always

spell_theme_ids: Dict[SpellType, str] = {
    SpellType.SUMMON_SKELETON_SWORDSMEN: "#summon_skeleton_swordsmen_icon",
    SpellType.METEOR_SHOWER: "#meteor_shower_icon",
    SpellType.INFECT_AREA: "#infect_area_icon"
}

spell_icon_surfaces: Dict[SpellType, pygame.Surface] = {}


def load_spell_icons() -> None:
    """Load all spell icons."""
    spell_icon_paths: Dict[SpellType, str] = {
        SpellType.SUMMON_SKELETON_SWORDSMEN: "SummonSkeletonSwordsmenIcon.png",
        SpellType.METEOR_SHOWER: "MeteorShowerIcon.png",
        SpellType.INFECT_AREA: "InfectAreaIcon.png",
    }
    
    for spell_type, filename in spell_icon_paths.items():
        if spell_type in spell_icon_surfaces:
            continue
        path = os.path.join("assets", "icons", filename)
        spell_icon_surfaces[spell_type] = pygame.image.load(path).convert_alpha()


def create_spell(
    x: float,
    y: float,
    spell_type: SpellType,
    team: TeamType,
    corruption_powers: List = None,
) -> int:
    """Create a spell entity with all necessary components.
    
    Args:
        x: X coordinate to place the spell at
        y: Y coordinate to place the spell at
        spell_type: Type of spell to create
        team: Team that is casting the spell
        corruption_powers: Optional corruption powers to apply
        
    Returns:
        Entity ID of the created spell
    """
    spell_creators = {
        SpellType.SUMMON_SKELETON_SWORDSMEN: create_summon_skeleton_swordsmen_spell,
        SpellType.METEOR_SHOWER: create_meteor_shower_spell,
        SpellType.INFECT_AREA: create_infect_area_spell,
    }
    
    if spell_type not in spell_creators:
        raise ValueError(f"Unknown spell type: {spell_type}")
    
    return spell_creators[spell_type](x, y, team, corruption_powers)


def create_base_spell(
    x: float,
    y: float,
    team: TeamType,
    corruption_powers: List = None,
) -> int:
    """Create a base spell entity with all necessary components."""
    entity = esper.create_entity()
    esper.add_component(entity, Position(x=x, y=y))
    esper.add_component(entity, Team(type=team))
    return entity

def create_summon_skeleton_swordsmen_spell(
    x: float,
    y: float,
    team: TeamType,
    corruption_powers: List = None,
) -> int:
    """Create a Summon Skeleton Swordsmen spell entity.
    
    This spell summons skeleton swordsmen in a circle when cast.
    The number of skeletons and radius are defined by constants.
    
    Args:
        x: X coordinate to place the spell at
        y: Y coordinate to place the spell at
        team: Team that is casting the spell
        corruption_powers: Optional corruption powers to apply
        
    Returns:
        Entity ID of the created spell
    """
    entity = create_base_spell(x, y, team, corruption_powers)
    
    # Create effects for summoning skeleton swordsmen in a circle
    effects = []
    radius = gc.SPELL_SUMMON_SKELETON_SWORDSMEN_RADIUS
    count = gc.SPELL_SUMMON_SKELETON_SWORDSMEN_COUNT
    
    for i in range(count):
        angle = (2 * math.pi * i) / count
        offset_x = radius * math.cos(angle)
        offset_y = radius * math.sin(angle)
        
        # Create a CreatesUnit effect for each skeleton swordsman
        effect = CreatesUnit(
            recipient=Recipient.PARENT,  # Create at the spell's position
            unit_type=UnitType.SKELETON_SWORDSMAN,
            team=team,
            offset=(int(offset_x), int(offset_y)),
            corruption_powers=corruption_powers,
            play_spawning=True,
        )
        effects.append(effect)

    esper.add_component(entity, SpellComponent(
        spell_type=SpellType.SUMMON_SKELETON_SWORDSMEN,
        team=team.value,
        effects=effects,
        radius=radius
    ))
    return entity


def create_meteor_shower_spell(
    x: float,
    y: float,
    team: TeamType,
    corruption_powers: List = None,
) -> int:
    """Create a Meteor Shower spell entity.
    
    This spell creates a volley of meteors that fly in from a fixed angle
    and explode on impact, dealing AoE damage.
    
    Args:
        x: X coordinate to place the spell at
        y: Y coordinate to place the spell at
        team: Team that is casting the spell
        corruption_powers: Optional corruption powers to apply
        
    Returns:
        Entity ID of the created spell
    """
    entity = create_base_spell(x, y, team, corruption_powers)
    
    # Import the effects we need
    from effects import CreatesVolley, CreatesCircleAoE, Damages, CreatesVisual, PlaySound, Recipient, SoundEffect
    from unit_condition import All, Alive, Grounded
    from visuals import Visual
    
    # Create the meteor shower effect
    meteor_effects = [
        CreatesCircleAoE(
            effects=[
                Damages(damage=gc.SPELL_METEOR_SHOWER_DAMAGE, recipient=Recipient.TARGET),
            ],
            radius=gc.SPELL_METEOR_SHOWER_AOE_RADIUS,
            unit_condition=All([Alive(), Grounded()]),
            location=Recipient.PARENT,
        ),
        CreatesVisual(
            recipient=Recipient.PARENT,
            visual=Visual.Explosion,
            animation_duration=gc.SPELL_METEOR_SHOWER_AOE_DURATION,
            scale=gc.SPELL_METEOR_SHOWER_AOE_RADIUS * gc.EXPLOSION_VISUAL_SCALE_RATIO,
            duration=gc.SPELL_METEOR_SHOWER_AOE_DURATION,
            layer=2,
        ),
        PlaySound(SoundEffect(filename="fireball_impact.wav", volume=0.5)),
    ]
    
    meteor_shower_effect = CreatesVolley(
        recipient=Recipient.PARENT,
        random_seed=43,  # Fixed seed for deterministic behavior
        radius=gc.SPELL_METEOR_SHOWER_RADIUS,
        duration=gc.SPELL_METEOR_SHOWER_DURATION,
        num_projectiles=gc.SPELL_METEOR_SHOWER_METEOR_COUNT,
        projectile_visual=Visual.Fireball,  # Using fireball visual for now
        projectile_effects=meteor_effects,
        projectile_speed=gc.SPELL_METEOR_SHOWER_PROJECTILE_SPEED,
        projectile_distance=gc.SPELL_METEOR_SHOWER_PROJECTILE_DISTANCE,
        projectile_angle=gc.SPELL_METEOR_SHOWER_PROJECTILE_ANGLE,
        on_create=lambda _: PlaySound(SoundEffect(filename="meteor_falling.wav", volume=0.5)).apply(None, None, None),
    )
    
    esper.add_component(entity, SpellComponent(
        spell_type=SpellType.METEOR_SHOWER,
        team=team.value,
        effects=[meteor_shower_effect],
        radius=gc.SPELL_METEOR_SHOWER_RADIUS
    ))
    
    return entity


def create_infect_area_spell(
    x: float,
    y: float,
    team: TeamType,
    corruption_powers: List = None,
) -> int:
    """Create an Infect Area spell entity.
    
    This spell creates a temporary aura on the ground that infects all units
    in the area with zombie infection when they die.
    
    Args:
        x: X coordinate to place the spell at
        y: Y coordinate to place the spell at
        team: Team that is casting the spell
        corruption_powers: Optional corruption powers to apply
        
    Returns:
        Entity ID of the created spell
    """
    entity = create_base_spell(x, y, team, corruption_powers)
    
    # Import the effects we need
    from effects import CreatesTemporaryAura, AppliesStatusEffect, Recipient
    from unit_condition import All, Alive, Infected, Not
    from components.status_effect import ZombieInfection
    
    # Create the infect area effect
    infect_area_effect = CreatesTemporaryAura(
        radius=gc.SPELL_INFECT_AREA_RADIUS,
        duration=gc.SPELL_INFECT_AREA_DURATION,
        effects=[
            AppliesStatusEffect(
                status_effect=ZombieInfection(
                    time_remaining=gc.ZOMBIE_INFECTION_DURATION,
                    team=team,
                    corruption_powers=corruption_powers,
                    owner=None  # The aura itself is the source
                ),
                recipient=Recipient.TARGET
            )
        ],
        color=(100, 50, 100),  # Purple color for infection aura
        period=gc.DEFAULT_AURA_PERIOD,
        owner_condition=Always(),  # Always active (no owner condition needed)
        unit_condition=Alive(),  # Only affect living, non-infected units
        recipient=Recipient.PARENT,  # Create aura at the spell's position
    )
    
    esper.add_component(entity, SpellComponent(
        spell_type=SpellType.INFECT_AREA,
        team=team.value,
        effects=[infect_area_effect],
        radius=gc.SPELL_INFECT_AREA_RADIUS
    ))
    
    return entity
