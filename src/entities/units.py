"""Unit creation module for Battle Swap.

This module contains functions for creating different types of units with their corresponding components.
"""

from enum import Enum
import esper
import pygame
import os
from typing import Dict, List
from components.ammo import Ammo
from components.attached import Attached
from components.entity_memory import EntityMemory
from components.hitbox import Hitbox
from components.immunity import ImmuneToZombieInfection
from components.instant_ability import InstantAbilities, InstantAbility
from components.no_nudge import NoNudge
from components.range_indicator import RangeIndicator
from components.stance import Stance
from components.walk_effects import WalkEffects
from game_constants import gc
from components.ability import Abilities, Ability, Cooldown, HasTarget, SatisfiesUnitCondition
from components.armor import Armor
from components.aura import Aura
from components.position import Position
from components.animation import AnimationState, AnimationType
from components.sprite_sheet import SpriteSheet
from components.status_effect import CrusaderBannerBearerEmpowered, Fleeing, Healing, DamageOverTime, StatusEffects, ZombieInfection
from target_strategy import ByCurrentHealth, ByDistance, ByMaxHealth, ByMissingHealth, ConditionPenalty, TargetStrategy, WeightedRanking
from components.destination import Destination
from components.team import Team, TeamType
from components.unit_state import State, UnitState
from components.movement import Movement
from components.unit_type import UnitType, UnitTypeComponent
from components.velocity import Velocity
from components.health import Health
from components.orientation import Orientation, FacingDirection
from effects import AppliesStatusEffect, AttachToTarget, CreatesAoE, CreatesAttachedVisual, CreatesLobbed, CreatesProjectile, Damages, Forget, Heals, IncreaseAmmo, Jump, PlaySound, Recipient, SoundEffect, StanceChange, RememberTarget
from unit_condition import (
    All, Alive, Always, AmmoEquals, Any, Grounded, HasComponent, HealthBelowPercent, InStance, Infected, IsEntity, IsUnitType, MaximumDistanceFromDestination, MinimumDistanceFromEntity, Never, Not, OnTeam,
    MaximumDistanceFromEntity, RememberedBy, RememberedSatisfies
)
from visuals import Visual

unit_theme_ids: Dict[UnitType, str] = {
    UnitType.CORE_ARCHER: "#core_archer_icon", 
    UnitType.CORE_BARBARIAN: "#core_barbarian_icon",
    UnitType.CORE_CAVALRY: "#core_cavalry_icon",
    UnitType.CORE_DUELIST: "#core_duelist_icon",
    UnitType.CORE_SWORDSMAN: "#core_swordsman_icon",
    UnitType.CORE_WIZARD: "#core_wizard_icon",
    UnitType.CRUSADER_BLACK_KNIGHT: "#crusader_black_knight_icon",
    UnitType.CRUSADER_BANNER_BEARER: "#crusader_banner_bearer_icon",
    UnitType.CRUSADER_CATAPULT: "#crusader_catapult_icon",
    UnitType.CRUSADER_CLERIC: "#crusader_cleric_icon",
    UnitType.CRUSADER_COMMANDER: "#crusader_commander_icon",
    UnitType.CRUSADER_CROSSBOWMAN: "#crusader_crossbowman_icon",
    UnitType.CRUSADER_DEFENDER: "#crusader_defender_icon",
    UnitType.CRUSADER_GOLD_KNIGHT: "#crusader_gold_knight_icon",
    UnitType.CRUSADER_GUARDIAN_ANGEL: "#crusader_guardian_angel_icon",
    UnitType.CRUSADER_LONGBOWMAN: "#crusader_longbowman_icon",
    UnitType.CRUSADER_PALADIN: "#crusader_paladin_icon",
    UnitType.CRUSADER_PIKEMAN: "#crusader_pikeman_icon",
    UnitType.CRUSADER_RED_KNIGHT: "#crusader_red_knight_icon",
    UnitType.CRUSADER_SOLDIER: "#crusader_soldier_icon",
    UnitType.WEREBEAR: "#werebear_icon",
    UnitType.ZOMBIE_BASIC_ZOMBIE: "#zombie_basic_zombie_icon",
    UnitType.ZOMBIE_JUMPER: "#zombie_jumper_icon",
    UnitType.ZOMBIE_SPITTER: "#zombie_spitter_icon",
    UnitType.ZOMBIE_TANK: "#zombie_tank_icon",
}

unit_icon_surfaces: Dict[UnitType, pygame.Surface] = {}

sprite_sheets: Dict[UnitType, pygame.Surface] = {}

class Faction(Enum):
    CORE = 0
    CRUSADERS = 1
    ZOMBIES = 2
    MISC = 3
    
    @staticmethod
    def faction_of(unit_type: UnitType) -> "Faction":
        return _unit_to_faction[unit_type]

    @staticmethod
    def units(faction: "Faction") -> List[UnitType]:
        return [unit_type for unit_type, faction_value in _unit_to_faction.items() if faction_value == faction]

_unit_to_faction = {
    UnitType.CORE_ARCHER: Faction.CORE,
    UnitType.CORE_BARBARIAN: Faction.CORE,
    UnitType.CORE_CAVALRY: Faction.CORE,
    UnitType.CORE_DUELIST: Faction.CORE,
    UnitType.CORE_SWORDSMAN: Faction.CORE,
    UnitType.CORE_WIZARD: Faction.CORE,
    UnitType.CRUSADER_BANNER_BEARER: Faction.CRUSADERS,
    UnitType.CRUSADER_BLACK_KNIGHT: Faction.CRUSADERS,
    UnitType.CRUSADER_CATAPULT: Faction.CRUSADERS,
    UnitType.CRUSADER_CLERIC: Faction.CRUSADERS,
    UnitType.CRUSADER_COMMANDER: Faction.CRUSADERS,
    UnitType.CRUSADER_CROSSBOWMAN: Faction.CRUSADERS,
    UnitType.CRUSADER_DEFENDER: Faction.CRUSADERS,
    UnitType.CRUSADER_GOLD_KNIGHT: Faction.CRUSADERS,
    UnitType.CRUSADER_GUARDIAN_ANGEL: Faction.CRUSADERS,
    UnitType.CRUSADER_LONGBOWMAN: Faction.CRUSADERS,
    UnitType.CRUSADER_PALADIN: Faction.CRUSADERS,
    UnitType.CRUSADER_PIKEMAN: Faction.CRUSADERS,
    UnitType.CRUSADER_RED_KNIGHT: Faction.CRUSADERS,
    UnitType.CRUSADER_SOLDIER: Faction.CRUSADERS,
    UnitType.ZOMBIE_BASIC_ZOMBIE: Faction.ZOMBIES,
    UnitType.ZOMBIE_JUMPER: Faction.ZOMBIES,
    UnitType.ZOMBIE_SPITTER: Faction.ZOMBIES,
    UnitType.ZOMBIE_TANK: Faction.ZOMBIES,
    UnitType.WEREBEAR: Faction.MISC,
}

def load_sprite_sheets():
    """Load all sprite sheets and unit icons."""
    unit_filenames = {
        UnitType.CORE_ARCHER: "CoreArcher.png", 
        UnitType.CORE_BARBARIAN: "CoreBarbarian.png",
        UnitType.CORE_CAVALRY: "CoreCavalry.png",
        UnitType.CORE_DUELIST: "CoreDuelist.png",
        UnitType.CORE_SWORDSMAN: "CoreSwordsman.png", 
        UnitType.CORE_WIZARD: "CoreWizard.png",
        UnitType.CRUSADER_BANNER_BEARER: "Kirby.png",
        UnitType.CRUSADER_BLACK_KNIGHT: "CrusaderBlackKnight.png",
        UnitType.CRUSADER_CATAPULT: "kirby_library/ReKirby_01.png",
        UnitType.CRUSADER_CLERIC: "CrusaderCleric.png",
        UnitType.CRUSADER_COMMANDER: "CrusaderCommander.png",
        UnitType.CRUSADER_CROSSBOWMAN: "CrusaderCrossbowman.png",
        UnitType.CRUSADER_DEFENDER: "CrusaderDefender.png",
        UnitType.CRUSADER_GOLD_KNIGHT: "CrusaderGoldKnight.png",
        UnitType.CRUSADER_GUARDIAN_ANGEL: "CrusaderGuardianAngel.png",
        UnitType.CRUSADER_LONGBOWMAN: "CrusaderLongbowman.png",
        UnitType.CRUSADER_PALADIN: "CrusaderPaladin.png",
        UnitType.CRUSADER_PIKEMAN: "CrusaderPikeman.png",
        UnitType.CRUSADER_RED_KNIGHT: "CrusaderRedKnight.png",
        UnitType.CRUSADER_SOLDIER: "CrusaderSoldier.png",
        UnitType.WEREBEAR: "Werebear.png",
        UnitType.ZOMBIE_BASIC_ZOMBIE: "ZombieBasicZombie.png",
        UnitType.ZOMBIE_JUMPER: "ZombieBasicZombie.png",
        UnitType.ZOMBIE_SPITTER: "ZombieBasicZombie.png",
        UnitType.ZOMBIE_TANK: "ZombieBasicZombie.png",
    }
    for unit_type, filename in unit_filenames.items():
        if unit_type in sprite_sheets:
            continue
        path = os.path.join("assets", "units", filename)
        sprite_sheets[unit_type] = pygame.image.load(path).convert_alpha()

    # Load unit icons
    unit_icon_paths: Dict[UnitType, str] = {
        UnitType.CORE_ARCHER: "CoreArcherIcon.png",
        UnitType.CORE_BARBARIAN: "CoreBarbarianIcon.png",
        UnitType.CORE_CAVALRY: "CoreCavalryIcon.png",
        UnitType.CORE_DUELIST: "CoreDuelistIcon.png",
        UnitType.CORE_SWORDSMAN: "CoreSwordsmanIcon.png",
        UnitType.CORE_WIZARD: "CoreWizardIcon.png",
        UnitType.CRUSADER_BANNER_BEARER: "CrusaderBannerBearerIcon.png",
        UnitType.CRUSADER_BLACK_KNIGHT: "CrusaderBlackKnightIcon.png",
        UnitType.CRUSADER_CATAPULT: "CrusaderCatapultIcon.png",
        UnitType.CRUSADER_CLERIC: "CrusaderClericIcon.png",
        UnitType.CRUSADER_COMMANDER: "CrusaderCommanderIcon.png",
        UnitType.CRUSADER_CROSSBOWMAN: "CrusaderCrossbowmanIcon.png",
        UnitType.CRUSADER_DEFENDER: "CrusaderDefenderIcon.png",
        UnitType.CRUSADER_GOLD_KNIGHT: "CrusaderGoldKnightIcon.png",
        UnitType.CRUSADER_GUARDIAN_ANGEL: "CrusaderGuardianAngelIcon.png",
        UnitType.CRUSADER_LONGBOWMAN: "CrusaderLongbowmanIcon.png",
        UnitType.CRUSADER_PALADIN: "CrusaderPaladinIcon.png",
        UnitType.CRUSADER_PIKEMAN: "CrusaderPikemanIcon.png",
        UnitType.CRUSADER_RED_KNIGHT: "CrusaderRedKnightIcon.png",
        UnitType.CRUSADER_SOLDIER: "CrusaderSoldierIcon.png",
        UnitType.WEREBEAR: "WerebearIcon.png",
        UnitType.ZOMBIE_BASIC_ZOMBIE: "ZombieBasicZombieIcon.png",
        UnitType.ZOMBIE_JUMPER: "ZombieBasicZombieIcon.png",
        UnitType.ZOMBIE_SPITTER: "ZombieSpitterIcon.png",
        UnitType.ZOMBIE_TANK: "ZombieTankIcon.png",
    }
    for unit_type, filename in unit_icon_paths.items():
        if unit_type in unit_icon_surfaces:
            continue
        path = os.path.join("assets", "icons", filename)
        unit_icon_surfaces[unit_type] = pygame.image.load(path).convert_alpha()

def create_unit(x: int, y: int, unit_type: UnitType, team: TeamType) -> int:
    """Create a unit entity with all necessary components."""
    return {
        UnitType.CORE_ARCHER: create_core_archer,
        UnitType.CORE_BARBARIAN: create_core_barbarian,
        UnitType.CORE_CAVALRY: create_core_cavalry,
        UnitType.CORE_DUELIST: create_core_duelist,
        UnitType.CORE_SWORDSMAN: create_core_swordsman,
        UnitType.CORE_WIZARD: create_core_wizard,
        UnitType.CRUSADER_BANNER_BEARER: create_crusader_banner_bearer,
        UnitType.CRUSADER_BLACK_KNIGHT: create_crusader_black_knight,
        UnitType.CRUSADER_CATAPULT: create_crusader_catapult,
        UnitType.CRUSADER_CLERIC: create_crusader_cleric,
        UnitType.CRUSADER_COMMANDER: create_crusader_commander,
        UnitType.CRUSADER_CROSSBOWMAN: create_crusader_crossbowman,
        UnitType.CRUSADER_DEFENDER: create_crusader_defender,
        UnitType.CRUSADER_GOLD_KNIGHT: create_crusader_gold_knight,
        UnitType.CRUSADER_GUARDIAN_ANGEL: create_crusader_guardian_angel,
        UnitType.CRUSADER_LONGBOWMAN: create_crusader_longbowman,
        UnitType.CRUSADER_PALADIN: create_crusader_paladin,
        UnitType.CRUSADER_PIKEMAN: create_crusader_pikeman,
        UnitType.CRUSADER_RED_KNIGHT: create_crusader_red_knight,
        UnitType.CRUSADER_SOLDIER: create_crusader_soldier,
        UnitType.WEREBEAR: create_werebear,
        UnitType.ZOMBIE_BASIC_ZOMBIE: create_zombie_basic_zombie,
        UnitType.ZOMBIE_JUMPER: create_zombie_jumper,
        UnitType.ZOMBIE_SPITTER: create_zombie_spitter,
        UnitType.ZOMBIE_TANK: create_zombie_tank,
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
    esper.add_component(entity, RangeIndicator(ranges=[gc.CORE_ARCHER_ATTACK_RANGE]))
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
                                Grounded(),
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
                                Grounded(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CORE_ARCHER_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=None
                                )
                            ])
                        )
                    ],
                    effects={
                        4: [
                            PlaySound(
                                sound_effects=[
                                    (SoundEffect(filename="bow_loading.wav", volume=0.25), 1.0),
                                ]
                            )
                        ],
                        7: [
                            CreatesProjectile(
                                projectile_speed=gc.CORE_ARCHER_PROJECTILE_SPEED,
                                effects=[
                                    Damages(damage=gc.CORE_ARCHER_ATTACK_DAMAGE, recipient=Recipient.TARGET),
                                ],
                                visual=Visual.Arrow,
                                projectile_offset_x=5*gc.MINIFOLKS_SCALE,
                                projectile_offset_y=0,
                                unit_condition=All([OnTeam(team=team.other()), Alive(), Grounded()]),
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
    esper.add_component(entity, WalkEffects({
        frame: [PlaySound(sound_effects=[
            (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
        ])]
        for frame in [1, 4]
    }))
    return entity

def create_core_barbarian(x: int, y: int, team: TeamType) -> int:
    """Create a barbarian entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CORE_BARBARIAN,
        movement_speed=gc.CORE_BARBARIAN_MOVEMENT_SPEED,
        health=gc.CORE_BARBARIAN_HP,
        hitbox=Hitbox(
            width=20,
            height=38,
        )
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=4, ascending=True),
        ],
        unit_condition=All([OnTeam(team=team.other()), Alive()])
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.CORE_BARBARIAN_ATTACK_RANGE*2/3)
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
                                Grounded(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CORE_BARBARIAN_ATTACK_RANGE,
                                    y_bias=2
                                ),
                            ])
                        )
                    ],
                    persistent_conditions=[],
                    effects={
                        6: [
                            CreatesAoE(
                                effects=[
                                    Damages(damage=gc.CORE_BARBARIAN_ATTACK_DAMAGE, recipient=Recipient.TARGET),
                                ],
                                duration=gc.CORE_BARBARIAN_ANIMATION_ATTACK_DURATION*4/12,
                                scale=gc.TINY_RPG_SCALE,
                                unit_condition=All([
                                    OnTeam(team=team.other()),
                                    Alive(),
                                    Grounded(),
                                ]),
                                visual=Visual.CoreBarbarianAttack,
                                location=Recipient.PARENT,
                            ),
                            PlaySound(SoundEffect(filename="deep_swoosh.wav", volume=0.70)),
                        ]
                    },
                )
            ]
        )
    )
    esper.add_component(entity, SpriteSheet(
        surface=sprite_sheets[UnitType.CORE_BARBARIAN],
        frame_width=100,
        frame_height=100,
        scale=gc.TINY_RPG_SCALE,
        frames={AnimationType.IDLE: 6, AnimationType.WALKING: 9, AnimationType.ABILITY1: 12, AnimationType.DYING: 4},
        rows={AnimationType.IDLE: 1, AnimationType.WALKING: 4, AnimationType.ABILITY1: 10, AnimationType.DYING: 19},
        animation_durations={
            AnimationType.IDLE: gc.CORE_BARBARIAN_ANIMATION_IDLE_DURATION,
            AnimationType.WALKING: gc.CORE_BARBARIAN_ANIMATION_WALKING_DURATION,
            AnimationType.ABILITY1: gc.CORE_BARBARIAN_ANIMATION_ATTACK_DURATION,
            AnimationType.DYING: gc.CORE_BARBARIAN_ANIMATION_DYING_DURATION,
        },
        sprite_center_offset=(-2, 2),
    ))
    esper.add_component(entity, WalkEffects({
        frame: [PlaySound(sound_effects=[
            (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
        ])]
        for frame in [2, 5]
    }))
    return entity

def create_core_cavalry(x: int, y: int, team: TeamType) -> int:
    """Create a cavalry entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CORE_CAVALRY,
        movement_speed=gc.CORE_CAVALRY_MOVEMENT_SPEED,
        health=gc.  CORE_CAVALRY_HP,
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
        Destination(target_strategy=targetting_strategy, x_offset=gc.CORE_CAVALRY_ATTACK_RANGE*2/3)
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
                                Grounded(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CORE_CAVALRY_ATTACK_RANGE,
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
                                    distance=gc.CORE_CAVALRY_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=5
                                ),
                            ])
                        )
                    ],
                    effects={3: [
                        Damages(damage=gc.CORE_CAVALRY_ATTACK_DAMAGE, recipient=Recipient.TARGET),
                        PlaySound([
                            (SoundEffect(filename=f"sword_swoosh{i+1}.wav", volume=0.50), 1.0) for i in range(3)
                        ]),
                    ]},
                )
            ]
        )
    )
    esper.add_component(entity, SpriteSheet(
        surface=sprite_sheets[UnitType.CORE_CAVALRY],
        frame_width=32,
        frame_height=32,
        scale=gc.MINIFOLKS_SCALE,
        frames={AnimationType.IDLE: 8, AnimationType.WALKING: 6, AnimationType.ABILITY1: 7, AnimationType.DYING: 6},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 4, AnimationType.DYING: 6},
        animation_durations={
            AnimationType.IDLE: gc.CORE_CAVALRY_ANIMATION_IDLE_DURATION,
            AnimationType.WALKING: gc.CORE_CAVALRY_ANIMATION_WALKING_DURATION,
            AnimationType.ABILITY1: gc.CORE_CAVALRY_ANIMATION_ATTACK_DURATION,
            AnimationType.DYING: gc.CORE_CAVALRY_ANIMATION_DYING_DURATION,
        },
        sprite_center_offset=(1, -6),
    ))
    esper.add_component(entity, WalkEffects({
        frame: [PlaySound(sound_effects=[
            (SoundEffect(filename=f"horse_footsteps_grass{i+1}.wav", volume=0.15), 1.0) for i in range(4)
        ])]
        for frame in [2]
    }))
    return entity

def create_core_duelist(x: int, y: int, team: TeamType) -> int:
    """Create a duelist entity with all necessary components."""
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
        Destination(target_strategy=targetting_strategy, x_offset=gc.CORE_DUELIST_ATTACK_RANGE*7/8)
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
                                Grounded(),
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
                                Grounded(),
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
    esper.add_component(entity, WalkEffects({
        frame: [PlaySound(sound_effects=[
            (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
        ])]
        for frame in [3, 7]
    }))
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
                                Grounded(),
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
                    effects={
                        2: [
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
    esper.add_component(entity, WalkEffects({
        frame: [PlaySound(sound_effects=[
            (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
        ])]
        for frame in [2, 5]
    }))
    return entity

def create_core_wizard(x: int, y: int, team: TeamType) -> int:
    """Create a wizard entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CORE_WIZARD,
        movement_speed=gc.CORE_WIZARD_MOVEMENT_SPEED,
        health=gc.CORE_WIZARD_HP,
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
    esper.add_component(entity, RangeIndicator(ranges=[gc.CORE_WIZARD_ATTACK_RANGE]))
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
                                Grounded(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CORE_WIZARD_ATTACK_RANGE,
                                    y_bias=None
                                )
                            ])
                        )
                    ],
                    persistent_conditions=[
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                Grounded(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CORE_WIZARD_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
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
                                projectile_speed=gc.CORE_WIZARD_PROJECTILE_SPEED,
                                effects=[
                                    CreatesAoE(
                                        effects=[
                                            Damages(damage=gc.CORE_WIZARD_ATTACK_DAMAGE, recipient=Recipient.TARGET),
                                        ],
                                        visual=Visual.Explosion,
                                        duration=gc.CORE_WIZARD_FIREBALL_AOE_DURATION,
                                        scale=gc.CORE_WIZARD_FIREBALL_AOE_SCALE,
                                        unit_condition=All([Alive(), Grounded()]),
                                        location=Recipient.PARENT,
                                    ),
                                    PlaySound(SoundEffect(filename="fireball_impact.wav", volume=0.50)),
                                ],
                                visual=Visual.Fireball,
                                projectile_offset_x=11*gc.MINIFOLKS_SCALE,
                                projectile_offset_y=-4*gc.MINIFOLKS_SCALE,
                                unit_condition=All([OnTeam(team=team.other()), Alive(), Grounded()]),
                            ),
                        ]
                    }
                )
            ]
        )
    )
    esper.add_component(entity, SpriteSheet(
        surface=sprite_sheets[UnitType.CORE_WIZARD],
        frame_width=32,
        frame_height=32,
        scale=gc.MINIFOLKS_SCALE,
        frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ABILITY1: 11, AnimationType.DYING: 9},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 3, AnimationType.DYING: 7},
        animation_durations={
            AnimationType.IDLE: gc.CORE_WIZARD_ANIMATION_IDLE_DURATION,
            AnimationType.WALKING: gc.CORE_WIZARD_ANIMATION_WALKING_DURATION,
            AnimationType.ABILITY1: gc.CORE_WIZARD_ANIMATION_ATTACK_DURATION,
            AnimationType.DYING: gc.CORE_WIZARD_ANIMATION_DYING_DURATION,
        },
        sprite_center_offset=(0, -8),
    ))
    esper.add_component(entity, WalkEffects({
        frame: [PlaySound(sound_effects=[
            (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
        ])]
        for frame in [1, 4]
    }))
    return entity

def create_crusader_banner_bearer(x: int, y: int, team: TeamType) -> int:
    """Create a banner bearer entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CRUSADER_BANNER_BEARER,
        movement_speed=gc.CRUSADER_BANNER_BEARER_MOVEMENT_SPEED,
        health=gc.CRUSADER_BANNER_BEARER_HP,
        hitbox=Hitbox(
            width=16,
            height=36,
        )
    )
    find_target_to_follow = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=None, ascending=True),
        ],
        unit_condition=All(
            [
                Not(
                    Any(
                        [
                            IsUnitType(unit_type=UnitType.CRUSADER_BANNER_BEARER),
                            IsUnitType(unit_type=UnitType.CRUSADER_GUARDIAN_ANGEL),
                        ]
                    ),
                ),
                OnTeam(team=team),
                Alive()
            ]
        )
    )
    follow_target = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=None, ascending=True),
        ],
        unit_condition=All(
            [
                RememberedBy(entity=entity),
                Alive(),
                OnTeam(team=team),
            ]
        )
    )
    esper.add_component(
        entity,
        Destination(
            target_strategy=follow_target,
            x_offset=gc.CRUSADER_BANNER_BEARER_AURA_RADIUS/2,
            use_team_x_offset=True,
            min_distance=1
        )
    )
    esper.add_component(
        entity,
        InstantAbilities(
            abilities=[
                InstantAbility(
                    target_strategy=find_target_to_follow,
                    trigger_conditions=[
                        HasTarget(
                            unit_condition=Always()
                        ),
                        SatisfiesUnitCondition(
                            Not(
                                RememberedSatisfies(
                                    condition=All(
                                        [
                                            Alive(),
                                            OnTeam(team=team),
                                        ]
                                    )
                                )
                            )
                        )
                    ],
                    effects=[
                        RememberTarget(),
                    ]
                )
            ]
        )
    )
    esper.add_component(
        entity,
        Aura(
            owner=entity,
            radius=gc.CRUSADER_BANNER_BEARER_AURA_RADIUS,
            effects=[
                AppliesStatusEffect(
                    status_effect=CrusaderBannerBearerEmpowered(time_remaining=gc.DEFAULT_AURA_PERIOD),
                    recipient=Recipient.TARGET
                )
            ],
            period=gc.DEFAULT_AURA_PERIOD,
            owner_condition=Alive(),
            unit_condition=All([
                Not(IsEntity(entity=entity)),
                OnTeam(team=team),
                Alive()
            ]),
            color=(255, 215, 0),
        )
    )
    esper.add_component(entity, SpriteSheet(
        surface=sprite_sheets[UnitType.CRUSADER_BANNER_BEARER],
        frame_width=100,
        frame_height=100,
        scale=gc.TINY_RPG_SCALE,
        frames={AnimationType.IDLE: 6, AnimationType.WALKING: 8, AnimationType.DYING: 3},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.DYING: 4},
        animation_durations={
            AnimationType.IDLE: gc.CRUSADER_BANNER_BEARER_ANIMATION_IDLE_DURATION,
            AnimationType.WALKING: gc.CRUSADER_BANNER_BEARER_ANIMATION_WALKING_DURATION,
            AnimationType.DYING: gc.CRUSADER_BANNER_BEARER_ANIMATION_DYING_DURATION,
        },
        sprite_center_offset=(0, 10),
    ))
    esper.add_component(entity, WalkEffects({
        frame: [PlaySound(sound_effects=[
            (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
        ])]
        for frame in [3, 7]
    }))
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
            WeightedRanking(
                rankings={
                    ByDistance(entity=entity, y_bias=None, ascending=True): 1,
                    ByCurrentHealth(ascending=False): -0.6,
                },
            ),
        ],
        unit_condition=All([OnTeam(team=team.other()), Alive()])
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.CRUSADER_BLACK_KNIGHT_ATTACK_RANGE*2/3)
    )
    esper.add_component(entity, Armor(flat_reduction=gc.ARMOR_FLAT_DAMAGE_REDUCTION, percent_reduction=gc.ARMOR_PERCENT_DAMAGE_REDUCTION))
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
                                Grounded(),
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
                                            on_death=lambda e: esper.delete_entity(e),
                                            unique_key=lambda e: f"FLEE {e}",
                                            offset=lambda e: (0, -esper.component_for_entity(e, Hitbox).height/2),
                                            layer=1
                                        )
                                    ],
                                    duration=gc.CRUSADER_BLACK_KNIGHT_FEAR_AOE_DURATION,
                                    scale=gc.CRUSADER_BLACK_KNIGHT_FEAR_AOE_SCALE,
                                    unit_condition=All([Alive(), Grounded(), Not(IsEntity(entity=entity))]),
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
    esper.add_component(entity, WalkEffects({
        frame: [PlaySound(sound_effects=[
            (SoundEffect(filename=f"horse_footsteps_grass{i+1}.wav", volume=0.15), 1.0) for i in range(4)
        ])]
        for frame in [3]
    }))
    return entity

def create_crusader_catapult(x: int, y: int, team: TeamType) -> int:
    """Create a catapult entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CRUSADER_CATAPULT,
        movement_speed=0,
        health=gc.CRUSADER_CATAPULT_HP,
        hitbox=Hitbox(
            width=16,
            height=36,
        )
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=All(
            [
                OnTeam(team=team.other()),
                Alive(),
                Grounded(),
                MaximumDistanceFromEntity(
                    entity=entity,
                    distance=gc.CRUSADER_CATAPULT_MAXIMUM_RANGE,
                    y_bias=None
                ),
                MinimumDistanceFromEntity(
                    entity=entity,
                    distance=gc.CRUSADER_CATAPULT_MINIMUM_RANGE,
                    y_bias=None
                )
            ]
        )
    )
    esper.add_component(entity, Destination(target_strategy=targetting_strategy, x_offset=0))
    esper.add_component(entity, RangeIndicator(ranges=[gc.CRUSADER_CATAPULT_MINIMUM_RANGE, gc.CRUSADER_CATAPULT_MAXIMUM_RANGE]))
    esper.add_component(
        entity,
        Abilities(
            abilities=[
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        HasTarget(unit_condition=Always())
                    ],
                    persistent_conditions=[
                        HasTarget(unit_condition=All([Alive(), Grounded()]))
                    ],
                    effects={
                        2: [
                            CreatesLobbed(
                                effects=[
                                    CreatesAoE(
                                        effects=[
                                            Damages(damage=gc.CRUSADER_CATAPULT_DAMAGE, recipient=Recipient.TARGET)
                                        ],
                                        visual=Visual.Explosion,
                                        duration=gc.CORE_WIZARD_FIREBALL_AOE_DURATION,
                                        scale=gc.CORE_WIZARD_FIREBALL_AOE_SCALE,
                                        unit_condition=All([Alive(), Grounded()]),
                                        location=Recipient.PARENT,
                                    )
                                ],
                                max_range=gc.CRUSADER_CATAPULT_MAXIMUM_RANGE,
                                min_range=gc.CRUSADER_CATAPULT_MINIMUM_RANGE,
                                visual=Visual.Fireball,
                                offset=(30, 0),
                            )
                        ]
                    }
                )
            ]
        )
    )
    esper.add_component(entity, SpriteSheet(
        surface=sprite_sheets[UnitType.CRUSADER_CATAPULT],
        frame_width=100,
        frame_height=100,
        scale=gc.TINY_RPG_SCALE,
        frames={AnimationType.IDLE: 6, 
                AnimationType.WALKING: 6, # Just for fleeing
                AnimationType.ABILITY1: 5, 
                AnimationType.DYING: 3},
        rows={AnimationType.IDLE: 0, 
               AnimationType.WALKING: 0,
               AnimationType.ABILITY1: 5, 
               AnimationType.DYING: 7},
        animation_durations={
            AnimationType.IDLE: gc.CRUSADER_CATAPULT_ANIMATION_IDLE_DURATION,
            AnimationType.WALKING: gc.CRUSADER_CATAPULT_ANIMATION_IDLE_DURATION,
            AnimationType.ABILITY1: gc.CRUSADER_CATAPULT_ANIMATION_ATTACK_DURATION,
            AnimationType.DYING: gc.CRUSADER_CATAPULT_ANIMATION_DYING_DURATION,
        },
        sprite_center_offset=(2, 9),
    ))
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
    targetting_strategy = TargetStrategy(
        rankings=[
            WeightedRanking(
                rankings={
                    ByDistance(entity=entity, y_bias=None, ascending=True): 1,
                    ByMissingHealth(ascending=False): 0.6,
                },
                unit_condition=All([OnTeam(team=team), Alive(), Not(IsEntity(entity=entity)), HealthBelowPercent(percent=1)])
            ),
            ByDistance(entity=entity, y_bias=None, ascending=True),
        ],
        unit_condition=All([OnTeam(team=team), Alive(), Not(IsEntity(entity=entity))])
    )
    esper.add_component(
        entity,
        Destination(
            target_strategy=targetting_strategy,
            x_offset=0,
            min_distance=gc.CRUSADER_CLERIC_ATTACK_RANGE*2/3
        )
    )
    esper.add_component(
        entity,
        RangeIndicator(ranges=[gc.CRUSADER_CLERIC_ATTACK_RANGE])
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
                                    distance=gc.CRUSADER_CLERIC_ATTACK_RANGE,
                                    y_bias=None
                                ),
                                HealthBelowPercent(percent=1),
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
                            Heals(amount=gc.CRUSADER_CLERIC_HEALING, recipient=Recipient.TARGET),
                            CreatesAttachedVisual(
                                visual=Visual.Healing,
                                animation_duration=1,
                                expiration_duration=1,
                                scale=2,
                                random_starting_frame=True,
                                layer=1,
                                on_death=lambda e: esper.delete_entity(e),
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
    esper.add_component(entity, WalkEffects({
        frame: [PlaySound(sound_effects=[
            (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
        ])]
        for frame in [3, 7]
    }))
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
                                Grounded(),
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
                    status_effect=CrusaderBannerBearerEmpowered(time_remaining=gc.DEFAULT_AURA_PERIOD),
                    recipient=Recipient.TARGET
                )
            ],
            period=gc.DEFAULT_AURA_PERIOD,
            owner_condition=Alive(),
            unit_condition=All([
                Not(IsEntity(entity=entity)),
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
    esper.add_component(entity, WalkEffects({
        frame: [PlaySound(sound_effects=[
            (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
        ])]
        for frame in [3, 7]
    }))
    return entity

def create_crusader_crossbowman(x: int, y: int, team: TeamType) -> int:
    """Create a crossbowman entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CRUSADER_CROSSBOWMAN,
        movement_speed=gc.CRUSADER_CROSSBOWMAN_MOVEMENT_SPEED,
        health=gc.CRUSADER_CROSSBOWMAN_HP,
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
    no_target_strategy = TargetStrategy(
        rankings=[ByDistance(entity=entity, y_bias=2, ascending=True)],
        unit_condition=Never(),
    )
    esper.add_component(entity, Destination(target_strategy=targetting_strategy, x_offset=0))
    esper.add_component(
        entity,
        Ammo(
            gc.CRUSADER_CROSSBOWMAN_STARTING_AMMO,
            max=gc.CRUSADER_CROSSBOWMAN_MAX_AMMO
        )
    )
    esper.add_component(entity, Armor(flat_reduction=gc.ARMOR_FLAT_DAMAGE_REDUCTION, percent_reduction=gc.ARMOR_PERCENT_DAMAGE_REDUCTION))
    esper.add_component(entity, RangeIndicator(ranges=[gc.CRUSADER_CROSSBOWMAN_ATTACK_RANGE]))
    RELOADING = 0
    FIRING = 1
    esper.add_component(entity, Stance(stance=RELOADING))
    esper.add_component(entity, Abilities(
        abilities=[
            Ability(
                target_strategy=targetting_strategy,
                trigger_conditions=[
                    HasTarget(
                        unit_condition=All([
                            Alive(),
                            Grounded(),
                            MaximumDistanceFromEntity(
                                entity=entity,
                                distance=gc.CRUSADER_CROSSBOWMAN_ATTACK_RANGE,
                                y_bias=None
                            )
                        ])
                    ),
                    SatisfiesUnitCondition(
                        InStance(FIRING)
                    ),
                ],
                persistent_conditions=[
                    HasTarget(
                        unit_condition=All([
                            Alive(),
                            Grounded(),
                            MaximumDistanceFromEntity(
                                entity=entity,
                                distance=gc.CRUSADER_CROSSBOWMAN_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                y_bias=None
                            )
                        ])
                    )
                ],
                effects={
                    4: [
                        CreatesProjectile(
                            projectile_speed=gc.CRUSADER_CROSSBOWMAN_PROJECTILE_SPEED,
                            effects=[
                                Damages(damage=gc.CRUSADER_CROSSBOWMAN_ATTACK_DAMAGE, recipient=Recipient.TARGET),        
                            ],
                            visual=Visual.Arrow,
                            projectile_offset_x=5*gc.MINIFOLKS_SCALE,
                            projectile_offset_y=0,
                            unit_condition=All([OnTeam(team=team.other()), Alive(), Grounded()]),
                        ),
                        IncreaseAmmo(amount=-1),
                        PlaySound(SoundEffect(filename="crossbow_firing.wav", volume=0.2)),
                    ]
                }
            ),
            Ability(
                target_strategy=no_target_strategy,
                trigger_conditions=[
                    SatisfiesUnitCondition(
                        InStance(RELOADING)
                    ),
                ],
                persistent_conditions=[],
                effects={
                    2: [
                        IncreaseAmmo(amount=1),
                        PlaySound(SoundEffect(filename="crossbow_reloading.wav", volume=0.05)),
                    ]
                }
            ),
        ]
    ))
    esper.add_component(entity, InstantAbilities(
        abilities=[
            InstantAbility(
                target_strategy=no_target_strategy,
                trigger_conditions=[
                    SatisfiesUnitCondition(
                        All([
                            InStance(RELOADING),
                            AmmoEquals(gc.CRUSADER_CROSSBOWMAN_MAX_AMMO),
                        ])
                    ),
                ],
                effects=[
                    StanceChange(stance=FIRING),
                ],
            ),
            InstantAbility(
                target_strategy=no_target_strategy,
                trigger_conditions=[
                    SatisfiesUnitCondition(
                        All([
                            InStance(FIRING),
                            AmmoEquals(0),
                        ])
                    ),
                ],
                effects=[StanceChange(stance=RELOADING)],
            ),
            # If the target is not in range, reload
            InstantAbility(
                target_strategy=targetting_strategy,
                trigger_conditions=[
                    HasTarget(
                        unit_condition=MinimumDistanceFromEntity(
                            entity=entity,
                            distance=gc.CRUSADER_CROSSBOWMAN_ATTACK_RANGE*1.1, # Not in range, so reload
                            y_bias=None
                        )
                    ),
                    SatisfiesUnitCondition(
                        All([
                            InStance(FIRING),
                            Not(AmmoEquals(gc.CRUSADER_CROSSBOWMAN_MAX_AMMO))
                        ])
                    ),
                ],
                effects=[
                    StanceChange(stance=RELOADING),
                ],
            ),
        ]
    ))
    esper.add_component(
        entity,
        SpriteSheet(
            surface=sprite_sheets[UnitType.CRUSADER_CROSSBOWMAN],
            frame_width=100,
            frame_height=100,
            scale=gc.TINY_RPG_SCALE,
            frames={AnimationType.IDLE: 6, AnimationType.WALKING: 7, AnimationType.ABILITY1: 8, AnimationType.ABILITY2: 4, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 2, AnimationType.ABILITY2: 4, AnimationType.DYING: 5},
            animation_durations={
                AnimationType.IDLE: gc.CRUSADER_CROSSBOWMAN_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.CRUSADER_CROSSBOWMAN_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: gc.CRUSADER_CROSSBOWMAN_ANIMATION_ATTACK_DURATION,
                AnimationType.ABILITY2: gc.CRUSADER_CROSSBOWMAN_ANIMATION_RELOAD_DURATION,
                AnimationType.DYING: gc.CRUSADER_CROSSBOWMAN_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(0, 2),
        )
    )
    esper.add_component(entity, WalkEffects({
        frame: [PlaySound(sound_effects=[
            (SoundEffect(filename=f"armored_grass_footstep{i+1}.wav", volume=0.25), 1.0) for i in range(5)
        ])]
        for frame in [1, 5]
    }))
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
    esper.add_component(entity, Armor(flat_reduction=gc.ARMOR_FLAT_DAMAGE_REDUCTION, percent_reduction=gc.ARMOR_PERCENT_DAMAGE_REDUCTION))
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
                                Grounded(),
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
    esper.add_component(entity, WalkEffects({
        frame: [PlaySound(sound_effects=[
            (SoundEffect(filename=f"armored_grass_footstep{i+1}.wav", volume=0.25), 1.0) for i in range(5)
        ])]
        for frame in [1, 5]
    }))
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
    esper.add_component(entity, Armor(flat_reduction=gc.ARMOR_FLAT_DAMAGE_REDUCTION, percent_reduction=gc.ARMOR_PERCENT_DAMAGE_REDUCTION))
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
                                Grounded(),
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
                                    Alive(),
                                    Grounded(),
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
    esper.add_component(entity, WalkEffects({
        frame: [PlaySound(sound_effects=[
            (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
        ])]
        for frame in [3, 7]
    }))
    return entity

def create_crusader_guardian_angel(x: int, y: int, team: TeamType) -> int:
    """Create an angel entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CRUSADER_GUARDIAN_ANGEL,
        movement_speed=gc.CRUSADER_GUARDIAN_ANGEL_MOVEMENT_SPEED,
        health=gc.CRUSADER_GUARDIAN_ANGEL_HP,
        hitbox=Hitbox(
            width=16,
            height=22,
        )
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=None, ascending=True),
        ],
        unit_condition=All([Not(IsUnitType(unit_type=UnitType.CRUSADER_GUARDIAN_ANGEL)), OnTeam(team=team), Alive(), Grounded()])
    )
    target_attached = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=None, ascending=True),
        ],
        unit_condition=RememberedBy(entity=entity)
    )
    esper.add_component(
        entity,
        Destination(
            target_strategy=targetting_strategy,
            x_offset=gc.CRUSADER_GUARDIAN_ANGEL_ATTACHMENT_RANGE,
            use_team_x_offset=True,
            min_distance=0.01
        )
    )
    NOT_ATTACHED = 0
    ATTACHED = 1
    esper.add_component(entity, Stance(NOT_ATTACHED))
    esper.add_component(entity, NoNudge())
    esper.add_component(
        entity,
        InstantAbilities(
            abilities=[
                InstantAbility(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        SatisfiesUnitCondition(unit_condition=InStance(NOT_ATTACHED)),
                        HasTarget(
                            unit_condition=All([
                                Not(IsUnitType(unit_type=UnitType.CRUSADER_GUARDIAN_ANGEL)),
                                OnTeam(team=team),
                                Alive()
                            ])
                        ),
                        SatisfiesUnitCondition(unit_condition=MaximumDistanceFromDestination(distance=5))
                    ],
                    effects=[
                        StanceChange(ATTACHED),
                        AttachToTarget(
                            offset=(
                                -gc.CRUSADER_GUARDIAN_ANGEL_ATTACHMENT_RANGE
                                if team == TeamType.TEAM1
                                else gc.CRUSADER_GUARDIAN_ANGEL_ATTACHMENT_RANGE,
                                0
                            ),
                            on_death=lambda e: esper.remove_component(e, Attached),
                        ),
                        RememberTarget()
                    ]
                ),
                InstantAbility(
                    target_strategy=target_attached,
                    trigger_conditions=[
                        HasTarget(
                            unit_condition=Not(
                                All([
                                    Alive(),
                                    Grounded(),
                                    OnTeam(team=team),
                                ])
                            )
                        ),
                        SatisfiesUnitCondition(
                            HasComponent(EntityMemory),
                        ),
                    ],
                    effects=[
                        Forget(),
                        StanceChange(NOT_ATTACHED),
                    ],
                ),
                InstantAbility(
                    target_strategy=target_attached,
                    trigger_conditions=[
                        Cooldown(duration=gc.CRUSADER_GUARDIAN_ANGEL_HEAL_COOLDOWN),
                        HasTarget(
                            unit_condition=All([
                                OnTeam(team=team),
                                RememberedBy(entity=entity),
                                Alive()
                            ])
                        )
                    ],
                    effects=[
                        AppliesStatusEffect(
                            status_effect=Healing(time_remaining=gc.CRUSADER_GUARDIAN_ANGEL_HEAL_COOLDOWN, dps=gc.CRUSADER_GUARDIAN_ANGEL_HEALING/gc.CRUSADER_GUARDIAN_ANGEL_HEAL_COOLDOWN),
                            recipient=Recipient.TARGET
                        ),
                        CreatesAttachedVisual(
                            visual=Visual.Healing,
                            animation_duration=gc.CRUSADER_GUARDIAN_ANGEL_HEAL_COOLDOWN + 1/30,
                            expiration_duration=gc.CRUSADER_GUARDIAN_ANGEL_HEAL_COOLDOWN + 1/30,
                            scale=2,
                            on_death=lambda e: esper.delete_entity(e),
                            random_starting_frame=False,
                            layer=1,
                        ),
                        PlaySound(SoundEffect(filename="heal.wav", volume=0.50)),
                    ]
                )
            ]
        )
    )
    esper.add_component(
        entity,
        SpriteSheet(
            surface=sprite_sheets[UnitType.CRUSADER_GUARDIAN_ANGEL],
            frame_width=100,
            frame_height=100,
            scale=gc.TINY_RPG_SCALE,
            frames={AnimationType.IDLE: 24, AnimationType.WALKING: 24, AnimationType.DYING: 8},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 0, AnimationType.DYING: 1},
            sprite_center_offset=(0, 6),
            animation_durations={
                AnimationType.IDLE: gc.CRUSADER_GUARDIAN_ANGEL_ANIMATION_FLYING_DURATION,
                AnimationType.WALKING: gc.CRUSADER_GUARDIAN_ANGEL_ANIMATION_FLYING_DURATION,
                AnimationType.DYING: gc.CRUSADER_GUARDIAN_ANGEL_ANIMATION_DYING_DURATION,
            },
        )
    )
    esper.add_component(entity, WalkEffects({
        frame: [PlaySound(sound_effects=[
            (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
        ])]
        for frame in [3, 7]
    }))
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
        RangeIndicator(ranges=[gc.CRUSADER_LONGBOWMAN_ATTACK_RANGE])
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
                                Grounded(),
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
                                Grounded(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CRUSADER_LONGBOWMAN_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=None
                                )
                            ])
                        )
                    ],
                    effects={
                        4: [
                            PlaySound(SoundEffect(filename="longbow_loading.wav", volume=0.50)),
                        ],
                        6: [
                            CreatesProjectile(
                                projectile_speed=gc.CRUSADER_LONGBOWMAN_PROJECTILE_SPEED,
                                effects=[
                                    Damages(damage=gc.CRUSADER_LONGBOWMAN_ATTACK_DAMAGE, recipient=Recipient.TARGET),
                                ],
                                visual=Visual.Arrow,
                                projectile_offset_x=5*gc.MINIFOLKS_SCALE,
                                projectile_offset_y=0,
                                unit_condition=All([OnTeam(team=team.other()), Alive(), Grounded()]),
                            ),
                            PlaySound(SoundEffect(filename="arrow_fired_from_longbow.wav", volume=0.50)),
                        ]
                    },
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
    esper.add_component(entity, WalkEffects({
        frame: [PlaySound(sound_effects=[
            (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
        ])]
        for frame in [3, 7]
    }))
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
    esper.add_component(entity, Armor(flat_reduction=gc.ARMOR_FLAT_DAMAGE_REDUCTION, percent_reduction=gc.ARMOR_PERCENT_DAMAGE_REDUCTION))
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
                                Grounded(),
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
    esper.add_component(entity, WalkEffects({
        frame: [PlaySound(sound_effects=[
            (SoundEffect(filename=f"horse_footsteps_grass{i+1}.wav", volume=0.15), 1.0) for i in range(4)
        ])]
        for frame in [3]
    }))
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
    PIKE_UP = 0
    PIKE_DOWN = 1
    esper.add_component(entity, Stance(stance=PIKE_UP))
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
                                Grounded(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CRUSADER_PIKEMAN_ATTACK_RANGE,
                                    y_bias=10,
                                ),
                            ])
                        ),
                        SatisfiesUnitCondition(unit_condition=InStance(stance=PIKE_UP))
                    ],
                    persistent_conditions=[],
                    effects={
                        1: [
                            StanceChange(stance=PIKE_DOWN),
                        ]
                    }
                ),
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                Grounded(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CRUSADER_PIKEMAN_ATTACK_RANGE,
                                    y_bias=10
                                ),
                            ])
                        ),
                        SatisfiesUnitCondition(unit_condition=InStance(stance=PIKE_DOWN))
                    ],
                    persistent_conditions=[
                        HasTarget(
                            unit_condition=All([
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CRUSADER_PIKEMAN_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE*3,
                                    y_bias=10
                                ),
                            ])
                        ),
                        SatisfiesUnitCondition(unit_condition=InStance(stance=PIKE_DOWN))
                    ],
                    effects={3: [
                        Damages(damage=gc.CRUSADER_PIKEMAN_ATTACK_DAMAGE, recipient=Recipient.TARGET),
                        PlaySound([
                            (SoundEffect(filename=f"sword_swoosh{i+1}.wav", volume=0.50), 1.0) for i in range(3)
                        ]),
                    ]},
                ),
                # If this ability is triggered, then there must not be a valid unit to attack, so pike up.
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        SatisfiesUnitCondition(unit_condition=InStance(stance=PIKE_DOWN))
                    ],
                    persistent_conditions=[],
                    effects={
                        1: [
                            StanceChange(stance=PIKE_UP),
                        ]
                    }
                ),
            ]
        )
    )
    esper.add_component(
        entity,
        SpriteSheet(
            surface=sprite_sheets[UnitType.CRUSADER_PIKEMAN],
            frame_width=120,
            frame_height=120,
            scale=gc.TINY_RPG_SCALE,
            frames={AnimationType.IDLE: 6, AnimationType.WALKING: 7, AnimationType.ABILITY1: 2, AnimationType.ABILITY2: 6, AnimationType.ABILITY3: 2, AnimationType.DYING: 3},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 2, AnimationType.ABILITY2: 3, AnimationType.ABILITY3: 4, AnimationType.DYING: 5},
            animation_durations={
                AnimationType.IDLE: gc.CRUSADER_PIKEMAN_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.CRUSADER_PIKEMAN_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: gc.CRUSADER_PIKEMAN_ANIMATION_STANCE_CHANGE_DURATION,
                AnimationType.ABILITY2: gc.CRUSADER_PIKEMAN_ANIMATION_ATTACK_DURATION,
                AnimationType.ABILITY3: gc.CRUSADER_PIKEMAN_ANIMATION_STANCE_CHANGE_DURATION,
                AnimationType.DYING: gc.CRUSADER_PIKEMAN_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(25, -30),
        )
    )
    esper.add_component(entity, WalkEffects({
        frame: [PlaySound(sound_effects=[
            (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
        ])]
        for frame in [1, 4]
    }))
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
                                Grounded(),
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
                                    status_effect=DamageOverTime(
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
                                Alive(),
                                Grounded(),
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
                                Grounded(),
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
    esper.add_component(entity, WalkEffects({
        frame: [PlaySound(sound_effects=[
            (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
        ])]
        for frame in [3, 7]
    }))
    return entity

def create_crusader_soldier(x: int, y: int, team: TeamType) -> int:
    """Create a soldier entity with all necessary components."""
    MELEE = 0
    RANGED = 1
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CRUSADER_SOLDIER,
        movement_speed=gc.CRUSADER_SOLDIER_MOVEMENT_SPEED,
        health=gc.CRUSADER_SOLDIER_HP,
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
        Destination(target_strategy=targetting_strategy, x_offset=gc.CRUSADER_SOLDIER_MELEE_RANGE*2/3)
    )
    esper.add_component(
        entity,
        RangeIndicator(ranges=[gc.CRUSADER_SOLDIER_RANGED_RANGE])
    )
    esper.add_component(entity, Stance(stance=RANGED))
    esper.add_component(entity, Armor(flat_reduction=gc.ARMOR_FLAT_DAMAGE_REDUCTION, percent_reduction=gc.ARMOR_PERCENT_DAMAGE_REDUCTION))
    esper.add_component(
        entity,
        InstantAbilities(
            abilities=[
                InstantAbility(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        SatisfiesUnitCondition(InStance(stance=MELEE)),
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                MinimumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CRUSADER_SOLDIER_SWITCH_STANCE_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=None,
                                ),
                            ])
                        )
                    ],
                    effects=[StanceChange(stance=RANGED)]
                )
            ]
        )
    )
    esper.add_component(
        entity,
        Abilities(
            abilities=[
                # Switch stance to melee
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        SatisfiesUnitCondition(InStance(stance=RANGED)),
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CRUSADER_SOLDIER_SWITCH_STANCE_RANGE,
                                    y_bias=None,
                                ),
                            ])
                        )
                    ],
                    persistent_conditions=[],
                    effects={
                        1: [
                            StanceChange(stance=MELEE),
                            PlaySound(SoundEffect(filename="drawing_sword.wav", volume=0.15)),
                        ]
                    }
                ),
                # Melee attack
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        SatisfiesUnitCondition(InStance(stance=MELEE)),
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                Grounded(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CRUSADER_SOLDIER_MELEE_RANGE,
                                    y_bias=3
                                ),
                            ])
                        ),
                    ],
                    persistent_conditions=[
                        HasTarget(
                            unit_condition=All([
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CRUSADER_SOLDIER_MELEE_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=3
                                ),
                            ])
                        )
                    ],
                    effects={
                        3: [
                            Damages(damage=gc.CRUSADER_SOLDIER_MELEE_DAMAGE, recipient=Recipient.TARGET),
                            PlaySound([
                                (SoundEffect(filename=f"sword_swoosh{i+1}.wav", volume=0.50), 1.0) for i in range(3)
                            ]),
                        ]
                    }
                ),
                # Ranged attack
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        SatisfiesUnitCondition(InStance(stance=RANGED)),
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                Grounded(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CRUSADER_SOLDIER_RANGED_RANGE,
                                    y_bias=None,
                                ),
                            ])
                        ),
                    ],
                    persistent_conditions=[
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                Grounded(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CRUSADER_SOLDIER_RANGED_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=None
                                ),
                                MinimumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CRUSADER_SOLDIER_SWITCH_STANCE_RANGE,
                                    y_bias=None
                                )
                            ])
                        )
                    ],
                    effects={
                        4: [
                            PlaySound(SoundEffect(filename="bow_loading.wav", volume=0.25)),
                        ],
                        7: [
                            CreatesProjectile(
                                projectile_speed=gc.CORE_ARCHER_PROJECTILE_SPEED,
                                effects=[
                                    Damages(damage=gc.CORE_ARCHER_ATTACK_DAMAGE, recipient=Recipient.TARGET),
                                ],
                                visual=Visual.Arrow,
                                projectile_offset_x=5*gc.MINIFOLKS_SCALE,
                                projectile_offset_y=0,
                                unit_condition=All([OnTeam(team=team.other()), Alive(), Grounded()]),
                            ),
                            PlaySound(
                                sound_effects=[
                                    (SoundEffect(filename="arrow_fired_from_bow.wav", volume=0.25), 1.0),
                                ]
                            )
                        ]
                    }
                ),
            ]
        )
    )
    esper.add_component(
        entity,
        SpriteSheet(
            surface=sprite_sheets[UnitType.CRUSADER_SOLDIER],
            frame_width=100,
            frame_height=100,
            scale=gc.TINY_RPG_SCALE,
            frames={AnimationType.IDLE: 6, AnimationType.WALKING: 8, AnimationType.ABILITY1: 3, AnimationType.ABILITY2: 6, AnimationType.ABILITY3: 9, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 7, AnimationType.ABILITY2: 2, AnimationType.ABILITY3: 4, AnimationType.DYING: 6},
            animation_durations={
                AnimationType.IDLE: gc.CRUSADER_SOLDIER_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.CRUSADER_SOLDIER_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: gc.CRUSADER_SOLDIER_ANIMATION_SWITCH_STANCE_DURATION,
                AnimationType.ABILITY2: gc.CRUSADER_SOLDIER_ANIMATION_MELEE_ATTACK_DURATION,
                AnimationType.ABILITY3: gc.CRUSADER_SOLDIER_ANIMATION_RANGED_ATTACK_DURATION,
                AnimationType.DYING: gc.CRUSADER_SOLDIER_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(0, 1),
        )
    )
    esper.add_component(entity, WalkEffects({
        frame: [PlaySound(sound_effects=[
            (SoundEffect(filename=f"armored_grass_footstep{i+1}.wav", volume=0.25), 1.0) for i in range(5)
        ])]
        for frame in [3, 7]
    }))
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
                                Grounded(),
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
    return entity

def create_zombie_basic_zombie(x: int, y: int, team: TeamType) -> int:
    """Create a zombie entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.ZOMBIE_BASIC_ZOMBIE,
        movement_speed=gc.ZOMBIE_BASIC_ZOMBIE_MOVEMENT_SPEED,
        health=gc.ZOMBIE_BASIC_ZOMBIE_HP,
        hitbox=Hitbox(width=16, height=32),
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=All([OnTeam(team=team.other()), Alive()])
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.ZOMBIE_BASIC_ZOMBIE_ATTACK_RANGE*2/3)
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
                                Grounded(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.ZOMBIE_BASIC_ZOMBIE_ATTACK_RANGE,
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
                                    distance=gc.ZOMBIE_BASIC_ZOMBIE_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=3
                                ),
                            ])
                        )
                    ],
                    effects={3: [
                        Damages(damage=gc.ZOMBIE_BASIC_ZOMBIE_ATTACK_DAMAGE, recipient=Recipient.TARGET),
                        AppliesStatusEffect(
                            status_effect=ZombieInfection(time_remaining=gc.ZOMBIE_INFECTION_DURATION, team=team),
                            recipient=Recipient.TARGET
                        )
                    ]},
                )
            ]
        )
    )
    esper.add_component(entity, ImmuneToZombieInfection())
    esper.add_component(
        entity,
        SpriteSheet(
            surface=sprite_sheets[UnitType.ZOMBIE_BASIC_ZOMBIE],
            frame_width=100,
            frame_height=100,
            scale=gc.TINY_RPG_SCALE,
            frames={AnimationType.IDLE: 3, AnimationType.WALKING: 4, AnimationType.ABILITY1: 5, AnimationType.DYING: 6},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 2, AnimationType.DYING: 3},
            animation_durations={
                AnimationType.IDLE: gc.ZOMBIE_BASIC_ZOMBIE_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.ZOMBIE_BASIC_ZOMBIE_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: gc.ZOMBIE_BASIC_ZOMBIE_ANIMATION_ATTACK_DURATION,
                AnimationType.DYING: gc.ZOMBIE_BASIC_ZOMBIE_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(2, 8),
        )
    )
    esper.add_component(entity, WalkEffects({
        frame: [PlaySound(sound_effects=[
            (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
        ])]
        for frame in [1, 3]
    }))
    return entity

def create_zombie_jumper(x: int, y: int, team: TeamType) -> int:
    """Create a jumper zombie entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.ZOMBIE_JUMPER,
        movement_speed=gc.ZOMBIE_JUMPER_MOVEMENT_SPEED,
        health=gc.ZOMBIE_JUMPER_HP,
        hitbox=Hitbox(width=16, height=32),
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            WeightedRanking(
                rankings={
                    ByDistance(entity=entity, y_bias=None, ascending=True): 1,
                    ByCurrentHealth(ascending=False): -0.6,
                },
            ),
        ],
        unit_condition=All([OnTeam(team=team.other()), Alive()])
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.ZOMBIE_JUMPER_ATTACK_RANGE*2/3)
    )
    esper.add_component(entity, RangeIndicator([gc.ZOMBIE_JUMPER_MINIMUM_JUMP_RANGE, gc.ZOMBIE_JUMPER_MAXIMUM_JUMP_RANGE]))
    esper.add_component(
        entity,
        Abilities(
            abilities=[
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        SatisfiesUnitCondition(Grounded()),
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                Grounded(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.ZOMBIE_JUMPER_ATTACK_RANGE,
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
                                    distance=gc.ZOMBIE_JUMPER_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=3
                                ),
                            ])
                        )
                    ],
                    effects={3: [
                        Damages(damage=gc.ZOMBIE_JUMPER_ATTACK_DAMAGE, recipient=Recipient.TARGET),
                        AppliesStatusEffect(
                            status_effect=ZombieInfection(time_remaining=gc.ZOMBIE_INFECTION_DURATION, team=team),
                            recipient=Recipient.TARGET
                        )
                    ]},
                ),
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        Cooldown(duration=gc.ZOMBIE_JUMPER_JUMP_COOLDOWN),
                        SatisfiesUnitCondition(Grounded()),
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                Grounded(),
                                MinimumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.ZOMBIE_JUMPER_MINIMUM_JUMP_RANGE,
                                    y_bias=None
                                ),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.ZOMBIE_JUMPER_MAXIMUM_JUMP_RANGE,
                                    y_bias=None
                                ),
                            ])
                        )
                    ],
                    persistent_conditions=[
                        SatisfiesUnitCondition(Grounded()),
                        HasTarget(
                            unit_condition=All([
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.ZOMBIE_JUMPER_MAXIMUM_JUMP_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=None
                                ),
                            ])
                        )
                    ],
                    effects={0: [
                        Jump(
                            min_range=gc.ZOMBIE_JUMPER_MINIMUM_JUMP_RANGE,
                            max_range=gc.ZOMBIE_JUMPER_MAXIMUM_JUMP_RANGE,
                            max_angle=gc.ZOMBIE_JUMPER_MAXIMUM_JUMP_ANGLE,
                            effects=[],
                        )
                    ]},
                )
            ]
        )
    )
    esper.add_component(entity, ImmuneToZombieInfection())
    esper.add_component(
        entity,
        SpriteSheet(
            surface=sprite_sheets[UnitType.ZOMBIE_JUMPER],
            frame_width=100,
            frame_height=100,
            scale=gc.TINY_RPG_SCALE,
            frames={
                AnimationType.IDLE: 3,
                AnimationType.WALKING: 4,
                AnimationType.ABILITY1: 5,
                AnimationType.ABILITY2: 3,
                AnimationType.DYING: 6,
                AnimationType.AIRBORNE: 1,
            },
            rows={
                AnimationType.IDLE: 0,
                AnimationType.WALKING: 1,
                AnimationType.ABILITY1: 2,
                AnimationType.ABILITY2: 0,
                AnimationType.DYING: 3,
                AnimationType.AIRBORNE: 0,
            },
            animation_durations={
                AnimationType.IDLE: gc.ZOMBIE_JUMPER_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.ZOMBIE_JUMPER_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: gc.ZOMBIE_JUMPER_ANIMATION_ATTACK_DURATION,
                AnimationType.ABILITY2: gc.ZOMBIE_JUMPER_ANIMATION_JUMPING_DURATION,
                AnimationType.DYING: gc.ZOMBIE_JUMPER_ANIMATION_DYING_DURATION,
                AnimationType.AIRBORNE: gc.ZOMBIE_JUMPER_ANIMATION_AIRBORNE_DURATION,
            },
            sprite_center_offset=(2, 8),
        )
    )
    esper.add_component(entity, WalkEffects({
        frame: [PlaySound(sound_effects=[
            (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
        ])]
        for frame in [1, 3]
    }))
    return entity

def create_zombie_spitter(x: int, y: int, team: TeamType) -> int:
    """Create a spitter entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.ZOMBIE_SPITTER,
        movement_speed=gc.ZOMBIE_SPITTER_MOVEMENT_SPEED,
        health=gc.ZOMBIE_SPITTER_HP,
        hitbox=Hitbox(
            width=16,
            height=32,
        )
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            WeightedRanking(
                rankings={
                    ByDistance(entity=entity, y_bias=2, ascending=True): 1,
                    ConditionPenalty(condition_to_check=Any([Infected(), HasComponent(ImmuneToZombieInfection)]), value=300): 1,
                },
                ascending=True,
            ),
        ],
        unit_condition=All([OnTeam(team=team.other()), Alive()])
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=0)
    )
    esper.add_component(entity, RangeIndicator(ranges=[gc.ZOMBIE_SPITTER_ATTACK_RANGE]))
    esper.add_component(entity, ImmuneToZombieInfection())
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
                                Grounded(),
                                Not(Infected()),
                                Not(HasComponent(ImmuneToZombieInfection)),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.ZOMBIE_SPITTER_ATTACK_RANGE,
                                    y_bias=None
                                )
                            ])
                        )
                    ],
                    persistent_conditions=[
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                Grounded(),
                                Not(Infected()),
                                Not(HasComponent(ImmuneToZombieInfection)),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.ZOMBIE_SPITTER_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=None
                                )
                            ])
                        )
                    ],
                    effects={
                        3: [
                            CreatesProjectile(
                                projectile_speed=gc.ZOMBIE_SPITTER_PROJECTILE_SPEED,
                                effects=[
                                    AppliesStatusEffect(
                                        status_effect=ZombieInfection(time_remaining=gc.ZOMBIE_INFECTION_DURATION, team=team),
                                        recipient=Recipient.TARGET
                                    ),
                                    AppliesStatusEffect(
                                        status_effect=DamageOverTime(
                                            time_remaining=gc.ZOMBIE_INFECTION_DURATION,
                                            dps=gc.ZOMBIE_SPITTER_ATTACK_DAMAGE/gc.ZOMBIE_INFECTION_DURATION,
                                        ),
                                        recipient=Recipient.TARGET
                                    )
                                ],
                                visual=Visual.Arrow,
                                projectile_offset_x=5*gc.MINIFOLKS_SCALE,
                                projectile_offset_y=0,
                                unit_condition=All([OnTeam(team=team.other()), Alive(), Grounded(), Not(Infected())]),
                            ),
                            PlaySound(SoundEffect(filename="zombie_spitter_attack.wav", volume=0.50)),
                        ]
                    },
                ),
                # Uses basic zombie attack otherwise
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                Grounded(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.ZOMBIE_BASIC_ZOMBIE_ATTACK_RANGE,
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
                                    distance=gc.ZOMBIE_BASIC_ZOMBIE_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=3
                                ),
                            ])
                        )
                    ],
                    effects={3: [
                        Damages(damage=gc.ZOMBIE_BASIC_ZOMBIE_ATTACK_DAMAGE, recipient=Recipient.TARGET),
                        AppliesStatusEffect(
                            status_effect=ZombieInfection(time_remaining=gc.ZOMBIE_INFECTION_DURATION, team=team),
                            recipient=Recipient.TARGET
                        )
                    ]},
                )
            ]
        )
    )
    esper.add_component(entity, SpriteSheet(
        surface=sprite_sheets[UnitType.ZOMBIE_SPITTER],
        frame_width=100,
        frame_height=100,
        scale=gc.TINY_RPG_SCALE,
        frames={AnimationType.IDLE: 3, AnimationType.WALKING: 4, AnimationType.ABILITY1: 5, AnimationType.ABILITY2: 5, AnimationType.DYING: 6},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 2, AnimationType.ABILITY2: 2, AnimationType.DYING: 3},
        animation_durations={
            AnimationType.IDLE: gc.ZOMBIE_SPITTER_ANIMATION_IDLE_DURATION,
            AnimationType.WALKING: gc.ZOMBIE_SPITTER_ANIMATION_WALKING_DURATION,
            AnimationType.ABILITY1: gc.ZOMBIE_SPITTER_ANIMATION_ATTACK_DURATION,
            AnimationType.ABILITY2: gc.ZOMBIE_BASIC_ZOMBIE_ANIMATION_ATTACK_DURATION,
            AnimationType.DYING: gc.ZOMBIE_SPITTER_ANIMATION_DYING_DURATION,
        },
        sprite_center_offset=(2, 8),
    ))
    return entity

def create_zombie_tank(x: int, y: int, team: TeamType) -> int:
    """Create a tank zombie entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.ZOMBIE_TANK,
        movement_speed=gc.ZOMBIE_TANK_MOVEMENT_SPEED,
        health=gc.ZOMBIE_TANK_HP,
        hitbox=Hitbox(width=16, height=32),
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=All([OnTeam(team=team.other()), Alive()])
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.ZOMBIE_TANK_ATTACK_RANGE*2/3)
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
                                Grounded(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.ZOMBIE_TANK_ATTACK_RANGE,
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
                                    distance=gc.ZOMBIE_TANK_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=3
                                ),
                            ])
                        )
                    ],
                    effects={3: [
                        Damages(damage=gc.ZOMBIE_TANK_ATTACK_DAMAGE, recipient=Recipient.TARGET),
                        AppliesStatusEffect(
                            status_effect=ZombieInfection(time_remaining=gc.ZOMBIE_INFECTION_DURATION, team=team),
                            recipient=Recipient.TARGET
                        )
                    ]},
                )
            ]
        )
    )
    esper.add_component(entity, ImmuneToZombieInfection())
    esper.add_component(
        entity,
        SpriteSheet(
            surface=sprite_sheets[UnitType.ZOMBIE_TANK],
            frame_width=100,
            frame_height=100,
            scale=2*gc.TINY_RPG_SCALE,
            frames={AnimationType.IDLE: 3, AnimationType.WALKING: 4, AnimationType.ABILITY1: 5, AnimationType.DYING: 6},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 2, AnimationType.DYING: 3},
            animation_durations={
                AnimationType.IDLE: gc.ZOMBIE_TANK_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.ZOMBIE_TANK_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: gc.ZOMBIE_TANK_ANIMATION_ATTACK_DURATION,
                AnimationType.DYING: gc.ZOMBIE_TANK_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(2, 8),
        )
    )
    esper.add_component(entity, WalkEffects({
        frame: [PlaySound(sound_effects=[
            (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
        ])]
        for frame in [1, 3]
    }))
    return entity
