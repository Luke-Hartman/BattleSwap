"""
Game constants loaded from JSON configuration.

This module loads and provides access to game constants defined in JSON configuration.
"""

import json
from pathlib import Path
from game_constants import GameConstants

# Load constants from JSON
constants_path = Path(__file__).parent / "config" / "game_constants.json"
with open(constants_path) as f:
    _constants = GameConstants.model_validate(json.load(f))

# Re-export all constants
NO_MANS_LAND_WIDTH = _constants.NO_MANS_LAND_WIDTH
BATTLEFIELD_WIDTH = _constants.BATTLEFIELD_WIDTH
BATTLEFIELD_HEIGHT = _constants.BATTLEFIELD_HEIGHT
# ... etc for all constants

# For animation durations, you may want to reconstruct the dictionaries
from components.animation import AnimationType

CORE_SWORDSMAN_ANIMATION_DURATIONS = {
    AnimationType.IDLE: _constants.CORE_SWORDSMAN_ANIMATION_IDLE_DURATION,
    AnimationType.WALKING: _constants.CORE_SWORDSMAN_ANIMATION_WALKING_DURATION,
    AnimationType.ABILITY1: _constants.CORE_SWORDSMAN_ANIMATION_ATTACK_DURATION,
    AnimationType.DYING: _constants.CORE_SWORDSMAN_ANIMATION_DYING_DURATION,
}

# ... etc for other animation duration dictionaries