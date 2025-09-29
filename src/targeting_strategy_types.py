"""Enum for different types of targeting strategies."""

from enum import Enum


class TargetingStrategyType(Enum):
    """Types of targeting strategies available in the game."""
    FOLLOWER = "follower"
    DEFAULT = "default"  # nearest enemy
    HUNTER = "hunter"    # prioritizes low health enemies
    CORPSES = "corpses"  # targets corpses
