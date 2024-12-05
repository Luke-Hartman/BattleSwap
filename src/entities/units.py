"""Unit creation module for Battle Swap.

This module contains functions for creating different types of units with their corresponding components.
"""

import esper
import pygame
import os
from typing import Dict
from components.hitbox import Hitbox
from components.range_indicator import RangeIndicator
from components.stats_card import StatsCard
from game_constants import gc
from components.ability import Abilities, Ability, Cooldown, HasTarget, SatisfiesUnitCondition
from components.armor import Armor
from components.aura import Aura
from components.position import Position
from components.animation import AnimationState, AnimationType
from components.sprite_sheet import SpriteSheet
from components.status_effect import CrusaderCommanderEmpowered, Fleeing, Healing, Ignited, StatusEffects
from target_strategy import ByDistance, ByMaxHealth, ByMissingHealth, TargetStrategy
from components.destination import Destination
from components.team import Team, TeamType
from components.unit_state import UnitState
from components.movement import Movement
from components.unit_type import UnitType, UnitTypeComponent
from components.velocity import Velocity
from components.health import Health
from components.orientation import Orientation, FacingDirection
from effects import AppliesStatusEffect, CreatesAoE, CreatesAttachedVisual, CreatesProjectile, Damages, Heals, PlaySound, Recipient, SoundEffect
from unit_condition import (
    All, Alive, HealthBelowPercent, Never, NotEntity, OnTeam,
    MaximumDistanceFromEntity
)
from visuals import Visual

unit_theme_ids: Dict[UnitType, str] = {
    UnitType.CORE_ARCHER: "#core_archer_icon", 
    UnitType.CORE_DUELIST: "#core_duelist_icon",
    UnitType.CORE_HORSEMAN: "#core_horseman_icon",
    UnitType.CORE_MAGE: "#core_mage_icon",
    UnitType.CORE_SWORDSMAN: "#core_swordsman_icon",
    UnitType.CRUSADER_BLACK_KNIGHT: "#crusader_black_knight_icon",
    UnitType.CRUSADER_CLERIC: "#crusader_cleric_icon",
    UnitType.CRUSADER_COMMANDER: "#crusader_commander_icon",
    UnitType.CRUSADER_DEFENDER: "#crusader_defender_icon",
    UnitType.CRUSADER_GOLD_KNIGHT: "#crusader_gold_knight_icon",
    UnitType.CRUSADER_LONGBOWMAN: "#crusader_longbowman_icon",
    UnitType.CRUSADER_PALADIN: "#crusader_paladin_icon",
    UnitType.CRUSADER_PIKEMAN: "#crusader_pikeman_icon",
    UnitType.CRUSADER_RED_KNIGHT: "#crusader_red_knight_icon",
    UnitType.WEREBEAR: "#werebear_icon",
}

unit_icon_surfaces: Dict[UnitType, pygame.Surface] = {}

sprite_sheets: Dict[TeamType, Dict[UnitType, pygame.Surface]] = {
    TeamType.TEAM1: {},
    TeamType.TEAM2: {}
}

def load_sprite_sheets():
    """Load all sprite sheets and unit icons."""
    unit_filenames = {
        UnitType.CORE_ARCHER: "CoreArcher.png", 
        UnitType.CORE_DUELIST: "CoreDuelist.png",
        UnitType.CORE_HORSEMAN: "CoreHorseman.png",
        UnitType.CORE_MAGE: "CoreMage.png",
        UnitType.CORE_SWORDSMAN: "CoreSwordsman.png", 
        UnitType.CRUSADER_BLACK_KNIGHT: "CrusaderBlackKnight.png",
        UnitType.CRUSADER_CLERIC: "CrusaderCleric.png",
        UnitType.CRUSADER_COMMANDER: "CrusaderCommander.png",
        UnitType.CRUSADER_DEFENDER: "CrusaderDefender.png",
        UnitType.CRUSADER_GOLD_KNIGHT: "CrusaderGoldKnight.png",
        UnitType.CRUSADER_LONGBOWMAN: "CrusaderLongbowman.png",
        UnitType.CRUSADER_PALADIN: "CrusaderPaladin.png",
        UnitType.CRUSADER_PIKEMAN: "CrusaderPikeman.png",
        UnitType.CRUSADER_RED_KNIGHT: "CrusaderRedKnight.png",
        UnitType.WEREBEAR: "Werebear.png",
    }
    for unit_type, filename in unit_filenames.items():
        path = os.path.join("assets", "units", filename)
        sprite_sheets[unit_type] = pygame.image.load(path).convert_alpha()

    # Load unit icons
    unit_icon_paths: Dict[UnitType, str] = {
        UnitType.CORE_ARCHER: "CoreArcherIcon.png",
        UnitType.CORE_DUELIST: "CoreDuelistIcon.png",
        UnitType.CORE_HORSEMAN: "CoreHorsemanIcon.png",
        UnitType.CORE_MAGE: "CoreMageIcon.png",
        UnitType.CORE_SWORDSMAN: "CoreSwordsmanIcon.png",
        UnitType.CRUSADER_BLACK_KNIGHT: "CrusaderBlackKnightIcon.png",
        UnitType.CRUSADER_CLERIC: "CrusaderClericIcon.png",
        UnitType.CRUSADER_COMMANDER: "CrusaderCommanderIcon.png",
        UnitType.CRUSADER_DEFENDER: "CrusaderDefenderIcon.png",
        UnitType.CRUSADER_GOLD_KNIGHT: "CrusaderGoldKnightIcon.png",
        UnitType.CRUSADER_LONGBOWMAN: "CrusaderLongbowmanIcon.png",
        UnitType.CRUSADER_PALADIN: "CrusaderPaladinIcon.png",
        UnitType.CRUSADER_PIKEMAN: "CrusaderPikemanIcon.png",
        UnitType.CRUSADER_RED_KNIGHT: "CrusaderRedKnightIcon.png",
        UnitType.WEREBEAR: "WerebearIcon.png",
    }
    for unit_type, filename in unit_icon_paths.items():
        path = os.path.join("assets", "icons", filename)
        unit_icon_surfaces[unit_type] = pygame.image.load(path).convert_alpha()

def create_unit(x: int, y: int, unit_type: UnitType, team: TeamType) -> int:
    """Create a unit entity with all necessary components."""
    return {
        UnitType.CORE_ARCHER: create_core_archer,
        UnitType.CORE_DUELIST: create_core_duelist,
        UnitType.CORE_HORSEMAN: create_core_horseman,
        UnitType.CORE_MAGE: create_core_mage,
        UnitType.CORE_SWORDSMAN: create_core_swordsman,
        UnitType.CRUSADER_BLACK_KNIGHT: create_crusader_black_knight,
        UnitType.CRUSADER_CLERIC: create_crusader_cleric,
        UnitType.CRUSADER_COMMANDER: create_crusader_commander,
        UnitType.CRUSADER_DEFENDER: create_crusader_defender,
        UnitType.CRUSADER_GOLD_KNIGHT: create_crusader_gold_knight,
        UnitType.CRUSADER_LONGBOWMAN: create_crusader_longbowman,
        UnitType.CRUSADER_PALADIN: create_crusader_paladin,
        UnitType.CRUSADER_PIKEMAN: create_crusader_pikeman,
        UnitType.CRUSADER_RED_KNIGHT: create_crusader_red_knight,
        UnitType.WEREBEAR: create_werebear,
    }[unit_type](x, y, team)

def unit_base_entity(
        x: int,
        y: int,
        team: TeamType,
        unit_type: UnitType,
        movement_speed: float,
        health: int,
        hitbox: Hitbox
    ) -> int:
    """Create a unit entity with all components shared by all units."""
    entity = esper.create_entity()
    esper.add_component(entity, Position(x=x, y=y))
    esper.add_component(entity, Velocity(x=0, y=0))
    esper.add_component(entity, Movement(speed=movement_speed))
    esper.add_component(entity, AnimationState(type=AnimationType.IDLE))
    esper.add_component(entity, Team(type=team))
    esper.add_component(entity, UnitState())
    esper.add_component(entity, UnitTypeComponent(type=unit_type))
    esper.add_component(entity, Health(current=health, maximum=health))
    esper.add_component(entity, StatusEffects())
    esper.add_component(entity, Orientation(
        facing=FacingDirection.RIGHT if team == TeamType.TEAM1 else FacingDirection.LEFT
    ))
    esper.add_component(entity, hitbox)
    return entity

def create_core_archer(x: int, y: int, team: TeamType) -> int:
    """Create an archer entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CORE_ARCHER,
        movement_speed=gc.CORE_ARCHER_MOVEMENT_SPEED,
        health=gc.CORE_ARCHER_HP,
        hitbox=Hitbox(
            width=16,
            height=32,
        )
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=All([OnTeam(team=team.other()), Alive()])
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=0)
    )
    esper.add_component(
        entity,
        RangeIndicator(range=gc.CORE_ARCHER_ATTACK_RANGE)
    )
    esper.add_component(
        entity,
        Abilities(
            abilities=[
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CORE_ARCHER_ATTACK_RANGE,
                                    y_bias=None
                                )
                            ])
                        )
                    ],
                    persistent_conditions=[
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CORE_ARCHER_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=None
                                )
                            ])
                        )
                    ],
                    effects={
                        7: [
                            CreatesProjectile(
                                projectile_speed=gc.CORE_ARCHER_PROJECTILE_SPEED,
                                effects=[
                                    Damages(damage=gc.CORE_ARCHER_ATTACK_DAMAGE, recipient=Recipient.TARGET),
                                ],
                                visual=Visual.Arrow,
                                projectile_offset_x=5*gc.MINIFOLKS_SCALE,
                                projectile_offset_y=0,
                            ),
                            PlaySound(
                                sound_effects=[
                                    (SoundEffect(filename="arrow_fired_from_bow.wav", volume=0.25), 1.0),
                                ]
                            )
                        ]
                    },
                )
            ]
        )
    )
    esper.add_component(entity, SpriteSheet(
        surface=sprite_sheets[UnitType.CORE_ARCHER],
        frame_width=32,
        frame_height=32,
        scale=gc.MINIFOLKS_SCALE,
        frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ABILITY1: 11, AnimationType.DYING: 4},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 3, AnimationType.DYING: 6},
        animation_durations={
            AnimationType.IDLE: gc.CORE_ARCHER_ANIMATION_IDLE_DURATION,
            AnimationType.WALKING: gc.CORE_ARCHER_ANIMATION_WALKING_DURATION,
            AnimationType.ABILITY1: gc.CORE_ARCHER_ANIMATION_ATTACK_DURATION,
            AnimationType.DYING: gc.CORE_ARCHER_ANIMATION_DYING_DURATION,
        },
        sprite_center_offset=(0, -8),
    ))
    esper.add_component(
        entity,
        StatsCard(
            text=[
                f"Name: Archer",
                f"Faction: Core",
                f"Health: {gc.CORE_ARCHER_HP}",
                f"Attack: {gc.CORE_ARCHER_ATTACK_DAMAGE}",
                f"DPS: {round(gc.CORE_ARCHER_ATTACK_DAMAGE/gc.CORE_ARCHER_ANIMATION_ATTACK_DURATION, 2)}",
                f"Speed: {gc.CORE_ARCHER_MOVEMENT_SPEED}",
                f"Range: {gc.CORE_ARCHER_ATTACK_RANGE}",
                f"Projectile Speed: {gc.CORE_ARCHER_PROJECTILE_SPEED}",
                f"AI: Targets the nearest enemy, preferring units at the same height on the y-axis",
            ]
        )
    )
    return entity

def create_core_duelist(x: int, y: int, team: TeamType) -> int:
    """Create a fancy swordsman entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CORE_DUELIST,
        movement_speed=gc.CORE_DUELIST_MOVEMENT_SPEED,
        health=gc.CORE_DUELIST_HP,
        hitbox=Hitbox(
            width=16,
            height=36,
        )
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=All([OnTeam(team=team.other()), Alive()])
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.CORE_DUELIST_ATTACK_RANGE*2/3)
    )
    sound_effects = [
        (SoundEffect(filename=f"quick_sword_thrust{i}.wav", volume=0.75), 1.0)
        for i in range(1, 6)
    ]
    esper.add_component(
        entity,
        Abilities(
            abilities=[
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CORE_DUELIST_ATTACK_RANGE,
                                    y_bias=5
                                ),
                            ])
                        )
                    ],
                    persistent_conditions=[
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CORE_DUELIST_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=5
                                ),
                            ])
                        )
                    ],
                    effects={
                        5: [
                            Damages(damage=gc.CORE_DUELIST_ATTACK_DAMAGE/7, recipient=Recipient.TARGET),
                            PlaySound(sound_effects),
                        ],
                        6: [
                            Damages(damage=gc.CORE_DUELIST_ATTACK_DAMAGE/7, recipient=Recipient.TARGET),
                            PlaySound(sound_effects),
                        ],
                        7: [
                            Damages(damage=gc.CORE_DUELIST_ATTACK_DAMAGE/7, recipient=Recipient.TARGET),
                            PlaySound(sound_effects),
                        ],
                        8: [
                            Damages(damage=gc.CORE_DUELIST_ATTACK_DAMAGE/7, recipient=Recipient.TARGET),
                            PlaySound(sound_effects),
                        ],
                        9: [
                            Damages(damage=gc.CORE_DUELIST_ATTACK_DAMAGE/7, recipient=Recipient.TARGET),
                            PlaySound(sound_effects),
                        ],
                        10: [
                            Damages(damage=gc.CORE_DUELIST_ATTACK_DAMAGE/7, recipient=Recipient.TARGET),
                            PlaySound(sound_effects),
                        ],
                        11: [
                            Damages(damage=gc.CORE_DUELIST_ATTACK_DAMAGE/7, recipient=Recipient.TARGET),
                            PlaySound(sound_effects),
                        ],
                    },
                )
            ]
        )
    )
    esper.add_component(entity, SpriteSheet(
        surface=sprite_sheets[UnitType.CORE_DUELIST],
        frame_width=100,
        frame_height=100,
        scale=gc.TINY_RPG_SCALE,
        frames={AnimationType.IDLE: 4, AnimationType.WALKING: 8, AnimationType.ABILITY1: 12, AnimationType.DYING: 4},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 4, AnimationType.DYING: 6},
        animation_durations={
            AnimationType.IDLE: gc.CORE_DUELIST_ANIMATION_IDLE_DURATION,
            AnimationType.WALKING: gc.CORE_DUELIST_ANIMATION_WALKING_DURATION,
            AnimationType.ABILITY1: gc.CORE_DUELIST_ANIMATION_ATTACK_DURATION,
            AnimationType.DYING: gc.CORE_DUELIST_ANIMATION_DYING_DURATION,
        },
        sprite_center_offset=(0, 2),
    ))
    esper.add_component(
        entity,
        StatsCard(
            text=[
                f"Name: Duelist",
                f"Faction: Core",
                f"Health: {gc.CORE_DUELIST_HP}",
                f"Attack: {round(gc.CORE_DUELIST_ATTACK_DAMAGE/7, 2)} * 7",
                f"DPS: {round(gc.CORE_DUELIST_ATTACK_DAMAGE/gc.CORE_DUELIST_ANIMATION_ATTACK_DURATION, 2)}",
                f"Speed: {gc.CORE_DUELIST_MOVEMENT_SPEED}",
                f"Range: {gc.CORE_DUELIST_ATTACK_RANGE}",
                f"AI: Targets the nearest enemy, preferring units at the same height on the y-axis",
            ]
        )
    )
    return entity

def create_core_horseman(x: int, y: int, team: TeamType) -> int:
    """Create a horseman entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CORE_HORSEMAN,
        movement_speed=gc.CORE_HORSEMAN_MOVEMENT_SPEED,
        health=gc.  CORE_HORSEMAN_HP,
        hitbox=Hitbox(
            width=32,
            height=46,
        )
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=All([OnTeam(team=team.other()), Alive()])
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.CORE_HORSEMAN_ATTACK_RANGE*2/3)
    )
    esper.add_component(
        entity,
        Abilities(
            abilities=[
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CORE_HORSEMAN_ATTACK_RANGE,
                                    y_bias=5
                                ),
                            ])
                        )
                    ],
                    persistent_conditions=[
                        HasTarget(
                            unit_condition=All([
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CORE_HORSEMAN_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=5
                                ),
                            ])
                        )
                    ],
                    effects={3: [
                        Damages(damage=gc.CORE_HORSEMAN_ATTACK_DAMAGE, recipient=Recipient.TARGET),
                        PlaySound([
                            (SoundEffect(filename=f"sword_swoosh{i+1}.wav", volume=0.50), 1.0) for i in range(3)
                        ]),
                    ]},
                )
            ]
        )
    )
    esper.add_component(entity, SpriteSheet(
        surface=sprite_sheets[UnitType.CORE_HORSEMAN],
        frame_width=32,
        frame_height=32,
        scale=gc.MINIFOLKS_SCALE,
        frames={AnimationType.IDLE: 8, AnimationType.WALKING: 6, AnimationType.ABILITY1: 7, AnimationType.DYING: 6},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 4, AnimationType.DYING: 6},
        animation_durations={
            AnimationType.IDLE: gc.CORE_HORSEMAN_ANIMATION_IDLE_DURATION,
            AnimationType.WALKING: gc.CORE_HORSEMAN_ANIMATION_WALKING_DURATION,
            AnimationType.ABILITY1: gc.CORE_HORSEMAN_ANIMATION_ATTACK_DURATION,
            AnimationType.DYING: gc.CORE_HORSEMAN_ANIMATION_DYING_DURATION,
        },
        sprite_center_offset=(1, -6),
    ))
    esper.add_component(
        entity,
        StatsCard(
            text=[
                f"Name: Horseman",
                f"Faction: Core",
                f"Health: {gc.CORE_HORSEMAN_HP}",
                f"Attack: {gc.CORE_HORSEMAN_ATTACK_DAMAGE}",
                f"DPS: {round(gc.CORE_HORSEMAN_ATTACK_DAMAGE/gc.CORE_HORSEMAN_ANIMATION_ATTACK_DURATION, 2)}",
                f"Speed: {gc.CORE_HORSEMAN_MOVEMENT_SPEED}",
                f"Range: {gc.CORE_HORSEMAN_ATTACK_RANGE}",
                f"AI: Targets the nearest enemy, preferring units at the same height on the y-axis",
            ]
        )
    )
    return entity

def create_core_mage(x: int, y: int, team: TeamType) -> int:
    """Create a mage entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CORE_MAGE,
        movement_speed=gc.CORE_MAGE_MOVEMENT_SPEED,
        health=gc.CORE_MAGE_HP,
        hitbox=Hitbox(
            width=24,
            height=36,
        )
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=All([OnTeam(team=team.other()), Alive()])
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=0)
    )
    esper.add_component(
        entity,
        RangeIndicator(range=gc.CORE_MAGE_ATTACK_RANGE)
    )
    esper.add_component(
        entity,
        Abilities(
            abilities=[
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CORE_MAGE_ATTACK_RANGE,
                                    y_bias=None
                                )
                            ])
                        )
                    ],
                    persistent_conditions=[
                        HasTarget(
                            unit_condition=All([
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CORE_MAGE_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=None
                                )
                            ])
                        )
                    ],
                    effects={
                        0: [
                            PlaySound(SoundEffect(filename="fireball_channeling.wav", volume=0.50)),
                        ],
                        6: [
                            PlaySound(SoundEffect(filename="fireball_creation.wav", volume=0.50)),
                        ],
                        7: [
                            CreatesProjectile(
                                projectile_speed=gc.CORE_MAGE_PROJECTILE_SPEED,
                                effects=[
                                    CreatesAoE(
                                        effects=[
                                            Damages(damage=gc.CORE_MAGE_ATTACK_DAMAGE, recipient=Recipient.TARGET),
                                            AppliesStatusEffect(
                                                status_effect=Ignited(
                                                    dps=gc.CORE_MAGE_IGNITE_DAMAGE/gc.CORE_MAGE_IGNITE_DURATION,
                                                    time_remaining=gc.CORE_MAGE_IGNITE_DURATION
                                                ),
                                                recipient=Recipient.TARGET
                                            ),
                                        ],
                                        visual=Visual.Explosion,
                                        duration=gc.CORE_MAGE_FIREBALL_AOE_DURATION,
                                        scale=gc.CORE_MAGE_FIREBALL_AOE_SCALE,
                                        unit_condition=Alive(),
                                        location=Recipient.PARENT,
                                    ),
                                    PlaySound(SoundEffect(filename="fireball_impact.wav", volume=0.50)),
                                ],
                                visual=Visual.Fireball,
                                projectile_offset_x=11*gc.MINIFOLKS_SCALE,
                                projectile_offset_y=-4*gc.MINIFOLKS_SCALE,
                            ),
                        ]
                    }
                )
            ]
        )
    )
    esper.add_component(entity, SpriteSheet(
        surface=sprite_sheets[UnitType.CORE_MAGE],
        frame_width=32,
        frame_height=32,
        scale=gc.MINIFOLKS_SCALE,
        frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ABILITY1: 11, AnimationType.DYING: 9},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 3, AnimationType.DYING: 7},
        animation_durations={
            AnimationType.IDLE: gc.CORE_MAGE_ANIMATION_IDLE_DURATION,
            AnimationType.WALKING: gc.CORE_MAGE_ANIMATION_WALKING_DURATION,
            AnimationType.ABILITY1: gc.CORE_MAGE_ANIMATION_ATTACK_DURATION,
            AnimationType.DYING: gc.CORE_MAGE_ANIMATION_DYING_DURATION,
        },
        sprite_center_offset=(0, -8),
    ))
    esper.add_component(
        entity,
        StatsCard(
            text=[
                f"Name: Mage",
                f"Faction: Core",
                f"Health: {gc.CORE_MAGE_HP}",
                f"Attack: {gc.CORE_MAGE_ATTACK_DAMAGE}",
                f"DPS: {round(gc.CORE_MAGE_ATTACK_DAMAGE/gc.CORE_MAGE_ANIMATION_ATTACK_DURATION, 2)}",
                f"Speed: {gc.CORE_MAGE_MOVEMENT_SPEED}",
                f"Range: {gc.CORE_MAGE_ATTACK_RANGE}",
                f"Projectile Speed: {gc.CORE_MAGE_PROJECTILE_SPEED}",
                f"Special: Fireball attack explodes, damaging all units in an AoE and igniting them for {gc.CORE_MAGE_IGNITE_DAMAGE} over {gc.CORE_MAGE_IGNITE_DURATION} seconds.",
                f"AI: Targets the nearest enemy, preferring units at the same height on the y-axis",
            ]
        )
    )
    return entity

def create_core_swordsman(x: int, y: int, team: TeamType) -> int:
    """Create a swordsman entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CORE_SWORDSMAN,
        movement_speed=gc.CORE_SWORDSMAN_MOVEMENT_SPEED,
        health=gc.CORE_SWORDSMAN_HP,
        hitbox=Hitbox(
            width=16,
            height=32,
        )
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=All([OnTeam(team=team.other()), Alive()])
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.CORE_SWORDSMAN_ATTACK_RANGE*2/3)
    )
    esper.add_component(
        entity,
        Abilities(
            abilities=[
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CORE_SWORDSMAN_ATTACK_RANGE,
                                    y_bias=3
                                ),
                            ])
                        )
                    ],
                    persistent_conditions=[
                        HasTarget(
                            unit_condition=All([
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CORE_SWORDSMAN_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=3
                                ),
                            ])
                        )
                    ],
                    effects={2: [
                            Damages(damage=gc.CORE_SWORDSMAN_ATTACK_DAMAGE, recipient=Recipient.TARGET),
                            PlaySound([
                                (SoundEffect(filename=f"sword_swoosh{i+1}.wav", volume=0.50), 1.0) for i in range(3)
                            ]),
                        ]
                    },
                )
            ]
        )
    )
    esper.add_component(entity, SpriteSheet(
        surface=sprite_sheets[UnitType.CORE_SWORDSMAN],
        frame_width=32,
        frame_height=32,
        scale=gc.MINIFOLKS_SCALE,
        frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ABILITY1: 6, AnimationType.DYING: 4},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 3, AnimationType.DYING: 5},
        animation_durations={
            AnimationType.IDLE: gc.CORE_SWORDSMAN_ANIMATION_IDLE_DURATION,
            AnimationType.WALKING: gc.CORE_SWORDSMAN_ANIMATION_WALKING_DURATION,
            AnimationType.ABILITY1: gc.CORE_SWORDSMAN_ANIMATION_ATTACK_DURATION,
            AnimationType.DYING: gc.CORE_SWORDSMAN_ANIMATION_DYING_DURATION,
        },
        sprite_center_offset=(0, -8),
    ))
    esper.add_component(
        entity,
        StatsCard(
            text=[
                f"Name: Swordsman",
                f"Faction: Core",
                f"Health: {gc.CORE_SWORDSMAN_HP}",
                f"Attack: {gc.CORE_SWORDSMAN_ATTACK_DAMAGE}",
                f"DPS: {round(gc.CORE_SWORDSMAN_ATTACK_DAMAGE/gc.CORE_SWORDSMAN_ANIMATION_ATTACK_DURATION, 2)}",
                f"Speed: {gc.CORE_SWORDSMAN_MOVEMENT_SPEED}",
                f"Range: {gc.CORE_SWORDSMAN_ATTACK_RANGE}",
                f"AI: Targets the nearest enemy, preferring units at the same height on the y-axis",
            ]
        )
    )
    return entity

def create_crusader_black_knight(x: int, y: int, team: TeamType) -> int:
    """Create a black knight entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CRUSADER_BLACK_KNIGHT,
        movement_speed=gc.CRUSADER_BLACK_KNIGHT_MOVEMENT_SPEED,
        health=gc.CRUSADER_BLACK_KNIGHT_HP,
        hitbox=Hitbox(
            width=50,
            height=54,
        )
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByMaxHealth(ascending=True),
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=All([OnTeam(team=team.other()), Alive()])
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.CRUSADER_BLACK_KNIGHT_ATTACK_RANGE*2/3)
    )
    esper.add_component(
        entity,
        Abilities(
            abilities=[
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CRUSADER_BLACK_KNIGHT_ATTACK_RANGE,
                                    y_bias=5
                                ),
                            ])
                        )
                    ],
                    persistent_conditions=[
                        HasTarget(
                            unit_condition=All([
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CRUSADER_BLACK_KNIGHT_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=5
                                ),
                            ])
                        )
                    ],
                    effects={2: [
                        Damages(
                            damage=gc.CRUSADER_BLACK_KNIGHT_ATTACK_DAMAGE,
                            recipient=Recipient.TARGET,
                            on_kill_effects=[
                                CreatesAoE(
                                    effects=[
                                        AppliesStatusEffect(
                                            status_effect=Fleeing(
                                                time_remaining=gc.CRUSADER_BLACK_KNIGHT_FLEE_DURATION,
                                                entity=entity
                                            ),
                                            recipient=Recipient.TARGET
                                        ),
                                        CreatesAttachedVisual(
                                            visual=Visual.Fear,
                                            animation_duration=0.3,
                                            expiration_duration=gc.CRUSADER_BLACK_KNIGHT_FLEE_DURATION,
                                            scale=gc.TINY_RPG_SCALE,
                                            remove_on_death=True,
                                            unique_key=lambda e: f"FLEE {e}",
                                            offset=lambda e: (0, -esper.component_for_entity(e, Hitbox).height/2),
                                            layer=1
                                        )
                                    ],
                                    duration=gc.CRUSADER_BLACK_KNIGHT_FEAR_AOE_DURATION,
                                    scale=gc.CRUSADER_BLACK_KNIGHT_FEAR_AOE_SCALE,
                                    unit_condition=All([Alive(), NotEntity(entity=entity)]),
                                    visual=Visual.CrusaderBlackKnightFear,
                                    location=Recipient.PARENT,
                                ),
                                PlaySound(SoundEffect(filename="black_knight_screech.wav", volume=0.50)),
                            ]
                        ),
                        PlaySound([
                            (SoundEffect(filename=f"sword_swoosh{i+1}.wav", volume=0.50), 1.0) for i in range(3)
                        ]),
                    ]},
                )
            ]
        )
    )
    esper.add_component(entity, SpriteSheet(
        surface=sprite_sheets[UnitType.CRUSADER_BLACK_KNIGHT],
        frame_width=100,
        frame_height=100,
        scale=gc.TINY_RPG_SCALE,
        frames={AnimationType.IDLE: 6, AnimationType.WALKING: 8, AnimationType.ABILITY1: 6, AnimationType.DYING: 4},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 3, AnimationType.DYING: 6},
        animation_durations={
            AnimationType.IDLE: gc.CRUSADER_BLACK_KNIGHT_ANIMATION_IDLE_DURATION,
            AnimationType.WALKING: gc.CRUSADER_BLACK_KNIGHT_ANIMATION_WALKING_DURATION,
            AnimationType.ABILITY1: gc.CRUSADER_BLACK_KNIGHT_ANIMATION_ATTACK_DURATION,
            AnimationType.DYING: gc.CRUSADER_BLACK_KNIGHT_ANIMATION_DYING_DURATION,
        },
        sprite_center_offset=(0, 7),
    ))
    esper.add_component(
        entity,
        StatsCard(
            text=[
                f"Name: Black Knight",
                f"Faction: Crusader",
                f"Health: {gc.CRUSADER_BLACK_KNIGHT_HP}",
                f"Attack: {gc.CRUSADER_BLACK_KNIGHT_ATTACK_DAMAGE}",
                f"DPS: {round(gc.CRUSADER_BLACK_KNIGHT_ATTACK_DAMAGE/gc.CRUSADER_BLACK_KNIGHT_ANIMATION_ATTACK_DURATION, 2)}",
                f"Speed: {gc.CRUSADER_BLACK_KNIGHT_MOVEMENT_SPEED}",
                f"Range: {gc.CRUSADER_BLACK_KNIGHT_ATTACK_RANGE}",
                f"Fear Duration: {gc.CRUSADER_BLACK_KNIGHT_FLEE_DURATION}",
                f"Special: Killing blows inflict fear on all other units in an AoE around the black knight.",
                f"AI: Targets the lowest health enemy, ties broken by distance.",
            ]
        )
    )
    return entity

def create_crusader_cleric(x: int, y: int, team: TeamType) -> int:
    """Create a cleric entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CRUSADER_CLERIC,
        movement_speed=gc.CRUSADER_CLERIC_MOVEMENT_SPEED,
        health=gc.CRUSADER_CLERIC_HP,
        hitbox=Hitbox(
            width=16,
            height=36,
        )
    )
    esper.add_component(
        entity,
        Destination(
            target_strategy=TargetStrategy(
                rankings=[
                    ByMaxHealth(ascending=False),
                    ByDistance(entity=entity, y_bias=2, ascending=True),
                ],
                unit_condition=All(
                    [
                        OnTeam(team=team),
                        Alive(),
                        NotEntity(entity=entity),
                    ]
                )
            ),
            x_offset=0,
            min_distance=gc.CRUSADER_CLERIC_ATTACK_RANGE*2/3
        )
    )
    esper.add_component(
        entity,
        RangeIndicator(range=gc.CRUSADER_CLERIC_ATTACK_RANGE)
    )
    esper.add_component(
        entity,
        Abilities(
            abilities=[
                Ability(
                    target_strategy=TargetStrategy(
                        rankings=[
                            ByMissingHealth(ascending=False),
                            ByDistance(entity=entity, y_bias=2, ascending=True),
                        ],
                        unit_condition=All([OnTeam(team=team), Alive(), HealthBelowPercent(percent=0.9)])
                    ),
                    trigger_conditions=[
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CRUSADER_CLERIC_ATTACK_RANGE,
                                    y_bias=None
                                )
                            ])
                        )
                    ],
                    persistent_conditions=[
                        HasTarget(
                            unit_condition=Alive()
                        )
                    ],
                    effects={
                        2: [
                            AppliesStatusEffect(
                                status_effect=Healing(time_remaining=2, dps=gc.CRUSADER_CLERIC_HEALING/2),
                                recipient=Recipient.TARGET
                            ),
                            CreatesAttachedVisual(
                                visual=Visual.Healing,
                                animation_duration=1,
                                expiration_duration=2,
                                scale=2,
                                remove_on_death=False,
                                random_starting_frame=True,
                                layer=1,
                            ),
                            PlaySound(SoundEffect(filename="heal.wav", volume=0.50)),
                        ]
                    },
                )
            ]
        )
    )
    esper.add_component(entity, SpriteSheet(
        surface=sprite_sheets[UnitType.CRUSADER_CLERIC],
        frame_width=100,
        frame_height=100,
        scale=gc.TINY_RPG_SCALE,
        frames={AnimationType.IDLE: 6, AnimationType.WALKING: 8, AnimationType.ABILITY1: 6, AnimationType.DYING: 4},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 4, AnimationType.DYING: 7},
        animation_durations={
            AnimationType.IDLE: gc.CRUSADER_CLERIC_ANIMATION_IDLE_DURATION,
            AnimationType.WALKING: gc.CRUSADER_CLERIC_ANIMATION_WALKING_DURATION,
            AnimationType.ABILITY1: gc.CRUSADER_CLERIC_ANIMATION_ATTACK_DURATION,
            AnimationType.DYING: gc.CRUSADER_CLERIC_ANIMATION_DYING_DURATION,
        },
        sprite_center_offset=(0, 2),
    ))
    esper.add_component(
        entity,
        StatsCard(
            text=[
                f"Name: Cleric",
                f"Faction: Crusader",
                f"Health: {gc.CRUSADER_CLERIC_HP}",
                f"Healing: {gc.CRUSADER_CLERIC_HEALING}",
                f"Healing DPS: {round(gc.CRUSADER_CLERIC_HEALING/gc.CRUSADER_CLERIC_ANIMATION_ATTACK_DURATION, 2)}",
                f"Speed: {gc.CRUSADER_CLERIC_MOVEMENT_SPEED}",
                f"Range: {gc.CRUSADER_CLERIC_ATTACK_RANGE}",
                f"AI: Walks towards the ally with the highest health, but heals the ally with the lowest current health in range. Ally must be under 90% health.",
            ]
        )
    )
    return entity

def create_crusader_commander(x: int, y: int, team: TeamType) -> int:
    """Create a commander entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CRUSADER_COMMANDER,
        movement_speed=gc.CRUSADER_COMMANDER_MOVEMENT_SPEED,
        health=gc.CRUSADER_COMMANDER_HP,
        hitbox=Hitbox(
            width=16,
            height=36,
        )
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=All([OnTeam(team=team.other()), Alive()])
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.CRUSADER_COMMANDER_ATTACK_RANGE*2/3)
    )
    esper.add_component(
        entity,
        Abilities(
            abilities=[
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CRUSADER_COMMANDER_ATTACK_RANGE,
                                    y_bias=5
                                ),
                            ])
                        )
                    ],
                    persistent_conditions=[
                        HasTarget(
                            unit_condition=All([
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CRUSADER_COMMANDER_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=5
                                ),
                            ])
                        )
                    ],
                    effects={4: [
                        Damages(damage=gc.CRUSADER_COMMANDER_ATTACK_DAMAGE, recipient=Recipient.TARGET),
                        PlaySound([
                            (SoundEffect(filename=f"sword_swoosh{i+1}.wav", volume=0.50), 1.0) for i in range(3)
                        ]),
                    ]},
                )
            ]
        )
    )
    esper.add_component(
        entity,
        Aura(
            owner=entity,
            radius=gc.CRUSADER_COMMANDER_AURA_RADIUS,
            effects=[
                AppliesStatusEffect(
                    status_effect=CrusaderCommanderEmpowered(time_remaining=gc.DEFAULT_AURA_PERIOD),
                    recipient=Recipient.TARGET
                )
            ],
            period=gc.DEFAULT_AURA_PERIOD,
            owner_condition=Alive(),
            unit_condition=All([
                NotEntity(entity=entity),
                OnTeam(team=team),
                Alive()
            ]),
            color=(255, 215, 0),
        )
    )
    esper.add_component(entity, SpriteSheet(
        surface=sprite_sheets[UnitType.CRUSADER_COMMANDER],
        frame_width=100,
        frame_height=100,
        scale=gc.TINY_RPG_SCALE,
        frames={AnimationType.IDLE: 6, AnimationType.WALKING: 8, AnimationType.ABILITY1: 7, AnimationType.DYING: 4},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 4, AnimationType.DYING: 8},
        animation_durations={
            AnimationType.IDLE: gc.CRUSADER_COMMANDER_ANIMATION_IDLE_DURATION,
            AnimationType.WALKING: gc.CRUSADER_COMMANDER_ANIMATION_WALKING_DURATION,
            AnimationType.ABILITY1: gc.CRUSADER_COMMANDER_ANIMATION_ATTACK_DURATION,
            AnimationType.DYING: gc.CRUSADER_COMMANDER_ANIMATION_DYING_DURATION,
        },
        sprite_center_offset=(0, 2),
    ))
    esper.add_component(
        entity,
        StatsCard(
            text=[
                f"Name: Commander",
                f"Faction: Crusader",
                f"Health: {gc.CRUSADER_COMMANDER_HP}",
                f"Attack: {gc.CRUSADER_COMMANDER_ATTACK_DAMAGE}",
                f"DPS: {round(gc.CRUSADER_COMMANDER_ATTACK_DAMAGE/gc.CRUSADER_COMMANDER_ANIMATION_ATTACK_DURATION, 2)}",
                f"Speed: {gc.CRUSADER_COMMANDER_MOVEMENT_SPEED}",
                f"Range: {gc.CRUSADER_COMMANDER_ATTACK_RANGE}",
                f"Special: Commanders have an aura which gives allied units {round(gc.CRUSADER_COMMANDER_EMPOWERED_DAMAGE_PERCENTAGE*100)}% increased damage (does not stack with itself).",
            ]
        )
    )
    return entity

def create_crusader_defender(x: int, y: int, team: TeamType) -> int:
    """Create a defender entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CRUSADER_DEFENDER,
        movement_speed=gc.CRUSADER_DEFENDER_MOVEMENT_SPEED,
        health=gc.CRUSADER_DEFENDER_HP,
        hitbox=Hitbox(
            width=16,
            height=32,
        )
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=All([OnTeam(team=team.other()), Alive()])
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.CRUSADER_DEFENDER_ATTACK_RANGE*2/3)
    )
    esper.add_component(
        entity,
        Abilities(
            abilities=[
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CRUSADER_DEFENDER_ATTACK_RANGE,
                                    y_bias=3
                                ),
                            ])
                        )
                    ],
                    persistent_conditions=[
                        HasTarget(
                            unit_condition=All([
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CRUSADER_DEFENDER_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=3
                                ),
                            ])
                        )
                    ],
                    effects={4: [
                        Damages(damage=gc.CRUSADER_DEFENDER_ATTACK_DAMAGE, recipient=Recipient.TARGET),
                        PlaySound([
                            (SoundEffect(filename=f"sword_swoosh{i+1}.wav", volume=0.50), 1.0) for i in range(3)
                        ]),
                    ]},
                )
            ]
        )
    )
    esper.add_component(entity, Armor(flat_reduction=gc.CRUSADER_DEFENDER_ARMOR_FLAT_REDUCTION, percent_reduction=gc.CRUSADER_DEFENDER_ARMOR_PERCENT_REDUCTION))
    esper.add_component(entity, SpriteSheet(
        surface=sprite_sheets[UnitType.CRUSADER_DEFENDER],
        frame_width=32,
        frame_height=32,
        scale=gc.MINIFOLKS_SCALE,
        frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ABILITY1: 6, AnimationType.DYING: 4},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 3, AnimationType.DYING: 6},
        animation_durations={
            AnimationType.IDLE: gc.CRUSADER_DEFENDER_ANIMATION_IDLE_DURATION,
            AnimationType.WALKING: gc.CRUSADER_DEFENDER_ANIMATION_WALKING_DURATION,
            AnimationType.ABILITY1: gc.CRUSADER_DEFENDER_ANIMATION_ATTACK_DURATION,
            AnimationType.DYING: gc.CRUSADER_DEFENDER_ANIMATION_DYING_DURATION,
        },
        sprite_center_offset=(0, -8),
    ))
    esper.add_component(
        entity,
        StatsCard(
            text=[
                f"Name: Defender",
                f"Faction: Crusader",
                f"Health: {gc.CRUSADER_DEFENDER_HP}",
                f"Attack: {gc.CRUSADER_DEFENDER_ATTACK_DAMAGE}",
                f"DPS: {round(gc.CRUSADER_DEFENDER_ATTACK_DAMAGE/gc.CRUSADER_DEFENDER_ANIMATION_ATTACK_DURATION, 2)}",
                f"Speed: {gc.CRUSADER_DEFENDER_MOVEMENT_SPEED}",
                f"Range: {gc.CRUSADER_DEFENDER_ATTACK_RANGE}",
                f"AI: Targets the nearest enemy, preferring units at the same height on the y-axis",
                f"Special: Defenders have {gc.CRUSADER_DEFENDER_ARMOR_FLAT_REDUCTION}% flat armor (applied first), followed by {round(gc.CRUSADER_DEFENDER_ARMOR_PERCENT_REDUCTION*100)}% percent armor, reducing damage taken by up to {round(gc.MAX_ARMOR_DAMAGE_REDUCTION*100)}%.",
            ]
        )
    )
    return entity

def create_crusader_gold_knight(x: int, y: int, team: TeamType) -> int:
    """Create a gold knight entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CRUSADER_GOLD_KNIGHT,
        movement_speed=gc.CRUSADER_GOLD_KNIGHT_MOVEMENT_SPEED,
        health=gc.CRUSADER_GOLD_KNIGHT_HP,
        hitbox=Hitbox(
            width=16,
            height=38,
        )
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=All([OnTeam(team=team.other()), Alive()])
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.CRUSADER_GOLD_KNIGHT_ATTACK_RANGE*2/3)
    )
    esper.add_component(
        entity,
        Abilities(
            abilities=[
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CRUSADER_GOLD_KNIGHT_ATTACK_RANGE,
                                    y_bias=3
                                ),
                            ])
                        )
                    ],
                    persistent_conditions=[],
                    effects={
                        0: [
                            CreatesAoE(
                                effects=[
                                    Damages(damage=gc.CRUSADER_GOLD_KNIGHT_ATTACK_DAMAGE, recipient=Recipient.TARGET),
                                    Heals(amount=gc.CRUSADER_GOLD_KNIGHT_ATTACK_HEAL, recipient=Recipient.OWNER)
                                ],
                                duration=gc.CRUSADER_GOLD_KNIGHT_ANIMATION_ATTACK_DURATION,
                                scale=gc.TINY_RPG_SCALE,
                                unit_condition=All([
                                    OnTeam(team=team.other()),
                                    Alive()
                                ]),
                                visual=Visual.CrusaderGoldKnightAttack,
                                location=Recipient.PARENT,
                            ),
                            PlaySound(SoundEffect(filename="deep_swoosh.wav", volume=0.50)),
                        ]
                    },
                )
            ]
        )
    )
    esper.add_component(entity, SpriteSheet(
        surface=sprite_sheets[UnitType.CRUSADER_GOLD_KNIGHT],
        frame_width=100,
        frame_height=100,
        scale=gc.TINY_RPG_SCALE,
        frames={AnimationType.IDLE: 6, AnimationType.WALKING: 8, AnimationType.ABILITY1: 4, AnimationType.DYING: 4},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 6, AnimationType.DYING: 5},
        animation_durations={
            AnimationType.IDLE: gc.CRUSADER_GOLD_KNIGHT_ANIMATION_IDLE_DURATION,
            AnimationType.WALKING: gc.CRUSADER_GOLD_KNIGHT_ANIMATION_WALKING_DURATION,
            AnimationType.ABILITY1: gc.CRUSADER_GOLD_KNIGHT_ANIMATION_ATTACK_DURATION,
            AnimationType.DYING: gc.CRUSADER_GOLD_KNIGHT_ANIMATION_DYING_DURATION,
        },
        sprite_center_offset=(0, 2),
    ))
    esper.add_component(
        entity,
        StatsCard(
            text=[
                f"Name: Gold Knight",
                f"Faction: Crusader",
                f"Health: {gc.CRUSADER_GOLD_KNIGHT_HP}",
                f"Attack: {gc.CRUSADER_GOLD_KNIGHT_ATTACK_DAMAGE}",
                f"DPS: {round(gc.CRUSADER_GOLD_KNIGHT_ATTACK_DAMAGE/gc.CRUSADER_GOLD_KNIGHT_ANIMATION_ATTACK_DURATION, 2)}",
                f"Speed: {gc.CRUSADER_GOLD_KNIGHT_MOVEMENT_SPEED}",
                f"Range: {gc.CRUSADER_GOLD_KNIGHT_ATTACK_RANGE}",
                f"AI: Targets the nearest enemy, preferring units at the same height on the y-axis",
                f"Special: Gold Knights hit all enemies in the radius of their attack, and heal for {gc.CRUSADER_GOLD_KNIGHT_ATTACK_HEAL} per enemy hit.",
            ]
        )
    )
    return entity

def create_crusader_longbowman(x: int, y: int, team: TeamType) -> int:
    """Create a longbowman entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CRUSADER_LONGBOWMAN,
        movement_speed=gc.CRUSADER_LONGBOWMAN_MOVEMENT_SPEED,
        health=gc.CRUSADER_LONGBOWMAN_HP,
        hitbox=Hitbox(
            width=16,
            height=36,
        )
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=All([OnTeam(team=team.other()), Alive()])
    )

    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=0)
    )
    esper.add_component(
        entity,
        RangeIndicator(range=gc.CRUSADER_LONGBOWMAN_ATTACK_RANGE)
    )
    esper.add_component(
        entity,
        Abilities(
            abilities=[
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CRUSADER_LONGBOWMAN_ATTACK_RANGE,
                                    y_bias=None
                                )
                            ])
                        )
                    ],
                    persistent_conditions=[
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CRUSADER_LONGBOWMAN_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=None
                                )
                            ])
                        )
                    ],
                    effects={6: [
                        CreatesProjectile(
                            projectile_speed=gc.CRUSADER_LONGBOWMAN_PROJECTILE_SPEED,
                            effects=[
                                Damages(damage=gc.CRUSADER_LONGBOWMAN_ATTACK_DAMAGE, recipient=Recipient.TARGET),
                            ],
                            visual=Visual.Arrow,
                            projectile_offset_x=5*gc.MINIFOLKS_SCALE,
                            projectile_offset_y=0
                        ),
                        PlaySound(SoundEffect(filename="arrow_fired_from_longbow.wav", volume=0.50)),
                    ]},
                )
            ]
        )
    )
    esper.add_component(
        entity,
        SpriteSheet(
            surface=sprite_sheets[UnitType.CRUSADER_LONGBOWMAN],
            frame_width=100,
            frame_height=100,
            scale=gc.TINY_RPG_SCALE,
            frames={AnimationType.IDLE: 6, AnimationType.WALKING: 7, AnimationType.ABILITY1: 8, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 2, AnimationType.DYING: 5},
            animation_durations={
                AnimationType.IDLE: gc.CRUSADER_LONGBOWMAN_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.CRUSADER_LONGBOWMAN_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: gc.CRUSADER_LONGBOWMAN_ANIMATION_ATTACK_DURATION,
                AnimationType.DYING: gc.CRUSADER_LONGBOWMAN_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(0, 2),
        )
    )
    esper.add_component(
        entity,
        StatsCard(
            text=[
                f"Name: Longbowman",
                f"Faction: Crusader",
                f"Health: {gc.CRUSADER_LONGBOWMAN_HP}",
                f"Attack: {gc.CRUSADER_LONGBOWMAN_ATTACK_DAMAGE}",
                f"DPS: {round(gc.CRUSADER_LONGBOWMAN_ATTACK_DAMAGE/gc.CRUSADER_LONGBOWMAN_ANIMATION_ATTACK_DURATION, 2)}",
                f"Speed: {gc.CRUSADER_LONGBOWMAN_MOVEMENT_SPEED}",
                f"Range: {gc.CRUSADER_LONGBOWMAN_ATTACK_RANGE}",
                f"AI: Targets the nearest enemy, preferring units at the same height on the y-axis",
            ]
        )
    )
    return entity

def create_crusader_paladin(x: int, y: int, team: TeamType) -> int:
    """Create a paladin entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CRUSADER_PALADIN,
        movement_speed=gc.CRUSADER_PALADIN_MOVEMENT_SPEED,
        health=gc.CRUSADER_PALADIN_HP,
        hitbox=Hitbox(
            width=50,
            height=54,
        )
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=All([OnTeam(team=team.other()), Alive()])
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.CRUSADER_PALADIN_ATTACK_RANGE*2/3)
    )
    esper.add_component(
        entity,
        Abilities(
            abilities=[
                Ability(
                    target_strategy=TargetStrategy(
                        rankings=[ByDistance(entity=entity, y_bias=2, ascending=True)],
                        unit_condition=Never(),
                    ),
                    trigger_conditions=[
                        Cooldown(duration=gc.CRUSADER_PALADIN_SKILL_COOLDOWN),
                        SatisfiesUnitCondition(unit_condition=HealthBelowPercent(percent=gc.CRUSADER_PALADIN_SKILL_HEALTH_PERCENT_THRESHOLD))
                    ],
                    persistent_conditions=[],
                    effects={
                        0: [
                            PlaySound(SoundEffect(filename="holy_healing_spell.wav", volume=0.50)),
                        ],
                        7: [
                            Heals(amount=gc.CRUSADER_PALADIN_SKILL_HEAL_PERCENT * gc.CRUSADER_PALADIN_HP, recipient=Recipient.OWNER),
                        ]
                    },
                ),
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CRUSADER_PALADIN_ATTACK_RANGE,
                                    y_bias=5
                                ),
                            ])
                        )
                    ],
                    persistent_conditions=[
                        HasTarget(
                            unit_condition=All([
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CRUSADER_PALADIN_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=5
                                ),
                            ])
                        )
                    ],
                    effects={3: [
                        Damages(damage=gc.CRUSADER_PALADIN_ATTACK_DAMAGE, recipient=Recipient.TARGET),
                        PlaySound([
                            (SoundEffect(filename=f"sword_swoosh{i+1}.wav", volume=0.50), 1.0) for i in range(3)
                        ]),
                    ]},
                )
            ]
        )
    )
    esper.add_component(
        entity,
        SpriteSheet(
            surface=sprite_sheets[UnitType.CRUSADER_PALADIN],
            frame_width=100,
            frame_height=100,
            scale=gc.TINY_RPG_SCALE,
            frames={AnimationType.IDLE: 6, AnimationType.WALKING: 8, AnimationType.ABILITY1: 13, AnimationType.ABILITY2: 6, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 7, AnimationType.ABILITY2: 3, AnimationType.DYING: 6},
            animation_durations={
                AnimationType.IDLE: gc.CRUSADER_PALADIN_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.CRUSADER_PALADIN_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: gc.CRUSADER_PALADIN_ANIMATION_SKILL_DURATION,
                AnimationType.ABILITY2: gc.CRUSADER_PALADIN_ANIMATION_ATTACK_DURATION,
                AnimationType.DYING: gc.CRUSADER_PALADIN_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(0, 7),
        )
    )
    esper.add_component(
        entity,
        StatsCard(
            text=[
                f"Name: Paladin",
                f"Faction: Crusader",
                f"Health: {gc.CRUSADER_PALADIN_HP}",
                f"Attack: {gc.CRUSADER_PALADIN_ATTACK_DAMAGE}",
                f"DPS: {round(gc.CRUSADER_PALADIN_ATTACK_DAMAGE/gc.CRUSADER_PALADIN_ANIMATION_ATTACK_DURATION, 2)}",
                f"Speed: {gc.CRUSADER_PALADIN_MOVEMENT_SPEED}",
                f"Range: {gc.CRUSADER_PALADIN_ATTACK_RANGE}",
                f"AI: Targets the nearest enemy, preferring units at the same height on the y-axis",
                f"Special: Heals self by {round(gc.CRUSADER_PALADIN_SKILL_HEAL_PERCENT*100)}% when their health is below {round(gc.CRUSADER_PALADIN_SKILL_HEALTH_PERCENT_THRESHOLD*100)}%, cooldown {gc.CRUSADER_PALADIN_SKILL_COOLDOWN}s. (Heal per second is at most {round(gc.CRUSADER_PALADIN_SKILL_HEAL_PERCENT * gc.CRUSADER_PALADIN_HP/gc.CRUSADER_PALADIN_SKILL_COOLDOWN, 2)} per second)",
            ]
        )
    )
    return entity

def create_crusader_pikeman(x: int, y: int, team: TeamType) -> int:
    """Create a pikeman entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CRUSADER_PIKEMAN,
        movement_speed=gc.CRUSADER_PIKEMAN_MOVEMENT_SPEED,
        health=gc.CRUSADER_PIKEMAN_HP,
        hitbox=Hitbox(
            width=16,
            height=32,
        )
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=All([OnTeam(team=team.other()), Alive()])
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.CRUSADER_PIKEMAN_ATTACK_RANGE*4/5)
    )
    esper.add_component(
        entity,
        Abilities(
            abilities=[
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CRUSADER_PIKEMAN_ATTACK_RANGE,
                                    y_bias=10
                                ),
                            ])
                        )
                    ],
                    persistent_conditions=[
                        HasTarget(
                            unit_condition=All([
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CRUSADER_PIKEMAN_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=10
                                ),
                            ])
                        )
                    ],
                    effects={3: [
                        Damages(damage=gc.CRUSADER_PIKEMAN_ATTACK_DAMAGE, recipient=Recipient.TARGET),
                        PlaySound([
                            (SoundEffect(filename=f"sword_swoosh{i+1}.wav", volume=0.50), 1.0) for i in range(3)
                        ]),
                    ]},
                )
            ]
        )
    )
    esper.add_component(
        entity,
        SpriteSheet(
            surface=sprite_sheets[UnitType.CRUSADER_PIKEMAN],
            frame_width=100,
            frame_height=68,
            scale=gc.MINIFOLKS_SCALE,
            frames={AnimationType.IDLE: 4, AnimationType.WALKING: 5, AnimationType.ABILITY1: 7, AnimationType.DYING: 7},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 2, AnimationType.DYING: 3},
            animation_durations={
                AnimationType.IDLE: gc.CRUSADER_PIKEMAN_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.CRUSADER_PIKEMAN_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: gc.CRUSADER_PIKEMAN_ANIMATION_ATTACK_DURATION,
                AnimationType.DYING: gc.CRUSADER_PIKEMAN_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(24, -16),
        )
    )
    esper.add_component(
        entity,
        StatsCard(
            text=[
                f"Name: Pikeman",
                f"Faction: Crusader",
                f"Health: {gc.CRUSADER_PIKEMAN_HP}",
                f"Attack: {gc.CRUSADER_PIKEMAN_ATTACK_DAMAGE}",
                f"DPS: {round(gc.CRUSADER_PIKEMAN_ATTACK_DAMAGE/gc.CRUSADER_PIKEMAN_ANIMATION_ATTACK_DURATION, 2)}",
                f"Speed: {gc.CRUSADER_PIKEMAN_MOVEMENT_SPEED}",
                f"Range: {gc.CRUSADER_PIKEMAN_ATTACK_RANGE}",
                f"AI: Targets the nearest enemy, preferring units at the same height on the y-axis",
            ]
        )
    )
    return entity

def create_crusader_red_knight(x: int, y: int, team: TeamType) -> int:
    """Create a red knight entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CRUSADER_RED_KNIGHT,
        movement_speed=gc.CRUSADER_RED_KNIGHT_MOVEMENT_SPEED,
        health=gc.CRUSADER_RED_KNIGHT_HP,
        hitbox=Hitbox(
            width=16,
            height=34,
        )
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=All([OnTeam(team=team.other()), Alive()])
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.CRUSADER_RED_KNIGHT_ATTACK_RANGE*2/3)
    )
    esper.add_component(
        entity,
        Abilities(
            abilities=[
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CRUSADER_RED_KNIGHT_SKILL_RANGE,
                                    y_bias=2
                                ),
                            ])
                        ),
                        Cooldown(duration=gc.CRUSADER_RED_KNIGHT_SKILL_COOLDOWN)
                    ],
                    persistent_conditions=[],
                    effects={7: [
                        CreatesAoE(
                            effects=[
                                Damages(damage=gc.CRUSADER_RED_KNIGHT_SKILL_DAMAGE, recipient=Recipient.TARGET),
                                AppliesStatusEffect(
                                    status_effect=Ignited(
                                        dps=gc.CRUSADER_RED_KNIGHT_SKILL_IGNITE_DAMAGE/gc.CRUSADER_RED_KNIGHT_SKILL_IGNITED_DURATION,
                                        time_remaining=gc.CRUSADER_RED_KNIGHT_SKILL_IGNITED_DURATION
                                    ),
                                    recipient=Recipient.TARGET
                                )
                            ],
                            visual=Visual.CrusaderRedKnightFireSlash,
                            duration=gc.CRUSADER_RED_KNIGHT_SKILL_AOE_DURATION,
                            scale=gc.CRUSADER_RED_KNIGHT_SKILL_AOE_SCALE,
                            unit_condition=All([
                                OnTeam(team=team.other()),
                                Alive()
                            ]),
                            location=Recipient.PARENT
                        )
                    ]},
                ),
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CRUSADER_RED_KNIGHT_ATTACK_RANGE,
                                    y_bias=3
                                )
                            ])
                        )
                    ],
                    persistent_conditions=[
                        HasTarget(
                            unit_condition=All([
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CRUSADER_RED_KNIGHT_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=3
                                )
                            ])
                        )
                    ],
                    effects={
                        3: [
                            Damages(damage=gc.CRUSADER_RED_KNIGHT_ATTACK_DAMAGE, recipient=Recipient.TARGET),
                            PlaySound([
                                (SoundEffect(filename=f"sword_swoosh{i+1}.wav", volume=0.50), 1.0) for i in range(3)
                            ]),
                        ],
                        7: [
                            Damages(damage=gc.CRUSADER_RED_KNIGHT_ATTACK_DAMAGE, recipient=Recipient.TARGET),
                            PlaySound([
                                (SoundEffect(filename=f"sword_swoosh{i+1}.wav", volume=0.50), 1.0) for i in range(3)
                            ]),
                        ]
                    },
                )
            ]
        )
    )
    esper.add_component(
        entity,
        SpriteSheet(
            surface=sprite_sheets[UnitType.CRUSADER_RED_KNIGHT],
            frame_width=100,
            frame_height=100,
            scale=gc.TINY_RPG_SCALE,
            frames={AnimationType.IDLE: 6, AnimationType.WALKING: 8, AnimationType.ABILITY1: 11, AnimationType.ABILITY2: 10, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 4, AnimationType.ABILITY2: 3, AnimationType.DYING: 7},
            animation_durations={
                AnimationType.IDLE: gc.CRUSADER_RED_KNIGHT_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.CRUSADER_RED_KNIGHT_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: gc.CRUSADER_RED_KNIGHT_ANIMATION_SKILL_DURATION,
                AnimationType.ABILITY2: gc.CRUSADER_RED_KNIGHT_ANIMATION_ATTACK_DURATION,
                AnimationType.DYING: gc.CRUSADER_RED_KNIGHT_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(0, 1),
        )
    )
    esper.add_component(
        entity,
        StatsCard(
            text=[
                f"Name: Red Knight",
                f"Faction: Crusader",
                f"Health: {gc.CRUSADER_RED_KNIGHT_HP}",
                f"Attack: {gc.CRUSADER_RED_KNIGHT_ATTACK_DAMAGE}",
                f"DPS: {round(gc.CRUSADER_RED_KNIGHT_ATTACK_DAMAGE/gc.CRUSADER_RED_KNIGHT_ANIMATION_ATTACK_DURATION, 2)}",
                f"Speed: {gc.CRUSADER_RED_KNIGHT_MOVEMENT_SPEED}",
                f"Range: {gc.CRUSADER_RED_KNIGHT_ATTACK_RANGE}",
                f"AI: Targets the nearest enemy, preferring units at the same height on the y-axis",
                f"Special: Creates an AoE of fire that hits enemies, dealing {gc.CRUSADER_RED_KNIGHT_SKILL_DAMAGE} damage and igniting for {gc.CRUSADER_RED_KNIGHT_SKILL_IGNITE_DAMAGE} over {gc.CRUSADER_RED_KNIGHT_SKILL_IGNITED_DURATION} seconds, cooldown {gc.CRUSADER_RED_KNIGHT_SKILL_COOLDOWN}s.",
            ]
        )
    )
    return entity

def create_werebear(x: int, y: int, team: TeamType) -> int:
    """Create a werebear entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.WEREBEAR,
        movement_speed=gc.WEREBEAR_MOVEMENT_SPEED,
        health=gc.WEREBEAR_HP,
        hitbox=Hitbox(
            width=24,
            height=40,
        )
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=All([OnTeam(team=team.other()), Alive()])
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.WEREBEAR_ATTACK_RANGE*2/3)
    )
    esper.add_component(
        entity,
        Abilities(
            abilities=[
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.WEREBEAR_ATTACK_RANGE,
                                    y_bias=3
                                ),
                            ])
                        )
                    ],
                    persistent_conditions=[
                        HasTarget(
                            unit_condition=All([
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.WEREBEAR_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=3
                                ),
                            ])
                        )
                    ],
                    effects={5: [Damages(damage=gc.WEREBEAR_ATTACK_DAMAGE, recipient=Recipient.TARGET)]},
                )
            ]
        )
    )
    esper.add_component(
        entity,
        SpriteSheet(
            surface=sprite_sheets[UnitType.WEREBEAR],
            frame_width=100,
            frame_height=100,
            scale=gc.TINY_RPG_SCALE,
            frames={AnimationType.IDLE: 6, AnimationType.WALKING: 7, AnimationType.ABILITY1: 8, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 2, AnimationType.DYING: 6},
            animation_durations={
                AnimationType.IDLE: gc.WEREBEAR_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.WEREBEAR_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: gc.WEREBEAR_ANIMATION_ATTACK_DURATION,
                AnimationType.DYING: gc.WEREBEAR_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(-2, 1),
        )
    )
    esper.add_component(
        entity,
        StatsCard(
            text=[
                f"Name: Werebear",
                f"Faction: Cursed Forest",
                f"Health: {gc.WEREBEAR_HP}",
                f"Attack: {gc.WEREBEAR_ATTACK_DAMAGE}",
                f"DPS: {round(gc.WEREBEAR_ATTACK_DAMAGE/gc.WEREBEAR_ANIMATION_ATTACK_DURATION, 2)}",
                f"Speed: {gc.WEREBEAR_MOVEMENT_SPEED}",
                f"Range: {gc.WEREBEAR_ATTACK_RANGE}",
                f"AI: Targets the nearest enemy, preferring units at the same height on the y-axis",
            ]
        )
    )
    return entity
