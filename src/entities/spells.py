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

spell_theme_ids: Dict[SpellType, str] = {
    SpellType.SUMMON_SKELETON_SWORDSMEN: "#summon_skeleton_swordsmen_icon"
}

spell_icon_surfaces: Dict[SpellType, pygame.Surface] = {}


def load_spell_icons() -> None:
    """Load all spell icons."""
    spell_icon_paths: Dict[SpellType, str] = {
        SpellType.SUMMON_SKELETON_SWORDSMEN: "SummonSkeletonSwordsmenIcon.png",
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
