"""Enums for specifying different kinds of simple visuals.

For example, any visual which is simply a looping animation should be defined here.
"""

import os
from typing import Optional, Tuple
import pygame
from enum import Enum, auto

from components.animation import AnimationType
from components.sprite_sheet import SpriteSheet
from game_constants import gc
class Visual(Enum):
    Arrow = auto()
    CoreBarbarianAttack = auto()
    CrusaderBlackKnightFear = auto()
    CrusaderCatapultBall = auto()
    CrusaderCatapultBallExplosion = auto()
    CrusaderCatapultBallRemains = auto()
    CrusaderGoldKnightAttack = auto()
    CrusaderRedKnightFireSlash = auto()
    Explosion = auto()
    Fear = auto()
    Fireball = auto()
    Healing = auto()
    Ignited = auto()
    Tongue = auto()
    TongueTip = auto()

visual_sheets: dict[Visual, pygame.Surface] = {}

def load_visual_sheets():
    """Load all visual sprite sheets."""
    visual_paths = {
        Visual.Arrow: os.path.join("assets", "effects", "HumansProjectiles.png"),
        Visual.CoreBarbarianAttack: os.path.join("assets", "units", "CoreBarbarian.png"),
        Visual.CrusaderBlackKnightFear: os.path.join("assets", "effects", "Black_Knight_Fear.png"),
        Visual.CrusaderCatapultBall: os.path.join("assets", "effects", "CrusaderCatapultBall.png"),
        Visual.CrusaderCatapultBallExplosion: os.path.join("assets", "effects", "CrusaderCatapultBall.png"),
        Visual.CrusaderCatapultBallRemains: os.path.join("assets", "effects", "CrusaderCatapultBall.png"),
        Visual.CrusaderGoldKnightAttack: os.path.join("assets", "effects", "CrusaderGoldKnightAttackEffect.png"),
        Visual.CrusaderRedKnightFireSlash: os.path.join("assets", "effects", "Knight-Attack03_Effect.png"),
        Visual.Explosion: os.path.join("assets", "effects", "explosiontip1_32x32.png"),
        Visual.Fear: os.path.join("assets", "effects", "Fear.png"),
        Visual.Fireball: os.path.join("assets", "effects", "Wizard.png"),
        Visual.Healing: os.path.join("assets", "units", "CrusaderCleric.png"),
        Visual.Ignited: os.path.join("assets", "effects", "Ignited.png"),
        Visual.Tongue: os.path.join("assets", "effects", "Tongue.png"),
        Visual.TongueTip: os.path.join("assets", "effects", "TongueTip.png"),
    }
    for visual, path in visual_paths.items():
        if visual in visual_sheets:
            continue
        visual_sheets[visual] = pygame.image.load(path).convert_alpha()

def create_visual_spritesheet(
        visual: Visual,
        duration: Optional[float] = None,
        scale: Optional[float] = None,
        frames: Optional[Tuple[int, int]] = None,
        layer: int = 1
) -> SpriteSheet:
    """Get the sprite sheet for a visual."""
    if visual == Visual.Arrow:
        if duration is None:
            duration = 1.0 # Doesn't matter for single frame
        if scale is None:
            scale = gc.MINIFOLKS_SCALE
        if frames is not None:
            raise NotImplementedError("Arrow visual cannot specify frames")
        return SpriteSheet(
            surface=visual_sheets[visual],
            frame_width=16,
            frame_height=16,
            scale=scale,
            frames={AnimationType.IDLE: 1},
            rows={AnimationType.IDLE: 0},
            animation_durations={AnimationType.IDLE: duration},
            sprite_center_offset=(-.5, -.5),
            layer=layer
        )
    elif visual == Visual.CrusaderBlackKnightFear:
        if duration is None:
            duration = 0.2
        if scale is None:
            scale = gc.TINY_RPG_SCALE
        if frames is None:
            frames = (0, 6)
        return SpriteSheet(
            surface=visual_sheets[visual],
            frame_width=96,
            frame_height=96,
            scale=scale,
            frames={AnimationType.IDLE: frames[1] - frames[0]},
            rows={AnimationType.IDLE: 0},
            animation_durations={AnimationType.IDLE: duration},
            sprite_center_offset=(0, 0),
            start_frames={AnimationType.IDLE: frames[0]},
            layer=layer
        )
    elif visual == Visual.CoreBarbarianAttack:
        if duration is None:
            duration = 0.2
        if scale is None:
            scale = gc.TINY_RPG_SCALE
        if frames is None:
            frames = (6, 10)
        return SpriteSheet(
            surface=visual_sheets[visual],
            frame_width=100,
            frame_height=100,
            scale=scale,
            frames={AnimationType.IDLE: frames[1] - frames[0]},
            rows={AnimationType.IDLE: 11},
            animation_durations={AnimationType.IDLE: duration},
            sprite_center_offset=(-2, 2),
            start_frames={AnimationType.IDLE: frames[0]},
            layer=layer
        )
    elif visual == Visual.CrusaderCatapultBall:
        if duration is None:
            duration = 0.2
        if scale is None:
            scale = gc.TINY_RPG_SCALE
        if frames is None:
            frames = (0, 1)
        return SpriteSheet(
            surface=visual_sheets[visual],
            frame_width=128,
            frame_height=96,
            scale=scale,
            frames={AnimationType.IDLE: frames[1] - frames[0]},
            rows={AnimationType.IDLE: 0},
            animation_durations={AnimationType.IDLE: duration},
            sprite_center_offset=(0, 0),
            start_frames={AnimationType.IDLE: frames[0]},
            layer=layer
        )
    elif visual == Visual.CrusaderCatapultBallExplosion:
        if duration is None:
            duration = 0.5
        if scale is None:
            scale = gc.TINY_RPG_SCALE
        if frames is None:
            frames = (1, 5)
        return SpriteSheet(
            surface=visual_sheets[visual],
            frame_width=128,
            frame_height=96,
            scale=scale,
            frames={AnimationType.IDLE: frames[1] - frames[0]},
            rows={AnimationType.IDLE: 0},
            animation_durations={AnimationType.IDLE: duration},
            sprite_center_offset=(0, 0),
            start_frames={AnimationType.IDLE: frames[0]},
            layer=layer
        )
    elif visual == Visual.CrusaderCatapultBallRemains:
        if duration is None:
            duration = 0.5
        if scale is None:
            scale = gc.TINY_RPG_SCALE
        if frames is None:
            frames = (5, 6)
        return SpriteSheet(
            surface=visual_sheets[visual],
            frame_width=128,
            frame_height=96,
            scale=scale,
            frames={AnimationType.IDLE: frames[1] - frames[0]},
            rows={AnimationType.IDLE: 0},
            animation_durations={AnimationType.IDLE: duration},
            sprite_center_offset=(0, 0),
            start_frames={AnimationType.IDLE: frames[0]},
            layer=layer
        )
    elif visual == Visual.CrusaderGoldKnightAttack:
        if duration is None:
            duration = 0.2
        if scale is None:
            scale = gc.TINY_RPG_SCALE
        if frames is None:
            frames = (0, 4)
        return SpriteSheet(
            surface=visual_sheets[visual],
            frame_width=100,
            frame_height=100,
            scale=scale,
            frames={AnimationType.IDLE: frames[1] - frames[0]},
            rows={AnimationType.IDLE: 0},
            animation_durations={AnimationType.IDLE: duration},
            sprite_center_offset=(0, 0),
            start_frames={AnimationType.IDLE: frames[0]},
            layer=layer
        )
    elif visual == Visual.CrusaderRedKnightFireSlash:
        if duration is None:
            duration = 0.2
        if scale is None:
            scale = gc.TINY_RPG_SCALE
        if frames is not None:
            raise NotImplementedError("CrusaderRedKnightFireSlash visual cannot specify frames")
        return SpriteSheet(
            surface=visual_sheets[visual],
            frame_width=100,
            frame_height=100,
            scale=scale,
            frames={AnimationType.IDLE: 3},
            rows={AnimationType.IDLE: 0},
            animation_durations={AnimationType.IDLE: duration},
            sprite_center_offset=(0, 0),
            layer=layer
        )
    elif visual == Visual.Explosion:
        if duration is None:
            duration = 0.2
        if scale is None:
            scale = gc.TINY_RPG_SCALE
        if frames is not None:
            raise NotImplementedError("Explosion visual cannot specify frames")
        return SpriteSheet(
            surface=visual_sheets[visual],
            frame_width=32,
            frame_height=32,
            scale=scale,
            frames={AnimationType.IDLE: 6},
            rows={AnimationType.IDLE: 0},
            animation_durations={AnimationType.IDLE: duration},
            sprite_center_offset=(0, 0),
            layer=layer
        )
    elif visual == Visual.Fear:
        if duration is None:
            duration = 0.2
        if scale is None:
            scale = gc.TINY_RPG_SCALE
        if frames is not None:
            raise NotImplementedError("Fear visual cannot specify frames")
        return SpriteSheet(
            surface=visual_sheets[visual],
            frame_width=32,
            frame_height=32,
            scale=scale,
            frames={AnimationType.IDLE: 2},
            rows={AnimationType.IDLE: 0},
            animation_durations={AnimationType.IDLE: duration},
            sprite_center_offset=(0, 0),
            layer=layer
        )
    elif visual == Visual.Fireball:
        if duration is None:
            duration = 0.2
        if scale is None:
            scale = gc.TINY_RPG_SCALE
        if frames is not None:
            raise NotImplementedError("Fireball visual cannot specify frames")
        return SpriteSheet(
            surface=visual_sheets[visual],
            frame_width=100,
            frame_height=100,
            scale=scale,
            frames={AnimationType.IDLE: 4},
            rows={AnimationType.IDLE: 5},
            animation_durations={AnimationType.IDLE: duration},
            sprite_center_offset=(-5, -2),
            layer=layer
        )
    elif visual == Visual.Healing:
        if duration is None:
            duration = 1.0
        if scale is None:
            scale = gc.TINY_RPG_SCALE
        if frames is not None:
            raise NotImplementedError("Healing visual cannot specify frames")
        return SpriteSheet(
            surface=visual_sheets[visual],
            frame_width=100,
            frame_height=100,
            scale=scale,
            frames={AnimationType.IDLE: 4},
            rows={AnimationType.IDLE: 5},
            animation_durations={AnimationType.IDLE: duration},
            sprite_center_offset=(0, 0),
            layer=layer
        )
    elif visual == Visual.Ignited:
        if duration is None:
            duration = 0.2
        if scale is None:
            scale = gc.TINY_RPG_SCALE
        if frames is None:
            raise NotImplementedError("Ignited visual cannot specify frames")
        return SpriteSheet(
            surface=visual_sheets[visual],
            frame_width=32,
            frame_height=32,
            scale=scale,
            frames={AnimationType.IDLE: 3},
            rows={AnimationType.IDLE: 0},
            animation_durations={AnimationType.IDLE: duration},
            sprite_center_offset=(0, 0),
            layer=layer
        )
    elif visual == Visual.Tongue:
        if duration is None:
            duration = 0.2
        if scale is None:
            scale = 1
        if frames is None:
            frames = (0, 1)
        return SpriteSheet(
            surface=visual_sheets[visual],
            frame_width=8,
            frame_height=8,
            scale=scale,
            frames={AnimationType.IDLE: frames[1] - frames[0]},
            rows={AnimationType.IDLE: 0},
            animation_durations={AnimationType.IDLE: duration},
            sprite_center_offset=(0, 0),
            layer=layer
        )
    elif visual == Visual.TongueTip:
        if duration is None:
            duration = 0.2
        if scale is None:
            scale = 1
        if frames is None:
            frames = (0, 1)
        return SpriteSheet(
            surface=visual_sheets[visual],
            frame_width=8,
            frame_height=8,
            scale=scale,
            frames={AnimationType.IDLE: frames[1] - frames[0]},
            rows={AnimationType.IDLE: 0},
            animation_durations={AnimationType.IDLE: duration},
            sprite_center_offset=(0, 0),
            layer=layer
        )
