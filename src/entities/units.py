"""Unit creation module for Battle Swap.

This module contains functions for creating different types of units with their corresponding components.
"""

import math
import esper
import pygame
import os
from typing import Dict
from CONSTANTS import *
from components.ability import Abilities, Ability, Cooldown, HasTarget, SatisfiesUnitCondition
from components.armor import Armor
from components.aura import Aura
from components.position import Position
from components.animation import AnimationState, AnimationType
from components.sprite_sheet import SpriteSheet
from components.status_effect import CrusaderBlackKnightDebuffed, CrusaderGoldKnightEmpowered, Ignited, StatusEffects
from target_strategy import ByDistance, ByMaxHealth, ByMissingHealth, Ranking, TargetStrategy
from components.destination import Destination
from components.team import Team, TeamType
from components.unit_state import UnitState
from components.movement import Movement
from components.unit_type import UnitType, UnitTypeComponent
from components.velocity import Velocity
from components.health import Health
from components.orientation import Orientation, FacingDirection
from effects import AppliesStatusEffect, CreatesAoE, CreatesAttachedVisual, CreatesProjectile, Damages, Heals, Recipient
from unit_condition import (
    All, Alive, HealthBelowPercent, MinimumDistanceFromEntity, Never, NotEntity, OnTeam,
    MaximumDistanceFromEntity, MaximumAngleFromEntity
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
    return entity

def create_core_archer(x: int, y: int, team: TeamType) -> int:
    """Create an archer entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CORE_ARCHER,
        movement_speed=CORE_ARCHER_MOVEMENT_SPEED,
        health=CORE_ARCHER_HP,
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
                                    distance=CORE_ARCHER_ATTACK_RANGE,
                                    y_bias=2
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
                                    distance=CORE_ARCHER_ATTACK_RANGE + TARGETTING_GRACE_DISTANCE,
                                    y_bias=2
                                )
                            ])
                        )
                    ],
                    effects={
                        7: [
                            CreatesProjectile(
                                projectile_speed=CORE_ARCHER_PROJECTILE_SPEED,
                                effects=[Damages(damage=CORE_ARCHER_ATTACK_DAMAGE, recipient=Recipient.TARGET)],
                                visual=Visual.Arrow,
                                projectile_offset_x=5*MINIFOLKS_SCALE,
                                projectile_offset_y=0,
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
        scale=MINIFOLKS_SCALE,
        frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ABILITY1: 11, AnimationType.DYING: 4},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 3, AnimationType.DYING: 6},
        animation_durations=CORE_ARCHER_ANIMATION_DURATIONS,
        sprite_center_offset=(0, -8),
    ))
    return entity

def create_core_duelist(x: int, y: int, team: TeamType) -> int:
    """Create a fancy swordsman entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CORE_DUELIST,
        movement_speed=CORE_DUELIST_MOVEMENT_SPEED,
        health=CORE_DUELIST_HP,
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=All([OnTeam(team=team.other()), Alive()])
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=CORE_DUELIST_ATTACK_RANGE*2/3)
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
                                    distance=CORE_DUELIST_ATTACK_RANGE,
                                    y_bias=2
                                ),
                                MaximumAngleFromEntity(
                                    entity=entity,
                                    maximum_angle=math.pi/16
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
                                    distance=CORE_DUELIST_ATTACK_RANGE + TARGETTING_GRACE_DISTANCE,
                                    y_bias=2
                                ),
                                MaximumAngleFromEntity(
                                    entity=entity,
                                    maximum_angle=math.pi/12
                                )
                            ])
                        )
                    ],
                    effects={
                        5: [Damages(damage=CORE_DUELIST_ATTACK_DAMAGE/7, recipient=Recipient.TARGET)],
                        6: [Damages(damage=CORE_DUELIST_ATTACK_DAMAGE/7, recipient=Recipient.TARGET)],
                        7: [Damages(damage=CORE_DUELIST_ATTACK_DAMAGE/7, recipient=Recipient.TARGET)],
                        8: [Damages(damage=CORE_DUELIST_ATTACK_DAMAGE/7, recipient=Recipient.TARGET)],
                        9: [Damages(damage=CORE_DUELIST_ATTACK_DAMAGE/7, recipient=Recipient.TARGET)],
                        10: [Damages(damage=CORE_DUELIST_ATTACK_DAMAGE/7, recipient=Recipient.TARGET)],
                        11: [Damages(damage=CORE_DUELIST_ATTACK_DAMAGE/7, recipient=Recipient.TARGET)],
                    },
                )
            ]
        )
    )
    esper.add_component(entity, SpriteSheet(
        surface=sprite_sheets[UnitType.CORE_DUELIST],
        frame_width=100,
        frame_height=100,
        scale=TINY_RPG_SCALE,
        frames={AnimationType.IDLE: 4, AnimationType.WALKING: 8, AnimationType.ABILITY1: 12, AnimationType.DYING: 4},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 4, AnimationType.DYING: 6},
        animation_durations=CORE_DUELIST_ANIMATION_DURATIONS,
        sprite_center_offset=(0, 0),
    ))
    return entity

def create_core_horseman(x: int, y: int, team: TeamType) -> int:
    """Create a horseman entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CORE_HORSEMAN,
        movement_speed=CORE_HORSEMAN_MOVEMENT_SPEED,
        health=CORE_HORSEMAN_HP,
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=All([OnTeam(team=team.other()), Alive()])
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=CORE_HORSEMAN_ATTACK_RANGE*2/3)
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
                                    distance=CORE_HORSEMAN_ATTACK_RANGE,
                                    y_bias=2
                                ),
                                MaximumAngleFromEntity(
                                    entity=entity,
                                    maximum_angle=math.pi/12
                                )
                            ])
                        )
                    ],
                    persistent_conditions=[
                        HasTarget(
                            unit_condition=All([
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=CORE_HORSEMAN_ATTACK_RANGE + TARGETTING_GRACE_DISTANCE,
                                    y_bias=2
                                ),
                                MaximumAngleFromEntity(
                                    entity=entity,
                                    maximum_angle=math.pi/12
                                )
                            ])
                        )
                    ],
                    effects={3: [Damages(damage=CORE_HORSEMAN_ATTACK_DAMAGE, recipient=Recipient.TARGET)]},
                )
            ]
        )
    )
    esper.add_component(entity, SpriteSheet(
        surface=sprite_sheets[UnitType.CORE_HORSEMAN],
        frame_width=32,
        frame_height=32,
        scale=MINIFOLKS_SCALE,
        frames={AnimationType.IDLE: 8, AnimationType.WALKING: 6, AnimationType.ABILITY1: 7, AnimationType.DYING: 6},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 4, AnimationType.DYING: 6},
        animation_durations=CORE_HORSEMAN_ANIMATION_DURATIONS,
        sprite_center_offset=(0, -8),
    ))
    return entity

def create_core_mage(x: int, y: int, team: TeamType) -> int:
    """Create a mage entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CORE_MAGE,
        movement_speed=CORE_MAGE_MOVEMENT_SPEED,
        health=CORE_MAGE_HP,
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
                                    distance=CORE_MAGE_ATTACK_RANGE,
                                    y_bias=2
                                )
                            ])
                        )
                    ],
                    persistent_conditions=[
                        HasTarget(
                            unit_condition=All([
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=CORE_MAGE_ATTACK_RANGE + TARGETTING_GRACE_DISTANCE,
                                    y_bias=2
                                )
                            ])
                        )
                    ],
                    effects={
                        7: [
                            CreatesProjectile(
                                projectile_speed=CORE_MAGE_PROJECTILE_SPEED,
                                effects=[
                                    CreatesAoE(
                                        effects=[
                                            Damages(damage=CORE_MAGE_ATTACK_DAMAGE, recipient=Recipient.TARGET),
                                            AppliesStatusEffect(
                                                status_effect=Ignited(
                                                    dps=CORE_MAGE_IGNITE_DAMAGE/CORE_MAGE_IGNITE_DURATION,
                                                    duration=CORE_MAGE_IGNITE_DURATION
                                                ),
                                                recipient=Recipient.TARGET
                                            ),
                                        ],
                                        visual=Visual.Explosion,
                                        duration=CORE_MAGE_FIREBALL_AOE_DURATION,
                                        scale=CORE_MAGE_FIREBALL_AOE_SCALE,
                                        unit_condition=Alive(),
                                    )
                                ],
                                visual=Visual.Fireball,
                                projectile_offset_x=11*MINIFOLKS_SCALE,
                                projectile_offset_y=-4*MINIFOLKS_SCALE,
                            )
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
        scale=MINIFOLKS_SCALE,
        frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ABILITY1: 11, AnimationType.DYING: 9},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 3, AnimationType.DYING: 7},
        animation_durations=CORE_MAGE_ANIMATION_DURATIONS,
        sprite_center_offset=(0, -8),
    ))
    return entity

def create_core_swordsman(x: int, y: int, team: TeamType) -> int:
    """Create a swordsman entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CORE_SWORDSMAN,
        movement_speed=CORE_SWORDSMAN_MOVEMENT_SPEED,
        health=CORE_SWORDSMAN_HP,
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=All([OnTeam(team=team.other()), Alive()])
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=CORE_SWORDSMAN_ATTACK_RANGE*2/3)
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
                                    distance=CORE_SWORDSMAN_ATTACK_RANGE,
                                    y_bias=2
                                ),
                                MaximumAngleFromEntity(
                                    entity=entity,
                                    maximum_angle=math.pi/12
                                )
                            ])
                        )
                    ],
                    persistent_conditions=[
                        HasTarget(
                            unit_condition=All([
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=CORE_SWORDSMAN_ATTACK_RANGE + TARGETTING_GRACE_DISTANCE,
                                    y_bias=2
                                ),
                                MaximumAngleFromEntity(
                                    entity=entity,
                                    maximum_angle=math.pi/12
                                )
                            ])
                        )
                    ],
                    effects={2: [Damages(damage=CORE_SWORDSMAN_ATTACK_DAMAGE, recipient=Recipient.TARGET)]},
                )
            ]
        )
    )
    esper.add_component(entity, SpriteSheet(
        surface=sprite_sheets[UnitType.CORE_SWORDSMAN],
        frame_width=32,
        frame_height=32,
        scale=MINIFOLKS_SCALE,
        frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ABILITY1: 6, AnimationType.DYING: 4},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 3, AnimationType.DYING: 5},
        animation_durations=CORE_SWORDSMAN_ANIMATION_DURATIONS,
        sprite_center_offset=(0, -8),
    ))
    return entity

def create_crusader_black_knight(x: int, y: int, team: TeamType) -> int:
    """Create a black knight entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CRUSADER_BLACK_KNIGHT,
        movement_speed=CRUSADER_BLACK_KNIGHT_MOVEMENT_SPEED,
        health=CRUSADER_BLACK_KNIGHT_HP,
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=All([OnTeam(team=team.other()), Alive()])
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=CRUSADER_BLACK_KNIGHT_ATTACK_RANGE*2/3)
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
                                    distance=CRUSADER_BLACK_KNIGHT_ATTACK_RANGE,
                                    y_bias=2
                                ),
                                MaximumAngleFromEntity(
                                    entity=entity,
                                    maximum_angle=math.pi/12
                                )
                            ])
                        )
                    ],
                    persistent_conditions=[
                        HasTarget(
                            unit_condition=All([
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=CRUSADER_BLACK_KNIGHT_ATTACK_RANGE + TARGETTING_GRACE_DISTANCE,
                                    y_bias=2
                                ),
                                MaximumAngleFromEntity(
                                    entity=entity,
                                    maximum_angle=math.pi/12
                                )
                            ])
                        )
                    ],
                    effects={2: [Damages(damage=CRUSADER_BLACK_KNIGHT_ATTACK_DAMAGE, recipient=Recipient.TARGET)]},
                )
            ]
        )
    )
    esper.add_component(entity, Armor(flat_reduction=CRUSADER_BLACK_KNIGHT_ARMOR_FLAT_REDUCTION, percent_reduction=CRUSADER_BLACK_KNIGHT_ARMOR_PERCENT_REDUCTION))
    esper.add_component(
        entity,
        Aura(
            radius=CRUSADER_BLACK_KNIGHT_AURA_RADIUS,
            effects=[
                AppliesStatusEffect(
                    status_effect=CrusaderBlackKnightDebuffed(duration=DEFAULT_AURA_PERIOD),
                    recipient=Recipient.TARGET
                )
            ],
            color=(150, 0, 0),
            period=DEFAULT_AURA_PERIOD,
            unit_condition=All([
                OnTeam(team=team.other()),
                Alive()
            ])
        )
    )
    esper.add_component(entity, SpriteSheet(
        surface=sprite_sheets[UnitType.CRUSADER_BLACK_KNIGHT],
        frame_width=100,
        frame_height=100,
        scale=TINY_RPG_SCALE,
        frames={AnimationType.IDLE: 6, AnimationType.WALKING: 8, AnimationType.ABILITY1: 6, AnimationType.DYING: 4},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 3, AnimationType.DYING: 6},
        animation_durations=CRUSADER_BLACK_KNIGHT_ANIMATION_DURATIONS,
        sprite_center_offset=(0, 0),
    ))
    return entity

def create_crusader_cleric(x: int, y: int, team: TeamType) -> int:
    """Create a cleric entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CRUSADER_CLERIC,
        movement_speed=CRUSADER_CLERIC_MOVEMENT_SPEED,
        health=CRUSADER_CLERIC_HP,
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
                        MinimumDistanceFromEntity(entity=entity, distance=CRUSADER_CLERIC_ATTACK_RANGE*2/3, y_bias=None)
                    ]
                )
            ),
            x_offset=0
        )
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
                                    distance=CRUSADER_CLERIC_ATTACK_RANGE,
                                    y_bias=2
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
                                    distance=CRUSADER_CLERIC_ATTACK_RANGE + TARGETTING_GRACE_DISTANCE,
                                    y_bias=2
                                )
                            ])
                        )
                    ],
                    effects={
                        2: [
                            Heals(amount=CRUSADER_CLERIC_HEALING, recipient=Recipient.TARGET),
                            CreatesAttachedVisual(
                                visual=Visual.Healing,
                                animation_duration=1,
                                expiration_duration=1,
                                scale=1
                            )
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
        scale=TINY_RPG_SCALE,
        frames={AnimationType.IDLE: 6, AnimationType.WALKING: 8, AnimationType.ABILITY1: 6, AnimationType.DYING: 4},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 4, AnimationType.DYING: 7},
        animation_durations=CRUSADER_CLERIC_ANIMATION_DURATIONS,
        sprite_center_offset=(0, 0),
    ))
    return entity

def create_crusader_commander(x: int, y: int, team: TeamType) -> int:
    """Create a commander entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CRUSADER_COMMANDER,
        movement_speed=CRUSADER_COMMANDER_MOVEMENT_SPEED,
        health=CRUSADER_COMMANDER_HP,
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=All([OnTeam(team=team.other()), Alive()])
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=CRUSADER_COMMANDER_ATTACK_RANGE*2/3)
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
                                    distance=CRUSADER_COMMANDER_ATTACK_RANGE,
                                    y_bias=2
                                ),
                                MaximumAngleFromEntity(
                                    entity=entity,
                                    maximum_angle=math.pi/12
                                )
                            ])
                        )
                    ],
                    persistent_conditions=[
                        HasTarget(
                            unit_condition=All([
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=CRUSADER_COMMANDER_ATTACK_RANGE + TARGETTING_GRACE_DISTANCE,
                                    y_bias=2
                                ),
                                MaximumAngleFromEntity(
                                    entity=entity,
                                    maximum_angle=math.pi/12
                                )
                            ])
                        )
                    ],
                    effects={4: [Damages(damage=CRUSADER_COMMANDER_ATTACK_DAMAGE, recipient=Recipient.TARGET)]},
                )
            ]
        )
    )
    esper.add_component(entity, Armor(flat_reduction=CRUSADER_COMMANDER_ARMOR_FLAT_REDUCTION, percent_reduction=CRUSADER_COMMANDER_ARMOR_PERCENT_REDUCTION))
    esper.add_component(entity, SpriteSheet(
        surface=sprite_sheets[UnitType.CRUSADER_COMMANDER],
        frame_width=100,
        frame_height=100,
        scale=TINY_RPG_SCALE,
        frames={AnimationType.IDLE: 6, AnimationType.WALKING: 8, AnimationType.ABILITY1: 7, AnimationType.DYING: 4},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 4, AnimationType.DYING: 8},
        animation_durations=CRUSADER_COMMANDER_ANIMATION_DURATIONS,
        sprite_center_offset=(0, 0),
    ))
    return entity

def create_crusader_defender(x: int, y: int, team: TeamType) -> int:
    """Create a defender entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CRUSADER_DEFENDER,
        movement_speed=CRUSADER_DEFENDER_MOVEMENT_SPEED,
        health=CRUSADER_DEFENDER_HP,
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=All([OnTeam(team=team.other()), Alive()])
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=CRUSADER_DEFENDER_ATTACK_RANGE*2/3)
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
                                    distance=CRUSADER_DEFENDER_ATTACK_RANGE,
                                    y_bias=2
                                ),
                                MaximumAngleFromEntity(
                                    entity=entity,
                                    maximum_angle=math.pi/12
                                )
                            ])
                        )
                    ],
                    persistent_conditions=[
                        HasTarget(
                            unit_condition=All([
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=CRUSADER_DEFENDER_ATTACK_RANGE + TARGETTING_GRACE_DISTANCE,
                                    y_bias=2
                                ),
                                MaximumAngleFromEntity(
                                    entity=entity,
                                    maximum_angle=math.pi/12
                                )
                            ])
                        )
                    ],
                    effects={4: [Damages(damage=CRUSADER_DEFENDER_ATTACK_DAMAGE, recipient=Recipient.TARGET)]},
                )
            ]
        )
    )
    esper.add_component(entity, Armor(flat_reduction=CRUSADER_DEFENDER_ARMOR_FLAT_REDUCTION, percent_reduction=CRUSADER_DEFENDER_ARMOR_PERCENT_REDUCTION))
    esper.add_component(entity, SpriteSheet(
        surface=sprite_sheets[UnitType.CRUSADER_DEFENDER],
        frame_width=32,
        frame_height=32,
        scale=MINIFOLKS_SCALE,
        frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ABILITY1: 6, AnimationType.DYING: 4},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 3, AnimationType.DYING: 6},
        animation_durations=CRUSADER_DEFENDER_ANIMATION_DURATIONS,
        sprite_center_offset=(0, -8),
    ))
    return entity

def create_crusader_gold_knight(x: int, y: int, team: TeamType) -> int:
    """Create a gold knight entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CRUSADER_GOLD_KNIGHT,
        movement_speed=CRUSADER_GOLD_KNIGHT_MOVEMENT_SPEED,
        health=CRUSADER_GOLD_KNIGHT_HP,
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=All([OnTeam(team=team.other()), Alive()])
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=CRUSADER_GOLD_KNIGHT_ATTACK_RANGE*2/3)
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
                                    distance=CRUSADER_GOLD_KNIGHT_ATTACK_RANGE,
                                    y_bias=2
                                ),
                                MaximumAngleFromEntity(
                                    entity=entity,
                                    maximum_angle=math.pi/12
                                )
                            ])
                        )
                    ],
                    persistent_conditions=[
                        HasTarget(
                            unit_condition=All([
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=CRUSADER_GOLD_KNIGHT_ATTACK_RANGE + TARGETTING_GRACE_DISTANCE,
                                    y_bias=2
                                ),
                                MaximumAngleFromEntity(
                                    entity=entity,
                                    maximum_angle=math.pi/12
                                )
                            ])
                        )
                    ],
                    effects={4: [Damages(damage=CRUSADER_GOLD_KNIGHT_ATTACK_DAMAGE, recipient=Recipient.TARGET)]},
                )
            ]
        )
    )
    esper.add_component(entity, Armor(flat_reduction=CRUSADER_GOLD_KNIGHT_ARMOR_FLAT_REDUCTION, percent_reduction=CRUSADER_GOLD_KNIGHT_ARMOR_PERCENT_REDUCTION))
    esper.add_component(
        entity,
        Aura(
            radius=CRUSADER_GOLD_KNIGHT_AURA_RADIUS,
            effects=[
                AppliesStatusEffect(
                    status_effect=CrusaderGoldKnightEmpowered(duration=DEFAULT_AURA_PERIOD),
                    recipient=Recipient.TARGET
                )
            ],
            period=DEFAULT_AURA_PERIOD,
            unit_condition=All([
                NotEntity(entity=entity),
                OnTeam(team=team),
                Alive()
            ]),
            color=(255, 215, 0)
        )
    )
    esper.add_component(entity, SpriteSheet(
        surface=sprite_sheets[UnitType.CRUSADER_GOLD_KNIGHT],
        frame_width=100,
        frame_height=100,
        scale=TINY_RPG_SCALE,
        frames={AnimationType.IDLE: 6, AnimationType.WALKING: 8, AnimationType.ABILITY1: 9, AnimationType.DYING: 4},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 2, AnimationType.DYING: 5},
        animation_durations=CRUSADER_GOLD_KNIGHT_ANIMATION_DURATIONS,
        sprite_center_offset=(0, 0),
    ))
    return entity

def create_crusader_longbowman(x: int, y: int, team: TeamType) -> int:
    """Create a longbowman entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CRUSADER_LONGBOWMAN,
        movement_speed=CRUSADER_LONGBOWMAN_MOVEMENT_SPEED,
        health=CRUSADER_LONGBOWMAN_HP,
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
                                    distance=CRUSADER_LONGBOWMAN_ATTACK_RANGE,
                                    y_bias=2
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
                                    distance=CRUSADER_LONGBOWMAN_ATTACK_RANGE + TARGETTING_GRACE_DISTANCE,
                                    y_bias=2
                                )
                            ])
                        )
                    ],
                    effects={6: [
                        CreatesProjectile(
                            projectile_speed=CRUSADER_LONGBOWMAN_PROJECTILE_SPEED,
                            effects=[Damages(damage=CRUSADER_LONGBOWMAN_ATTACK_DAMAGE, recipient=Recipient.TARGET)],
                            visual=Visual.Arrow,
                            projectile_offset_x=5*MINIFOLKS_SCALE,
                            projectile_offset_y=0
                        )
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
            scale=TINY_RPG_SCALE,
            frames={AnimationType.IDLE: 6, AnimationType.WALKING: 7, AnimationType.ABILITY1: 8, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 2, AnimationType.DYING: 5},
            animation_durations=CRUSADER_LONGBOWMAN_ANIMATION_DURATIONS,
            sprite_center_offset=(0, 0),
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
        movement_speed=CRUSADER_PALADIN_MOVEMENT_SPEED,
        health=CRUSADER_PALADIN_HP,
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=All([OnTeam(team=team.other()), Alive()])
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=CRUSADER_PALADIN_ATTACK_RANGE*2/3)
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
                        Cooldown(duration=CRUSADER_PALADIN_SKILL_COOLDOWN),
                        SatisfiesUnitCondition(unit_condition=HealthBelowPercent(percent=CRUSADER_PALADIN_SKILL_HEALTH_PERCENT_THRESHOLD))
                    ],
                    persistent_conditions=[],
                    effects={7: [Heals(amount=CRUSADER_PALADIN_SKILL_HEAL_PERCENT * CRUSADER_PALADIN_HP, recipient=Recipient.OWNER)]},
                ),
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=CRUSADER_PALADIN_ATTACK_RANGE,
                                    y_bias=2
                                ),
                                MaximumAngleFromEntity(
                                    entity=entity,
                                    maximum_angle=math.pi/12
                                )
                            ])
                        )
                    ],
                    persistent_conditions=[
                        HasTarget(
                            unit_condition=All([
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=CRUSADER_PALADIN_ATTACK_RANGE + TARGETTING_GRACE_DISTANCE,
                                    y_bias=2
                                ),
                                MaximumAngleFromEntity(
                                    entity=entity,
                                    maximum_angle=math.pi/12
                                )
                            ])
                        )
                    ],
                    effects={3: [Damages(damage=CRUSADER_PALADIN_ATTACK_DAMAGE, recipient=Recipient.TARGET)]},
                )
            ]
        )
    )
    esper.add_component(entity, Armor(flat_reduction=CRUSADER_PALADIN_ARMOR_FLAT_REDUCTION, percent_reduction=CRUSADER_PALADIN_ARMOR_PERCENT_REDUCTION))
    esper.add_component(
        entity,
        SpriteSheet(
            surface=sprite_sheets[UnitType.CRUSADER_PALADIN],
            frame_width=100,
            frame_height=100,
            scale=TINY_RPG_SCALE,
            frames={AnimationType.IDLE: 6, AnimationType.WALKING: 8, AnimationType.ABILITY1: 13, AnimationType.ABILITY2: 6, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 7, AnimationType.ABILITY2: 3, AnimationType.DYING: 6},
            animation_durations=CRUSADER_PALADIN_ANIMATION_DURATIONS,
            sprite_center_offset=(0, 0),
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
        movement_speed=CRUSADER_PIKEMAN_MOVEMENT_SPEED,
        health=CRUSADER_PIKEMAN_HP,
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=All([OnTeam(team=team.other()), Alive()])
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=CRUSADER_PIKEMAN_ATTACK_RANGE*4/5)
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
                                    distance=CRUSADER_PIKEMAN_ATTACK_RANGE,
                                    y_bias=2
                                ),
                                MaximumAngleFromEntity(
                                    entity=entity,
                                    maximum_angle=math.pi/16
                                )
                            ])
                        )
                    ],
                    persistent_conditions=[
                        HasTarget(
                            unit_condition=All([
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=CRUSADER_PIKEMAN_ATTACK_RANGE + TARGETTING_GRACE_DISTANCE,
                                    y_bias=2
                                ),
                                MaximumAngleFromEntity(
                                    entity=entity,
                                    maximum_angle=math.pi/12
                                )
                            ])
                        )
                    ],
                    effects={3: [Damages(damage=CRUSADER_PIKEMAN_ATTACK_DAMAGE, recipient=Recipient.TARGET)]},
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
            scale=MINIFOLKS_SCALE,
            frames={AnimationType.IDLE: 4, AnimationType.WALKING: 5, AnimationType.ABILITY1: 7, AnimationType.DYING: 7},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 2, AnimationType.DYING: 3},
            animation_durations=CRUSADER_PIKEMAN_ANIMATION_DURATIONS,
            sprite_center_offset=(24, -16),
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
        movement_speed=CRUSADER_RED_KNIGHT_MOVEMENT_SPEED,
        health=CRUSADER_RED_KNIGHT_HP,
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=All([OnTeam(team=team.other()), Alive()])
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=CRUSADER_RED_KNIGHT_ATTACK_RANGE*2/3)
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
                                    distance=CRUSADER_RED_KNIGHT_SKILL_RANGE,
                                    y_bias=2
                                ),
                                MaximumAngleFromEntity(
                                    entity=entity,
                                    maximum_angle=math.pi/3
                                )
                            ])
                        ),
                        Cooldown(duration=CRUSADER_RED_KNIGHT_SKILL_COOLDOWN)
                    ],
                    persistent_conditions=[],
                    effects={7: [
                        CreatesAoE(
                            effects=[
                                Damages(damage=CRUSADER_RED_KNIGHT_SKILL_DAMAGE, recipient=Recipient.TARGET),
                                AppliesStatusEffect(
                                    status_effect=Ignited(
                                        dps=CRUSADER_RED_KNIGHT_SKILL_IGNITE_DAMAGE/CRUSADER_RED_KNIGHT_SKILL_IGNITED_DURATION,
                                        duration=CRUSADER_RED_KNIGHT_SKILL_IGNITED_DURATION
                                    ),
                                    recipient=Recipient.TARGET
                                )
                            ],
                            visual=Visual.CrusaderRedKnightFireSlash,
                            duration=CRUSADER_RED_KNIGHT_SKILL_AOE_DURATION,
                            scale=CRUSADER_RED_KNIGHT_SKILL_AOE_SCALE,
                            unit_condition=All([
                                NotEntity(entity=entity),
                                Alive()
                            ])
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
                                    distance=CRUSADER_RED_KNIGHT_ATTACK_RANGE,
                                    y_bias=2
                                )
                            ])
                        )
                    ],
                    persistent_conditions=[
                        HasTarget(
                            unit_condition=All([
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=CRUSADER_RED_KNIGHT_ATTACK_RANGE + TARGETTING_GRACE_DISTANCE,
                                    y_bias=2
                                )
                            ])
                        )
                    ],
                    effects={
                        3: [Damages(damage=CRUSADER_RED_KNIGHT_ATTACK_DAMAGE, recipient=Recipient.TARGET)],
                        7: [Damages(damage=CRUSADER_RED_KNIGHT_ATTACK_DAMAGE, recipient=Recipient.TARGET)]
                    },
                )
            ]
        )
    )
    esper.add_component(entity, Armor(flat_reduction=CRUSADER_RED_KNIGHT_ARMOR_FLAT_REDUCTION, percent_reduction=CRUSADER_RED_KNIGHT_ARMOR_PERCENT_REDUCTION))
    esper.add_component(
        entity,
        SpriteSheet(
            surface=sprite_sheets[UnitType.CRUSADER_RED_KNIGHT],
            frame_width=100,
            frame_height=100,
            scale=TINY_RPG_SCALE,
            frames={AnimationType.IDLE: 6, AnimationType.WALKING: 8, AnimationType.ABILITY1: 11, AnimationType.ABILITY2: 10, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 4, AnimationType.ABILITY2: 3, AnimationType.DYING: 7},
            animation_durations=CRUSADER_RED_KNIGHT_ANIMATION_DURATIONS,
            sprite_center_offset=(0, 0),
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
        movement_speed=WEREBEAR_MOVEMENT_SPEED,
        health=WEREBEAR_HP,
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=All([OnTeam(team=team.other()), Alive()])
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=WEREBEAR_ATTACK_RANGE*2/3)
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
                                    distance=WEREBEAR_ATTACK_RANGE,
                                    y_bias=2
                                ),
                                MaximumAngleFromEntity(
                                    entity=entity,
                                    maximum_angle=math.pi/12
                                )
                            ])
                        )
                    ],
                    persistent_conditions=[
                        HasTarget(
                            unit_condition=All([
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=WEREBEAR_ATTACK_RANGE + TARGETTING_GRACE_DISTANCE,
                                    y_bias=2
                                ),
                                MaximumAngleFromEntity(
                                    entity=entity,
                                    maximum_angle=math.pi/12
                                )
                            ])
                        )
                    ],
                    effects={5: [Damages(damage=WEREBEAR_ATTACK_DAMAGE, recipient=Recipient.TARGET)]},
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
            scale=TINY_RPG_SCALE,
            frames={AnimationType.IDLE: 6, AnimationType.WALKING: 7, AnimationType.ABILITY1: 8, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 2, AnimationType.DYING: 6},
            animation_durations=WEREBEAR_ANIMATION_DURATIONS,
            sprite_center_offset=(0, 0),
        )
    )
    return entity
