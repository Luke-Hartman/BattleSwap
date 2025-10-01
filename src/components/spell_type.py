"""Spell type definitions."""

from enum import Enum


class SpellType(Enum):
    """Types of spells available in the game."""
    
    SUMMON_SKELETON_SWORDSMEN = "summon_skeleton_swordsmen"
    METEOR_SHOWER = "meteor_shower"
    INFECTING_AREA = "infecting_area"
    HEALING_AREA = "healing_area"
    SLOWING_AREA = "slowing_area"
