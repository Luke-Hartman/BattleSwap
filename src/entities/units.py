"""Unit creation module for Battle Swap.

This module contains functions for creating different types of units with their corresponding components.
"""

from enum import Enum
from components.unit_tier import UnitTier, UnitTierComponent
import esper
import pygame
import os
from typing import Dict, List, Optional, Type
from components.ammo import Ammo
from components.attached import Attached
from components.corruption import IncreasedAttackSpeedComponent, IncreasedDamageComponent, IncreasedMovementSpeedComponent
from components.entity_memory import EntityMemory
from components.follower import Follower
from components.forced_movement import ForcedMovement
from components.hitbox import Hitbox
from components.instant_ability import InstantAbilities, InstantAbility
from components.no_nudge import NoNudge
from components.projectile import Projectile
from components.range_indicator import RangeIndicator
from components.smooth_movement import SmoothMovement
from components.stance import Stance
from components.visual_link import VisualLink
from components.instant_ability import InstantAbilities, InstantAbility
from components.animation_effects import AnimationEffects
from components.unusable_corpse import UnusableCorpse
from game_constants import gc
from components.ability import Abilities, Ability, Cooldown, HasTarget, SatisfiesUnitCondition
from components.armor import Armor, ArmorLevel
from components.aura import Auras, Aura
from components.position import Position
from components.animation import AnimationState, AnimationType
from components.sprite_sheet import SpriteSheet
from components.status_effect import InfantryBannerBearerEmpowered, Fleeing, Healing, DamageOverTime, Invisible, StatusEffects, WontPursue, ZombieInfection, InfantryBannerBearerMovementSpeedBuff, InfantryBannerBearerAttackSpeedBuff, ReviveProgress
from target_strategy import ByCurrentHealth, ByDistance, ByMissingHealth, ConditionPenalty, TargetStrategy, TargetingGroup, WeightedRanking
from components.destination import Destination
from components.team import Team, TeamType
from components.item import ItemComponent
from components.item import ItemType
from components.unit_state import State, UnitState
from components.movement import Movement
from components.unit_type import UnitType, UnitTypeComponent
from components.velocity import Velocity
from components.health import Health
from components.orientation import Orientation, FacingDirection
from components.status_effect import Immobilized
from effects import (
    AddsForcedMovement, AppliesStatusEffect, CreatesRepeat, CreatesUnit, CreatesVisual,
    CreatesAttachedVisual, CreatesLobbed, CreatesProjectile, CreatesVisualLink, Damages, 
    Heals, HealToFull, HealPercentageMax, IncreaseAmmo, IncreasesMaxHealthFromTarget, Jump, PlaySound, Recipient, 
    SoundEffect, StanceChange, RememberTarget, CreatesVisualAoE, CreatesCircleAoE, Revive
)
from unit_condition import (
    All, Alive, Always, AmmoEquals, Any, Grounded, HasComponent, HasStatusEffect, HealthBelowPercent, InStance, Infected, IsEntity, IsUnitType, MaximumDistanceFromDestination, MinimumDistanceFromEntity, Never, Not, OnTeam,
    MaximumDistanceFromEntity, RememberedBy, RememberedSatisfies
)
from visuals import Visual
from components.on_death_effects import OnDeathEffect
from components.on_kill_effects import OnKillEffects
from components.on_hit_effects import OnHitEffects
from corruption_powers import CorruptionPower, IncreasedAttackSpeed, IncreasedDamage, IncreasedMaxHealth, IncreasedMovementSpeed

unit_theme_ids: Dict[UnitType, str] = {
    UnitType.CORE_ARCHER: "#core_archer_icon", 
    UnitType.CORE_VETERAN: "#core_veteran_icon",
    UnitType.CORE_CAVALRY: "#core_cavalry_icon",
    UnitType.CORE_DUELIST: "#core_duelist_icon",
    UnitType.CORE_LONGBOWMAN: "#core_longbowman_icon",
    UnitType.CORE_SWORDSMAN: "#core_swordsman_icon",
    UnitType.CORE_WIZARD: "#core_wizard_icon",
    UnitType.INFANTRY_BANNER_BEARER: "#infantry_banner_bearer_icon",
    UnitType.CRUSADER_BLACK_KNIGHT: "#crusader_black_knight_icon",
    UnitType.INFANTRY_CATAPULT: "#infantry_catapult_icon",
    UnitType.CRUSADER_CLERIC: "#crusader_cleric_icon",
    UnitType.MISC_COMMANDER: "#misc_commander_icon",
    UnitType.INFANTRY_CROSSBOWMAN: "#infantry_crossbowman_icon",
    UnitType.CORE_DEFENDER: "#core_defender_icon",
    UnitType.CRUSADER_GOLD_KNIGHT: "#crusader_gold_knight_icon",
    UnitType.CRUSADER_GUARDIAN_ANGEL: "#crusader_guardian_angel_icon",
    UnitType.CRUSADER_PALADIN: "#crusader_paladin_icon",
    UnitType.INFANTRY_PIKEMAN: "#infantry_pikeman_icon",
    UnitType.MISC_RED_KNIGHT: "#misc_red_knight_icon",
    UnitType.INFANTRY_SOLDIER: "#infantry_soldier_icon",
    UnitType.ORC_BERSERKER: "#orc_berserker_icon",
    UnitType.ORC_WARRIOR: "#orc_warrior_icon",
    UnitType.ORC_WARCHIEF: "#orc_warchief_icon",
    UnitType.ORC_GOBLIN: "#orc_goblin_icon",
    UnitType.ORC_WARG_RIDER: "#orc_warg_rider_icon",
    UnitType.PIRATE_CREW: "#pirate_crew_icon",
    UnitType.PIRATE_GUNNER: "#pirate_gunner_icon",
    UnitType.PIRATE_CAPTAIN: "#pirate_captain_icon",
    UnitType.PIRATE_CANNON: "#pirate_cannon_icon",
    UnitType.PIRATE_HARPOONER: "#pirate_harpooner_icon",
    UnitType.SKELETON_ARCHER: "#skeleton_archer_icon",
    UnitType.SKELETON_HORSEMAN: "#skeleton_horseman_icon",
    UnitType.SKELETON_MAGE: "#skeleton_mage_icon",
    UnitType.SKELETON_SWORDSMAN: "#skeleton_swordsman_icon",
    UnitType.SKELETON_ARCHER_NECROMANCER: "#skeleton_mage_icon",
    UnitType.SKELETON_HORSEMAN_NECROMANCER: "#skeleton_mage_icon",
    UnitType.SKELETON_MAGE_NECROMANCER: "#skeleton_mage_icon",
    UnitType.SKELETON_SWORDSMAN_NECROMANCER: "#skeleton_mage_icon",
    UnitType.SKELETON_LICH: "#skeleton_mage_icon",
    UnitType.WEREBEAR: "#werebear_icon",
    UnitType.ZOMBIE_BASIC_ZOMBIE: "#zombie_basic_zombie_icon",
    UnitType.MISC_BRUTE: "#misc_brute_icon",
    UnitType.ZOMBIE_FIGHTER: "#zombie_fighter_icon",
    UnitType.MISC_GRABBER: "#misc_grabber_icon",
    UnitType.ZOMBIE_JUMPER: "#zombie_jumper_icon",
    UnitType.ZOMBIE_SPITTER: "#zombie_spitter_icon",
    UnitType.ZOMBIE_TANK: "#zombie_tank_icon",
}

unit_icon_surfaces: Dict[UnitType, pygame.Surface] = {}

def get_unit_icon_theme_class(unit_tier: 'UnitTier') -> str:
    """Get the appropriate theme class for unit icons based on tier."""
    from components.unit_tier import UnitTier
    
    if unit_tier == UnitTier.ADVANCED:
        return "@unit_count_advanced"
    elif unit_tier == UnitTier.ELITE:
        return "@unit_count_elite"
    else:  # UnitTier.BASIC
        return "@unit_count"

def get_tier_label_theme_class(unit_tier: 'UnitTier') -> str:
    """Get the appropriate theme class for tier labels based on tier."""
    from components.unit_tier import UnitTier
    
    if unit_tier == UnitTier.ADVANCED:
        return "@tier_label_advanced"
    elif unit_tier == UnitTier.ELITE:
        return "@tier_label_elite"
    else:  # UnitTier.BASIC
        return "@tier_label_basic"

sprite_sheets: Dict[UnitType, pygame.Surface] = {}

class Faction(Enum):
    CORE = 0
    CRUSADERS = 1
    ORC = 2
    PIRATE = 3
    SKELETON = 4
    ZOMBIES = 5
    MISC = 6
    INFANTRY = 7
    
    @staticmethod
    def faction_of(unit_type: UnitType) -> "Faction":
        return _unit_to_faction[unit_type]

    @staticmethod
    def units(faction: "Faction") -> List[UnitType]:
        return [unit_type for unit_type, faction_value in _unit_to_faction.items() if faction_value == faction]

_unit_to_faction = {
    UnitType.CORE_ARCHER: Faction.CORE,
    UnitType.CORE_VETERAN: Faction.CORE,
    UnitType.CORE_CAVALRY: Faction.CORE,
    UnitType.CORE_DUELIST: Faction.CORE,
    UnitType.CORE_LONGBOWMAN: Faction.CORE,
    UnitType.CORE_SWORDSMAN: Faction.CORE,
    UnitType.CORE_WIZARD: Faction.CORE,
    UnitType.INFANTRY_BANNER_BEARER: Faction.INFANTRY,
    UnitType.CRUSADER_BLACK_KNIGHT: Faction.CRUSADERS,
    UnitType.INFANTRY_CATAPULT: Faction.INFANTRY,
    UnitType.CRUSADER_CLERIC: Faction.CRUSADERS,
    UnitType.MISC_COMMANDER: Faction.MISC,
    UnitType.INFANTRY_CROSSBOWMAN: Faction.INFANTRY,
    UnitType.CORE_DEFENDER: Faction.CORE,
    UnitType.CRUSADER_GOLD_KNIGHT: Faction.CRUSADERS,
    UnitType.CRUSADER_GUARDIAN_ANGEL: Faction.CRUSADERS,
    UnitType.CRUSADER_PALADIN: Faction.CRUSADERS,
    UnitType.INFANTRY_PIKEMAN: Faction.INFANTRY,
    UnitType.MISC_RED_KNIGHT: Faction.MISC,
    UnitType.INFANTRY_SOLDIER: Faction.INFANTRY,
    UnitType.ORC_BERSERKER: Faction.ORC,
    UnitType.ORC_WARRIOR: Faction.ORC,
    UnitType.ORC_WARCHIEF: Faction.ORC,
    UnitType.ORC_GOBLIN: Faction.ORC,
    UnitType.ORC_WARG_RIDER: Faction.ORC,
    UnitType.PIRATE_CREW: Faction.PIRATE,
    UnitType.PIRATE_GUNNER: Faction.PIRATE,
    UnitType.PIRATE_CAPTAIN: Faction.PIRATE,
    UnitType.PIRATE_CANNON: Faction.PIRATE,
    UnitType.PIRATE_HARPOONER: Faction.PIRATE,
    UnitType.SKELETON_ARCHER: Faction.SKELETON,
    UnitType.SKELETON_MAGE: Faction.SKELETON,
    UnitType.SKELETON_SWORDSMAN: Faction.SKELETON,
    UnitType.SKELETON_HORSEMAN: Faction.SKELETON,
    UnitType.SKELETON_ARCHER_NECROMANCER: Faction.SKELETON,
    UnitType.SKELETON_HORSEMAN_NECROMANCER: Faction.SKELETON,
    UnitType.SKELETON_MAGE_NECROMANCER: Faction.SKELETON,
    UnitType.SKELETON_SWORDSMAN_NECROMANCER: Faction.SKELETON,
    UnitType.SKELETON_LICH: Faction.SKELETON,
    UnitType.WEREBEAR: Faction.MISC,
    UnitType.ZOMBIE_BASIC_ZOMBIE: Faction.ZOMBIES,
    UnitType.MISC_BRUTE: Faction.MISC,
    UnitType.ZOMBIE_FIGHTER: Faction.ZOMBIES,
    UnitType.MISC_GRABBER: Faction.MISC,
    UnitType.ZOMBIE_JUMPER: Faction.ZOMBIES,
    UnitType.ZOMBIE_SPITTER: Faction.ZOMBIES,
    UnitType.ZOMBIE_TANK: Faction.ZOMBIES,
}

def load_sprite_sheets():
    """Load all sprite sheets and unit icons."""
    unit_filenames = {
        UnitType.CORE_ARCHER: "CoreArcher.png", 
        UnitType.CORE_VETERAN: "CoreVeteran.png",
        UnitType.CORE_CAVALRY: "CoreCavalry.png",
        UnitType.CORE_DUELIST: "CoreDuelist.png",
        UnitType.CORE_LONGBOWMAN: "CoreLongbowman.png",
        UnitType.CORE_SWORDSMAN: "CoreSwordsman.png", 
        UnitType.CORE_WIZARD: "CoreWizard.png",
        UnitType.INFANTRY_BANNER_BEARER: "InfantryBannerBearer.png",
        UnitType.CRUSADER_BLACK_KNIGHT: "CrusaderBlackKnight.png",
        UnitType.INFANTRY_CATAPULT: "InfantryCatapult.png",
        UnitType.CRUSADER_CLERIC: "CrusaderCleric.png",
        UnitType.MISC_COMMANDER: "MiscCommander.png",
        UnitType.INFANTRY_CROSSBOWMAN: "InfantryCrossbowman.png",
        UnitType.CORE_DEFENDER: "CoreDefender.png",
        UnitType.CRUSADER_GOLD_KNIGHT: "CrusaderGoldKnight.png",
        UnitType.CRUSADER_GUARDIAN_ANGEL: "CrusaderGuardianAngel.png",
        UnitType.CRUSADER_PALADIN: "CrusaderPaladin.png",
        UnitType.INFANTRY_PIKEMAN: "InfantryPikeman.png",
        UnitType.MISC_RED_KNIGHT: "MiscRedKnight.png",
        UnitType.INFANTRY_SOLDIER: "InfantrySoldier.png",
        UnitType.ORC_BERSERKER: "OrcBerserker.png",
        UnitType.ORC_WARRIOR: "OrcWarrior.png",
        UnitType.ORC_WARCHIEF: "OrcWarchief.png",
        UnitType.ORC_GOBLIN: "OrcGoblin.png",
        UnitType.ORC_WARG_RIDER: "OrcWargRider.png",
        UnitType.PIRATE_CREW: "PirateCrew.png",
        UnitType.PIRATE_GUNNER: "PirateGunner.png",
        UnitType.PIRATE_CAPTAIN: "PirateCaptain.png",
        UnitType.PIRATE_CANNON: "PirateCannon.png",
        UnitType.PIRATE_HARPOONER: "PirateHarpooner.png",
        UnitType.SKELETON_ARCHER: "SkeletonArcher.png",
        UnitType.SKELETON_MAGE: "SkeletonMage.png",
        UnitType.SKELETON_SWORDSMAN: "SkeletonSwordsman.png",
        UnitType.SKELETON_HORSEMAN: "SkeletonHorseman.png",
        UnitType.SKELETON_ARCHER_NECROMANCER: "SkeletonArcherNecromancer.png",
        UnitType.SKELETON_HORSEMAN_NECROMANCER: "SkeletonHorsemanNecromancer.png",
        UnitType.SKELETON_MAGE_NECROMANCER: "SkeletonMageNecromancer.png",
        UnitType.SKELETON_SWORDSMAN_NECROMANCER: "SkeletonSwordsmanNecromancer.png",
        UnitType.SKELETON_LICH: "SkeletonLich.png",
        UnitType.WEREBEAR: "Werebear.png",
        UnitType.ZOMBIE_BASIC_ZOMBIE: "ZombieBasicZombieNew.png",
        UnitType.MISC_BRUTE: "ZombieBasicZombie.png",
        UnitType.ZOMBIE_FIGHTER: "ZombieFighter.png",
        UnitType.MISC_GRABBER: "ZombieBasicZombie.png",
        UnitType.ZOMBIE_JUMPER: "ZombieJumper.png",
        UnitType.ZOMBIE_SPITTER: "ZombieSpitter.png",
        UnitType.ZOMBIE_TANK: "ZombieTank.png",
    }
    for unit_type, filename in unit_filenames.items():
        if unit_type in sprite_sheets:
            continue
        path = os.path.join("assets", "units", filename)
        sprite_sheets[unit_type] = pygame.image.load(path).convert_alpha()

    # Load unit icons
    unit_icon_paths: Dict[UnitType, str] = {
        UnitType.CORE_ARCHER: "CoreArcherIcon.png",
        UnitType.CORE_VETERAN: "CoreVeteranIcon.png",
        UnitType.CORE_CAVALRY: "CoreCavalryIcon.png",
        UnitType.CORE_DUELIST: "CoreDuelistIcon.png",
        UnitType.CORE_LONGBOWMAN: "CoreLongbowmanIcon.png",
        UnitType.CORE_SWORDSMAN: "CoreSwordsmanIcon.png",
        UnitType.CORE_WIZARD: "CoreWizardIcon.png",
        UnitType.INFANTRY_BANNER_BEARER: "InfantryBannerBearerIcon.png",
        UnitType.CRUSADER_BLACK_KNIGHT: "CrusaderBlackKnightIcon.png",
        UnitType.INFANTRY_CATAPULT: "InfantryCatapultIcon.png",
        UnitType.CRUSADER_CLERIC: "CrusaderClericIcon.png",
        UnitType.MISC_COMMANDER: "MiscCommanderIcon.png",
        UnitType.INFANTRY_CROSSBOWMAN: "InfantryCrossbowmanIcon.png",
        UnitType.CORE_DEFENDER: "CoreDefenderIcon.png",
        UnitType.CRUSADER_GOLD_KNIGHT: "CrusaderGoldKnightIcon.png",
        UnitType.CRUSADER_GUARDIAN_ANGEL: "CrusaderGuardianAngelIcon.png",
        UnitType.CRUSADER_PALADIN: "CrusaderPaladinIcon.png",
        UnitType.INFANTRY_PIKEMAN: "InfantryPikemanIcon.png",
        UnitType.MISC_RED_KNIGHT: "MiscRedKnightIcon.png",
        UnitType.INFANTRY_SOLDIER: "InfantrySoldierIcon.png",
        UnitType.ORC_BERSERKER: "OrcBerserkerIcon.png",
        UnitType.ORC_WARRIOR: "OrcWarriorIcon.png",
        UnitType.ORC_WARCHIEF: "OrcWarchiefIcon.png",
        UnitType.ORC_GOBLIN: "OrcGoblinIcon.png",
        UnitType.ORC_WARG_RIDER: "OrcWargRiderIcon.png",
        UnitType.PIRATE_CREW: "PirateCrewIcon.png",
        UnitType.PIRATE_GUNNER: "PirateGunnerIcon.png",
        UnitType.PIRATE_CAPTAIN: "PirateCaptainIcon.png",
        UnitType.PIRATE_CANNON: "PirateCannonIcon.png",
        UnitType.PIRATE_HARPOONER: "PirateHarpoonerIcon.png",
        UnitType.SKELETON_ARCHER: "SkeletonArcherIcon.png",
        UnitType.SKELETON_MAGE: "SkeletonMageIcon.png",
        UnitType.SKELETON_SWORDSMAN: "SkeletonSwordsmanIcon.png",
        UnitType.SKELETON_HORSEMAN: "SkeletonHorsemanIcon.png",
        UnitType.SKELETON_ARCHER_NECROMANCER: "SkeletonArcherNecromancerIcon.png",
        UnitType.SKELETON_HORSEMAN_NECROMANCER: "SkeletonHorsemanNecromancerIcon.png",
        UnitType.SKELETON_MAGE_NECROMANCER: "SkeletonMageNecromancerIcon.png",
        UnitType.SKELETON_SWORDSMAN_NECROMANCER: "SkeletonSwordsmanNecromancerIcon.png",
        UnitType.WEREBEAR: "WerebearIcon.png",
        UnitType.ZOMBIE_BASIC_ZOMBIE: "ZombieBasicZombieIcon.png",
        UnitType.MISC_BRUTE: "MiscBruteIcon.png",
        UnitType.ZOMBIE_FIGHTER: "ZombieFighterIcon.png",
        UnitType.MISC_GRABBER: "MiscGrabberIcon.png",
        UnitType.ZOMBIE_JUMPER: "ZombieBasicZombieIcon.png",
        UnitType.ZOMBIE_SPITTER: "ZombieSpitterIcon.png",
        UnitType.ZOMBIE_TANK: "ZombieTankIcon.png",
    }
    for unit_type, filename in unit_icon_paths.items():
        if unit_type in unit_icon_surfaces:
            continue
        path = os.path.join("assets", "icons", filename)
        unit_icon_surfaces[unit_type] = pygame.image.load(path).convert_alpha()

def _get_corruption_power(
        corruption_powers: Optional[List[CorruptionPower]],
        power_type: Type[CorruptionPower],
        team: TeamType
    ) -> Optional[CorruptionPower]:
    if corruption_powers is None:
        return None
    for power in corruption_powers:
        if isinstance(power, power_type) and (power.required_team is None or power.required_team == team):
            return power
    return None

# Note: These are tuples, not lists so they don't get mutated as they will be shared by many units.
MALE_DEATH_SOUNDS = (
    PlaySound(
        (
            *((SoundEffect(filename=f"male_death_grunt_{i}.wav", volume=0.07), 1.0) for i in range(8)),
            (SoundEffect(filename=f"wilhelm_scream.wav", volume=0.07), gc.WILHELM_CHANCE*8)
        )
    ),
)

FEMALE_DEATH_SOUNDS = (
    PlaySound(
        (
            *((SoundEffect(filename=f"female_death_grunt_{i}.wav", volume=0.07), 1.0) for i in range(8)),
            (SoundEffect(filename=f"wilhelm_scream.wav", volume=0.07), gc.WILHELM_CHANCE*8)
        )
    ),
)

HORSE_DEATH_SOUNDS = (
    PlaySound(
        (
            *((SoundEffect(filename=f"neighing_{i}.wav", volume=0.07), 1.0) for i in range(3)),
            (SoundEffect(filename=f"wilhelm_scream.wav", volume=0.07), gc.WILHELM_CHANCE*3)
        )
    ),
)

OLD_MALE_DEATH_SOUNDS = (
    PlaySound(
        (
            *((SoundEffect(filename=f"old_male_death_grunt_{i}.wav", volume=0.1), 1.0) for i in range(4)),
            (SoundEffect(filename=f"wilhelm_scream.wav", volume=0.07), gc.WILHELM_CHANCE*4)
        )
    ),
)

ORC_DEATH_SOUNDS = (
    PlaySound(
        (
            *((SoundEffect(filename=f"orc_death_grunt_{i}.wav", volume=0.07), 1.0) for i in range(3)),
            (SoundEffect(filename=f"wilhelm_scream.wav", volume=0.07), gc.WILHELM_CHANCE*3)
        )
    ),
)

SKELETON_DEATH_SOUNDS = (
    PlaySound(
        (
            *((SoundEffect(filename=f"skeleton_death_{i}.wav", volume=0.07), 1.0) for i in range(4)),
            (SoundEffect(filename=f"wilhelm_scream.wav", volume=0.07), gc.WILHELM_CHANCE*4)
        )
    ),
)

ZOMBIE_DEATH_SOUNDS = (
    PlaySound(
        (
            *((SoundEffect(filename=f"zombie_grunt_{i}.wav", volume=0.07), 1.0) for i in range(3)),
            (SoundEffect(filename=f"wilhelm_scream.wav", volume=0.07), gc.WILHELM_CHANCE*3)
        )
    ),
)

def create_unit(
    x: int,
    y: int,
    unit_type: UnitType,
    team: TeamType,
    corruption_powers: Optional[List[CorruptionPower]],
    tier: UnitTier = UnitTier.BASIC,
    play_spawning: bool = False,
    orientation: Optional[FacingDirection] = None,
    items: Optional[List[ItemType]] = None,
) -> int:
    """Create a unit entity with all necessary components."""
    entity = {
        UnitType.CORE_ARCHER: create_core_archer,
        UnitType.CORE_VETERAN: create_core_veteran,
        UnitType.CORE_CAVALRY: create_core_cavalry,
        UnitType.CORE_DUELIST: create_core_duelist,
        UnitType.CORE_LONGBOWMAN: create_core_longbowman,
        UnitType.CORE_SWORDSMAN: create_core_swordsman,
        UnitType.CORE_WIZARD: create_core_wizard,
        UnitType.INFANTRY_BANNER_BEARER: create_infantry_banner_bearer,
        UnitType.CRUSADER_BLACK_KNIGHT: create_crusader_black_knight,
        UnitType.INFANTRY_CATAPULT: create_infantry_catapult,
        UnitType.CRUSADER_CLERIC: create_crusader_cleric,
        UnitType.MISC_COMMANDER: create_misc_commander,
        UnitType.INFANTRY_CROSSBOWMAN: create_infantry_crossbowman,
        UnitType.CORE_DEFENDER: create_core_defender,
        UnitType.CRUSADER_GOLD_KNIGHT: create_crusader_gold_knight,
        UnitType.CRUSADER_GUARDIAN_ANGEL: create_crusader_guardian_angel,
        UnitType.CRUSADER_PALADIN: create_crusader_paladin,
        UnitType.INFANTRY_PIKEMAN: create_infantry_pikeman,
        UnitType.MISC_RED_KNIGHT: create_misc_red_knight,
        UnitType.INFANTRY_SOLDIER: create_infantry_soldier,
        UnitType.ORC_BERSERKER: create_orc_berserker,
        UnitType.ORC_WARRIOR: create_orc_warrior,
        UnitType.ORC_WARCHIEF: create_orc_warchief,
        UnitType.ORC_GOBLIN: create_orc_goblin,
        UnitType.ORC_WARG_RIDER: create_orc_warg_rider,
        UnitType.PIRATE_CREW: create_pirate_crew,
        UnitType.PIRATE_GUNNER: create_pirate_gunner,
        UnitType.PIRATE_CAPTAIN: create_pirate_captain,
        UnitType.PIRATE_CANNON: create_pirate_cannon,
        UnitType.PIRATE_HARPOONER: create_pirate_harpooner,
        UnitType.SKELETON_ARCHER: create_skeleton_archer,
        UnitType.SKELETON_MAGE: create_skeleton_mage,
        UnitType.SKELETON_SWORDSMAN: create_skeleton_swordsman,
        UnitType.SKELETON_HORSEMAN: create_skeleton_horseman,
        UnitType.SKELETON_ARCHER_NECROMANCER: create_skeleton_archer_necromancer,
        UnitType.SKELETON_HORSEMAN_NECROMANCER: create_skeleton_horseman_necromancer,
        UnitType.SKELETON_MAGE_NECROMANCER: create_skeleton_mage_necromancer,
        UnitType.SKELETON_SWORDSMAN_NECROMANCER: create_skeleton_swordsman_necromancer,
        UnitType.SKELETON_LICH: create_skeleton_lich,
        UnitType.WEREBEAR: create_werebear,
        UnitType.ZOMBIE_BASIC_ZOMBIE: create_zombie_basic_zombie,
        UnitType.MISC_BRUTE: create_misc_brute,
        UnitType.ZOMBIE_FIGHTER: create_zombie_fighter,
        UnitType.MISC_GRABBER: create_misc_grabber,
        UnitType.ZOMBIE_JUMPER: create_zombie_jumper,
        UnitType.ZOMBIE_SPITTER: create_zombie_spitter,
        UnitType.ZOMBIE_TANK: create_zombie_tank,
    }[unit_type](x, y, team, corruption_powers, tier, play_spawning, orientation)

    # Add ItemComponent and apply item effects
    esper.add_component(entity, ItemComponent(items or []))
    if items:
        from entities.items import item_registry
        for item_type in items:
            item = item_registry[item_type]
            item.apply(entity)
    
    return entity

def unit_base_entity(
        x: int,
        y: int,
        team: TeamType,
        unit_type: UnitType,
        movement_speed: float,
        health: int,
        hitbox: Hitbox,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a unit entity with all components shared by all units."""
    entity = esper.create_entity()
    esper.add_component(entity, Position(x=x, y=y))
    esper.add_component(entity, Velocity(x=0, y=0))
    esper.add_component(entity, Movement(speed=movement_speed))
    esper.add_component(entity, AnimationState(type=AnimationType.SPAWNING if play_spawning else AnimationType.IDLE))
    esper.add_component(entity, Team(type=team))
    esper.add_component(entity, UnitState(state=State.SPAWNING if play_spawning else State.IDLE))
    esper.add_component(entity, UnitTypeComponent(type=unit_type))
    health_power = _get_corruption_power(corruption_powers, IncreasedMaxHealth, team)
    if health_power is not None:
        health = health * (1 + health_power.increase_percent / 100)    
    esper.add_component(entity, Health(current=health, maximum=health))
    esper.add_component(entity, StatusEffects())
    # Use provided orientation or default based on team
    facing_direction = orientation if orientation is not None else (FacingDirection.RIGHT if team == TeamType.TEAM1 else FacingDirection.LEFT)
    esper.add_component(entity, Orientation(facing=facing_direction))
    esper.add_component(entity, hitbox)
    movement_power = _get_corruption_power(corruption_powers, IncreasedMovementSpeed, team)
    if movement_power is not None:
        esper.add_component(entity, IncreasedMovementSpeedComponent(increase_percent=movement_power.increase_percent))
    animation_power = _get_corruption_power(corruption_powers, IncreasedAttackSpeed, team)
    if animation_power is not None:
        esper.add_component(entity, IncreasedAttackSpeedComponent(increase_percent=animation_power.increase_percent))
    damage_power = _get_corruption_power(corruption_powers, IncreasedDamage, team)
    if damage_power is not None:
        esper.add_component(entity, IncreasedDamageComponent(increase_percent=damage_power.increase_percent))
    esper.add_component(entity, UnitTierComponent(tier))
    # Add empty OnDeathEffect component to all units for items and other death effects
    esper.add_component(entity, OnDeathEffect(effects=[]))
    return entity

def create_core_archer(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
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
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=0)
    )
    # Determine range and projectile speed based on tier - Elite gets 50% more range and 50% more projectile speed
    attack_range = gc.CORE_ARCHER_ATTACK_RANGE
    projectile_speed = gc.CORE_ARCHER_PROJECTILE_SPEED
    if tier == UnitTier.ELITE:
        attack_range = attack_range * 1.5
        projectile_speed = projectile_speed * 1.5
    
    esper.add_component(entity, RangeIndicator(ranges=[attack_range]))
    arrow_damage = gc.CORE_ARCHER_ATTACK_DAMAGE
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
                                    distance=attack_range,
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
                                    distance=attack_range + gc.TARGETTING_GRACE_DISTANCE,
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
                                projectile_speed=projectile_speed,
                                effects=[
                                    Damages(damage=arrow_damage, recipient=Recipient.TARGET, is_melee=False),
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
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.CORE_ARCHER, tier))
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
            ])]
            for frame in [1, 4]
        },
    }))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(MALE_DEATH_SOUNDS)
    return entity

def create_core_veteran(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a veteran entity with all necessary components."""
    # Calculate tier-specific values
    veteran_health = gc.CORE_VETERAN_HP
    veteran_damage = gc.CORE_VETERAN_ATTACK_DAMAGE
    veteran_movement_speed = gc.CORE_VETERAN_MOVEMENT_SPEED
    
    # Advanced tier (and Elite): 25% more health and damage
    if tier == UnitTier.ADVANCED or tier == UnitTier.ELITE:
        veteran_health = veteran_health * 1.25
        veteran_damage = veteran_damage * 1.25
    
    # Elite tier: additional 25% faster movement speed 
    if tier == UnitTier.ELITE:
        veteran_movement_speed = veteran_movement_speed * 1.25
    
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CORE_VETERAN,
        movement_speed=veteran_movement_speed,
        health=veteran_health,
        hitbox=Hitbox(
            width=20,
            height=38,
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=4, ascending=True),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.CORE_VETERAN_ATTACK_RANGE*2/3)
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
                                    distance=gc.CORE_VETERAN_ATTACK_RANGE,
                                    y_bias=2
                                ),
                            ])
                        )
                    ],
                    persistent_conditions=[],
                    effects={
                        5: [
                            CreatesVisualAoE(
                                effects=[
                                    Damages(damage=veteran_damage, recipient=Recipient.TARGET, is_melee=True),
                                ],
                                duration=gc.CORE_VETERAN_ANIMATION_ATTACK_DURATION*3/10,
                                scale=gc.MINIFOLKS_SCALE,
                                unit_condition=All([
                                    OnTeam(team=team.other()),
                                    Alive(),
                                    Grounded(),
                                ]),
                                visual=Visual.CoreVeteranAttack,
                                location=Recipient.PARENT,
                            ),
                            PlaySound(SoundEffect(filename="deep_swoosh.wav", volume=0.70)),
                        ]
                    },
                )
            ]
        )
    )
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.CORE_VETERAN, tier))
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
            ])]
            for frame in [2, 5]
        },
    }))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(MALE_DEATH_SOUNDS)
    return entity

def create_core_cavalry(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a cavalry entity with all necessary components."""
    # Calculate tier-specific values
    cavalry_health = gc.CORE_CAVALRY_HP
    cavalry_damage = gc.CORE_CAVALRY_ATTACK_DAMAGE
    
    # Advanced tier: 60% more health
    if tier == UnitTier.ADVANCED:
        cavalry_health = cavalry_health * 1.6
    
    # Elite tier: another +60% HP (total 2.2x base health)
    elif tier == UnitTier.ELITE:
        cavalry_health = cavalry_health * 2.2
    
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CORE_CAVALRY,
        movement_speed=gc.CORE_CAVALRY_MOVEMENT_SPEED,
        health=cavalry_health,
        hitbox=Hitbox(
            width=32,
            height=46,
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
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
                        Damages(damage=cavalry_damage, recipient=Recipient.TARGET, is_melee=True),
                        PlaySound([
                            (SoundEffect(filename=f"sword_swoosh{i+1}.wav", volume=0.50), 1.0) for i in range(3)
                        ]),
                    ]},
                )
            ]
        )
    )
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.CORE_CAVALRY, tier))
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"horse_footsteps_grass{i+1}.wav", volume=0.15), 1.0) for i in range(4)
            ])]
            for frame in [2]
        },
    }))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(HORSE_DEATH_SOUNDS)
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(MALE_DEATH_SOUNDS)
    return entity

def create_core_duelist(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
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
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.CORE_DUELIST_ATTACK_RANGE*7/8)
    )
    sound_effects = [
        (SoundEffect(filename=f"quick_sword_thrust{i}.wav", volume=0.75), 1.0)
        for i in range(1, 6)
    ]
    if tier == UnitTier.BASIC:
        hits_per_frame = 2
    elif tier == UnitTier.ADVANCED:
        hits_per_frame = 3
    elif tier == UnitTier.ELITE:
        hits_per_frame = 4
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
                        5: [Damages(damage=gc.CORE_DUELIST_ATTACK_DAMAGE, recipient=Recipient.TARGET, is_melee=True)] * hits_per_frame + [
                            PlaySound(sound_effects),
                        ],
                        6: [Damages(damage=gc.CORE_DUELIST_ATTACK_DAMAGE, recipient=Recipient.TARGET, is_melee=True)] * hits_per_frame + [
                            PlaySound(sound_effects),
                        ],
                        7: [Damages(damage=gc.CORE_DUELIST_ATTACK_DAMAGE, recipient=Recipient.TARGET, is_melee=True)] * hits_per_frame + [
                            PlaySound(sound_effects),
                        ],
                        8: [Damages(damage=gc.CORE_DUELIST_ATTACK_DAMAGE, recipient=Recipient.TARGET, is_melee=True)] * hits_per_frame + [
                            PlaySound(sound_effects),
                        ],
                        9: [Damages(damage=gc.CORE_DUELIST_ATTACK_DAMAGE, recipient=Recipient.TARGET, is_melee=True)] * hits_per_frame + [
                            PlaySound(sound_effects),
                        ],
                        10: [Damages(damage=gc.CORE_DUELIST_ATTACK_DAMAGE, recipient=Recipient.TARGET, is_melee=True)] * hits_per_frame + [
                            PlaySound(sound_effects),
                        ],
                        11: [Damages(damage=gc.CORE_DUELIST_ATTACK_DAMAGE, recipient=Recipient.TARGET, is_melee=True)] * hits_per_frame + [
                            PlaySound(sound_effects),
                        ],
                    },
                )
            ]
        )
    )
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.CORE_DUELIST, tier))
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
            ])]
            for frame in [3, 7]
        },
    }))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(FEMALE_DEATH_SOUNDS)
    return entity

def create_core_longbowman(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a longbowman entity with all necessary components."""
    # Calculate tier-specific values
    longbowman_damage = gc.CORE_LONGBOWMAN_ATTACK_DAMAGE
    
    if tier == UnitTier.ADVANCED or tier == UnitTier.ELITE:
        pierce = 1
    else:
        pierce = 0
    
    # Advanced tier: 33.33% damage cut
    if tier == UnitTier.ADVANCED:
        longbowman_damage = longbowman_damage * (2/3)  # 33.33% damage cut
    
    # Elite tier: damage back to normal (no damage cut)
    # No additional changes needed since longbowman_damage starts at base value
    
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CORE_LONGBOWMAN,
        movement_speed=gc.CORE_LONGBOWMAN_MOVEMENT_SPEED,
        health=gc.CORE_LONGBOWMAN_HP,
        hitbox=Hitbox(
            width=16,
            height=36,
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=0)
    )
    esper.add_component(
        entity,
        RangeIndicator(ranges=[gc.CORE_LONGBOWMAN_ATTACK_RANGE])
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
                                    distance=gc.CORE_LONGBOWMAN_ATTACK_RANGE,
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
                                    distance=gc.CORE_LONGBOWMAN_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
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
                                projectile_speed=gc.CORE_LONGBOWMAN_PROJECTILE_SPEED,
                                effects=[
                                    Damages(damage=longbowman_damage, recipient=Recipient.TARGET, is_melee=False),
                                ],
                                visual=Visual.LongbowArrow,
                                projectile_offset_x=5*gc.MINIFOLKS_SCALE,
                                projectile_offset_y=0,
                                unit_condition=All([OnTeam(team=team.other()), Alive(), Grounded()]),
                                pierce=pierce,
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
        get_unit_sprite_sheet(UnitType.CORE_LONGBOWMAN, tier)
    )
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
            ])]
            for frame in [3, 7]
        },
    }))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(FEMALE_DEATH_SOUNDS)
    return entity

def create_core_swordsman(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a swordsman entity with all necessary components."""
    # Calculate tier-specific values
    swordsman_health = gc.CORE_SWORDSMAN_HP
    swordsman_damage = gc.CORE_SWORDSMAN_ATTACK_DAMAGE
    
    # Advanced tier: 30% more health and damage
    if tier == UnitTier.ADVANCED:
        swordsman_health = swordsman_health * 1.3
        swordsman_damage = swordsman_damage * 1.3
    
    # Elite tier: 60% more health and damage (total)
    elif tier == UnitTier.ELITE:
        swordsman_health = swordsman_health * 1.6
        swordsman_damage = swordsman_damage * 1.6
    
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CORE_SWORDSMAN,
        movement_speed=gc.CORE_SWORDSMAN_MOVEMENT_SPEED,
        health=swordsman_health,
        hitbox=Hitbox(
            width=16,
            height=32,
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
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
                            Damages(damage=swordsman_damage, recipient=Recipient.TARGET, is_melee=True),
                            PlaySound([
                                (SoundEffect(filename=f"sword_swoosh{i+1}.wav", volume=0.50), 1.0) for i in range(3)
                            ]),
                        ]
                    },
                )
            ]
        )
    )
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.CORE_SWORDSMAN, tier))
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
            ])]
            for frame in [2, 5]
        },
    }))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(MALE_DEATH_SOUNDS)
    return entity

def create_skeleton_archer(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a skeleton archer entity with all necessary components."""
    # Calculate tier-specific values
    skeleton_archer_damage = gc.SKELETON_ARCHER_ATTACK_DAMAGE
    attack_range = gc.SKELETON_ARCHER_ATTACK_RANGE
    attack_animation_duration = gc.SKELETON_ARCHER_ANIMATION_ATTACK_DURATION
    projectile_speed = gc.SKELETON_ARCHER_PROJECTILE_SPEED
    
    # Advanced tier: 50% faster rate of fire
    if tier == UnitTier.ADVANCED:
        attack_animation_duration = attack_animation_duration * 2/3  # 50% faster = 2/3 duration
    
    # Elite tier: 50% more range and projectile speed
    if tier == UnitTier.ELITE:
        attack_range = attack_range * 1.5
        projectile_speed = projectile_speed * 1.5
    
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.SKELETON_ARCHER,
        movement_speed=gc.SKELETON_ARCHER_MOVEMENT_SPEED,
        health=gc.SKELETON_ARCHER_HP,
        hitbox=Hitbox(
            width=16,
            height=32,
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=0)
    )
    
    esper.add_component(entity, RangeIndicator(ranges=[attack_range]))
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
                                    distance=attack_range,
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
                                    distance=attack_range + gc.TARGETTING_GRACE_DISTANCE,
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
                        7: [  # Projectile created on frame 7
                            CreatesProjectile(
                                projectile_speed=projectile_speed,
                                effects=[
                                    Damages(damage=skeleton_archer_damage, recipient=Recipient.TARGET, is_melee=False),
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
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.SKELETON_ARCHER, tier))
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
            ])]
            for frame in [1, 4]
        },
    }))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(SKELETON_DEATH_SOUNDS)
    esper.add_component(entity, UnusableCorpse())
    return entity

def create_skeleton_mage(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a skeleton mage entity with all necessary components."""
    # Calculate tier-specific damage
    skeleton_mage_damage = gc.SKELETON_MAGE_ATTACK_DAMAGE
    attack_range = gc.SKELETON_MAGE_ATTACK_RANGE
    attack_animation_duration = gc.SKELETON_MAGE_ANIMATION_ATTACK_DURATION
    projectile_speed = gc.SKELETON_MAGE_PROJECTILE_SPEED
    
    # Advanced tier: 50% more damage
    if tier == UnitTier.ADVANCED:
        skeleton_mage_damage = skeleton_mage_damage * 1.5
    
    # Elite tier: 100% more damage total
    elif tier == UnitTier.ELITE:
        skeleton_mage_damage = skeleton_mage_damage * 2.0
    
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.SKELETON_MAGE,
        movement_speed=gc.SKELETON_MAGE_MOVEMENT_SPEED,
        health=gc.SKELETON_MAGE_HP,
        hitbox=Hitbox(
            width=16,
            height=32,
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=0)
    )
    
    esper.add_component(entity, RangeIndicator(ranges=[attack_range]))
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
                                    distance=attack_range,
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
                                    distance=attack_range + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=None
                                )
                            ])
                        )
                    ],
                    effects={
                        2: [
                            PlaySound(SoundEffect(filename="skeleton_mage_cast.wav", volume=0.1)),
                            CreatesProjectile(
                                projectile_speed=projectile_speed,
                                effects=[
                                    CreatesVisualAoE(
                                        effects=[
                                            Damages(damage=skeleton_mage_damage, recipient=Recipient.TARGET, is_melee=False),
                                            PlaySound(SoundEffect(filename="skeleton_mage_aoe.wav", volume=1.0)),
                                        ],
                                        duration=0.5,
                                        scale=gc.MINIFOLKS_SCALE,
                                        unit_condition=All([Alive(), Grounded()]),
                                        location=Recipient.PARENT,
                                        visual=Visual.SkeletonMageExplosion,
                                    ),
                                ],
                                visual=Visual.SkeletonMageProjectile,
                                unit_condition=All([OnTeam(team=team.other()), Alive(), Grounded()]),
                                projectile_offset_x=10*gc.MINIFOLKS_SCALE,
                                projectile_offset_y=2*gc.MINIFOLKS_SCALE,
                            )
                        ],
                    },
                )
            ]
        )
    )
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.SKELETON_MAGE, tier))
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
            ])]
            for frame in [1, 4]
        },
    }))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(SKELETON_DEATH_SOUNDS)
    esper.add_component(entity, UnusableCorpse())
    return entity

def create_skeleton_swordsman(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a skeleton swordsman entity with all necessary components."""
    # Calculate tier-specific values
    skeleton_swordsman_health = gc.SKELETON_SWORDSMAN_HP
    skeleton_swordsman_damage = gc.SKELETON_SWORDSMAN_ATTACK_DAMAGE
    
    # Advanced tier: 30% more health and damage
    if tier == UnitTier.ADVANCED:
        skeleton_swordsman_health = skeleton_swordsman_health * 1.3
        skeleton_swordsman_damage = skeleton_swordsman_damage * 1.3
    
    # Elite tier: 60% more health and damage (total)
    elif tier == UnitTier.ELITE:
        skeleton_swordsman_health = skeleton_swordsman_health * 1.6
        skeleton_swordsman_damage = skeleton_swordsman_damage * 1.6
    
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.SKELETON_SWORDSMAN,
        movement_speed=gc.SKELETON_SWORDSMAN_MOVEMENT_SPEED,
        health=skeleton_swordsman_health,
        hitbox=Hitbox(
            width=16,
            height=32,
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.SKELETON_SWORDSMAN_ATTACK_RANGE*2/3)
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
                                    distance=gc.SKELETON_SWORDSMAN_ATTACK_RANGE,
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
                                    distance=gc.SKELETON_SWORDSMAN_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=3
                                ),
                            ])
                        )
                    ],
                    effects={
                        2: [
                            Damages(damage=skeleton_swordsman_damage, recipient=Recipient.TARGET, is_melee=True),
                            PlaySound([
                                (SoundEffect(filename=f"sword_swoosh{i+1}.wav", volume=0.50), 1.0) for i in range(3)
                            ]),
                        ]
                    },
                )
            ]
        )
    )
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.SKELETON_SWORDSMAN, tier))
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
            ])]
            for frame in [2, 5]
        },
    }))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(SKELETON_DEATH_SOUNDS)
    esper.add_component(entity, UnusableCorpse())
    return entity

def create_skeleton_horseman(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a skeleton horseman entity with all necessary components."""
    skeleton_horseman_health = gc.SKELETON_HORSEMAN_HP
    skeleton_horseman_damage = gc.SKELETON_HORSEMAN_ATTACK_DAMAGE

    if tier == UnitTier.ADVANCED:
        skeleton_horseman_health = skeleton_horseman_health * 1.6
    elif tier == UnitTier.ELITE:
        skeleton_horseman_health = skeleton_horseman_health * 2.2

    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.SKELETON_HORSEMAN,
        movement_speed=gc.SKELETON_HORSEMAN_MOVEMENT_SPEED,
        health=skeleton_horseman_health,
        hitbox=Hitbox(
            width=32,
            height=46,
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.SKELETON_HORSEMAN_ATTACK_RANGE*2/3)
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
                                    distance=gc.SKELETON_HORSEMAN_ATTACK_RANGE,
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
                                    distance=gc.SKELETON_HORSEMAN_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=5
                                ),
                            ])
                        )
                    ],
                    effects={4: [
                        Damages(damage=skeleton_horseman_damage, recipient=Recipient.TARGET, is_melee=True),
                        PlaySound([
                            (SoundEffect(filename=f"sword_swoosh{i+1}.wav", volume=0.50), 1.0) for i in range(3)
                        ]),
                    ]},
                )
            ]
        )
    )
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.SKELETON_HORSEMAN, tier))
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"horse_footsteps_grass{i+1}.wav", volume=0.15), 1.0) for i in range(4)
            ])]
            for frame in [2]
        },
    }))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(SKELETON_DEATH_SOUNDS)
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(HORSE_DEATH_SOUNDS)
    esper.add_component(entity, UnusableCorpse())
    return entity

def create_orc_berserker(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create an orc berserker entity with all necessary components."""
    # Calculate tier-specific values
    orc_berserker_health = gc.ORC_BERSERKER_HP
    orc_berserker_ranged_damage = gc.ORC_BERSERKER_RANGED_DAMAGE
    orc_berserker_melee_damage = gc.ORC_BERSERKER_MELEE_DAMAGE
    orc_berserker_movement_speed = gc.ORC_BERSERKER_MOVEMENT_SPEED
    
    # Advanced tier: 50% increased damage
    if tier == UnitTier.ADVANCED or tier == UnitTier.ELITE:
        orc_berserker_ranged_damage = orc_berserker_ranged_damage * 1.5
        orc_berserker_melee_damage = orc_berserker_melee_damage * 1.5
    
    # Elite tier: 50% increased life
    if tier == UnitTier.ELITE:
        orc_berserker_health = orc_berserker_health * 1.5
    
    MELEE = 0
    RANGED = 1
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.ORC_BERSERKER,
        movement_speed=orc_berserker_movement_speed,
        health=orc_berserker_health,
        hitbox=Hitbox(
            width=16,
            height=32,
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    
    # Orcs start at 50% life
    health_component = esper.component_for_entity(entity, Health)
    health_component.current = int(health_component.maximum * 0.5)
    
    # Add OnKillEffects component for orc healing
    esper.add_component(
        entity,
        OnKillEffects(
            effects=[
                HealPercentageMax(
                    recipient=Recipient.OWNER,
                    percentage=0.5,
                    duration=1.0
                ),
                PlaySound([
                    (SoundEffect(filename=f"orc_berserker_kill_sound{i+1}.wav", volume=0.50), 1.0) for i in range(4)
                ]),
                CreatesAttachedVisual(
                    recipient=Recipient.OWNER,
                    visual=Visual.Healing,
                    animation_duration=1,
                    expiration_duration=1,
                    scale=2,
                    random_starting_frame=True,
                    layer=1,
                    on_death=lambda e: esper.delete_entity(e),
                )
            ]
        )
    )
    
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.ORC_BERSERKER_MELEE_RANGE*2/3)
    )
    esper.add_component(
        entity,
        RangeIndicator(ranges=[gc.ORC_BERSERKER_RANGED_RANGE])
    )
    esper.add_component(entity, Stance(stance=RANGED))
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
                                    distance=gc.ORC_BERSERKER_SWITCH_STANCE_RANGE + gc.TARGETTING_GRACE_DISTANCE,
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
                                    distance=gc.ORC_BERSERKER_SWITCH_STANCE_RANGE,
                                    y_bias=None,
                                ),
                            ])
                        )
                    ],
                    persistent_conditions=[],
                    effects={
                        1: [
                            StanceChange(stance=MELEE),
                        ]
                    }
                ),
                # Melee attack (2 hits)
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
                                    distance=gc.ORC_BERSERKER_MELEE_RANGE,
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
                                    distance=gc.ORC_BERSERKER_MELEE_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=3
                                ),
                            ])
                        )
                    ],
                    effects={
                        2: [
                            Damages(
                                damage=orc_berserker_melee_damage, 
                                recipient=Recipient.TARGET,
                                is_melee=True
                            ),
                            Damages(
                                damage=orc_berserker_melee_damage, 
                                recipient=Recipient.TARGET,
                                is_melee=True
                            ),
                            PlaySound([
                                (SoundEffect(filename=f"sword_swoosh{i+1}.wav", volume=0.50), 1.0) for i in range(3)
                            ]),
                            PlaySound([
                                (SoundEffect(filename=f"sword_swoosh{i+1}.wav", volume=0.50), 1.0) for i in range(3)
                            ]),
                        ]
                    }
                ),
                # Ranged attack (throwing axe)
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
                                    distance=gc.ORC_BERSERKER_RANGED_RANGE,
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
                                    distance=gc.ORC_BERSERKER_RANGED_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=None
                                ),
                                MinimumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.ORC_BERSERKER_SWITCH_STANCE_RANGE,
                                    y_bias=None
                                )
                            ])
                        )
                    ],
                    effects={
                        2: [
                            CreatesProjectile(
                                projectile_speed=gc.ORC_BERSERKER_PROJECTILE_SPEED,
                                effects=[
                                    Damages(
                                        damage=orc_berserker_ranged_damage, 
                                        recipient=Recipient.TARGET,
                                        is_melee=False
                                    ),
                                ],
                                visual=Visual.OrcThrowingAxe,
                                projectile_offset_x=5*gc.MINIFOLKS_SCALE,
                                projectile_offset_y=0,
                                unit_condition=All([OnTeam(team=team.other()), Alive(), Grounded()]),
                                on_create=lambda projectile_entity: esper.add_component(
                                    projectile_entity, 
                                    AnimationEffects({
                                        AnimationType.IDLE: {
                                            0: [
                                                PlaySound(
                                                    sound_effects=[
                                                        (SoundEffect(filename="normal_swoosh.wav", volume=0.25), 1.0),
                                                    ]
                                                )
                                            ],
                                            2: [
                                                PlaySound(
                                                    sound_effects=[
                                                        (SoundEffect(filename="normal_swoosh.wav", volume=0.1), 1.0),
                                                    ]
                                                )
                                            ]
                                        }
                                    })
                                ),
                            ),
                            PlaySound(
                                sound_effects=[
                                    (SoundEffect(filename="normal_swoosh.wav", volume=0.25), 1.0),
                                ]
                            ),
                        ]
                    }
                )
            ]
        )
    )
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.ORC_BERSERKER, tier))
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
            ])]
            for frame in [2, 5]
        },
    }))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(ORC_DEATH_SOUNDS)
    return entity

def create_orc_warrior(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create an orc warrior entity with all necessary components."""
    # Calculate tier-specific values
    orc_warrior_health = gc.ORC_WARRIOR_HP
    orc_warrior_damage = gc.ORC_WARRIOR_ATTACK_DAMAGE
    orc_warrior_movement_speed = gc.ORC_WARRIOR_MOVEMENT_SPEED
    
    # Advanced tier: 30% more health and damage
    if tier == UnitTier.ADVANCED or tier == UnitTier.ELITE:
        orc_warrior_health = orc_warrior_health * 1.3
        orc_warrior_damage = orc_warrior_damage * 1.3
    
    # Elite tier: 30% increased movement and attack speed
    if tier == UnitTier.ELITE:
        orc_warrior_movement_speed = gc.ORC_WARRIOR_MOVEMENT_SPEED * 1.3
    
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.ORC_WARRIOR,
        movement_speed=orc_warrior_movement_speed,
        health=orc_warrior_health,
        hitbox=Hitbox(
            width=16,
            height=32,
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    
    # Orcs start at 50% life
    health_component = esper.component_for_entity(entity, Health)
    health_component.current = int(health_component.maximum * 0.5)
    
    # Add OnKillEffects component for orc healing
    esper.add_component(
        entity,
        OnKillEffects(
            effects=[
                HealPercentageMax(
                    recipient=Recipient.OWNER,
                    percentage=0.5,
                    duration=1.0
                ),  
                PlaySound([
                    (SoundEffect(filename=f"orc_kill_sound{i+1}.wav", volume=0.50), 1.0) for i in range(4)
                ]),
                CreatesAttachedVisual(
                    recipient=Recipient.OWNER,
                    visual=Visual.Healing,
                    animation_duration=1,
                    expiration_duration=1,
                    scale=2,
                    random_starting_frame=True,
                    layer=1,
                    on_death=lambda e: esper.delete_entity(e),
                )
            ]
        )
    )
    
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.ORC_WARRIOR_ATTACK_RANGE*2/3)
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
                                    distance=gc.ORC_WARRIOR_ATTACK_RANGE,
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
                                    distance=gc.ORC_WARRIOR_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=3
                                ),
                            ])
                        )
                    ],
                    effects={
                        2: [
                            Damages(
                                damage=orc_warrior_damage, 
                                recipient=Recipient.TARGET,
                                is_melee=True
                            ),
                            PlaySound([
                                (SoundEffect(filename=f"sword_swoosh{i+1}.wav", volume=0.50), 1.0) for i in range(3)
                            ]),
                        ]
                    },
                )
            ]
        )
    )
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.ORC_WARRIOR, tier))
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
            ])]
            for frame in [2, 5]
        },
    }))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(ORC_DEATH_SOUNDS)
    return entity

def create_orc_warchief(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create an orc warchief entity with all necessary components."""
    # Calculate tier-specific values
    orc_warchief_health = gc.ORC_WARCHIEF_HP
    orc_warchief_damage = gc.ORC_WARCHIEF_ATTACK_DAMAGE
    
    # Advanced tier: 50% increased health
    if tier == UnitTier.ADVANCED or tier == UnitTier.ELITE:
        orc_warchief_health = orc_warchief_health * 1.5
    
    # Elite tier: 50% increased damage
    if tier == UnitTier.ELITE:
        orc_warchief_damage = orc_warchief_damage * 1.5
    
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.ORC_WARCHIEF,
        movement_speed=gc.ORC_WARCHIEF_MOVEMENT_SPEED,
        health=orc_warchief_health,
        hitbox=Hitbox(
            width=16,
            height=32,
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )

    # Orcs start at 50% life
    health_component = esper.component_for_entity(entity, Health)
    health_component.current = int(health_component.maximum * 0.5)
    
    # Add OnKillEffects component for orc warchief abilities
    esper.add_component(
        entity,
        OnKillEffects(
            effects=[
                IncreasesMaxHealthFromTarget(
                    recipient=Recipient.OWNER
                ),
                HealPercentageMax(
                    recipient=Recipient.OWNER,
                    percentage=0.5,
                    duration=1.0
                ),
                PlaySound([
                    (SoundEffect(filename=f"orc_warchief_kill_sound{i+1}.wav", volume=0.50), 1.0) for i in range(4)
                ]),
                CreatesAttachedVisual(
                    recipient=Recipient.OWNER,
                    visual=Visual.Healing,
                    animation_duration=1,
                    expiration_duration=1,
                    scale=2,
                    random_starting_frame=True,
                    layer=1,
                    on_death=lambda e: esper.delete_entity(e),
                )
            ]
        )
    )
    
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.ORC_WARCHIEF_ATTACK_RANGE*2/3)
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
                                    distance=gc.ORC_WARCHIEF_ATTACK_RANGE,
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
                                    distance=gc.ORC_WARCHIEF_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=3
                                ),
                            ])
                        )
                    ],
                    effects={
                        2: [
                            Damages(
                                damage=orc_warchief_damage, 
                                recipient=Recipient.TARGET,
                                is_melee=True
                            ),
                            PlaySound([
                                (SoundEffect(filename=f"sword_swoosh{i+1}.wav", volume=0.50), 1.0) for i in range(3)
                            ]),
                        ]
                    },
                )
            ]
        )
    )
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.ORC_WARCHIEF, tier))
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
            ])]
            for frame in [2, 5]
        },
    }))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(ORC_DEATH_SOUNDS)
    return entity

def create_orc_goblin(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create an orc goblin entity with all necessary components."""
    # Calculate tier-specific values
    orc_goblin_movement_speed = gc.ORC_GOBLIN_MOVEMENT_SPEED
    orc_goblin_invisible_duration = gc.ORC_GOBLIN_INVISIBLE_DURATION
    
    # Elite tier: 25% increased movement speed and attack speed
    if tier == UnitTier.ELITE:
        orc_goblin_movement_speed = orc_goblin_movement_speed * 1.25
    
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.ORC_GOBLIN,
        movement_speed=orc_goblin_movement_speed,
        health=gc.ORC_GOBLIN_HP,
        hitbox=Hitbox(
            width=16,
            height=28,
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    
    # Add OnKillEffects component for orc goblin invisibility
    esper.add_component(
        entity,
        OnKillEffects(
            effects=[
                AppliesStatusEffect(
                    status_effect=Invisible(time_remaining=orc_goblin_invisible_duration, owner=entity),
                    recipient=Recipient.OWNER
                ),
                PlaySound(SoundEffect(filename="orc_goblin_laugh.wav", volume=0.50)),
            ]
        )
    )
    
    # Hunter targeting strategy like black knight
    targetting_strategy = TargetStrategy(
        rankings=[
            WeightedRanking(
                rankings={
                    ByDistance(entity=entity, y_bias=None, ascending=True): 1,
                    ByCurrentHealth(ascending=False): -0.6,
                },
            ),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
    )
    
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.ORC_GOBLIN_ATTACK_RANGE*2/3)
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
                                    distance=gc.ORC_GOBLIN_ATTACK_RANGE,
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
                                    distance=gc.ORC_GOBLIN_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=3
                                ),
                            ])
                        )
                    ],
                    effects={
                        2: [
                            Damages(
                                damage=gc.ORC_GOBLIN_ATTACK_DAMAGE, 
                                recipient=Recipient.TARGET,
                                is_melee=True
                            ),
                            PlaySound([
                                (SoundEffect(filename=f"sword_swoosh{i+1}.wav", volume=0.50), 1.0) for i in range(3)
                            ]),
                        ]
                    },
                )
            ]
        )
    )
    
    # Add instant ability for advanced tier goblins to go invisible at combat start
    if tier == UnitTier.ADVANCED or tier == UnitTier.ELITE:
        # Apply invisibility status effect directly so unit starts invisible
        if esper.has_component(entity, StatusEffects):
            status_effects = esper.component_for_entity(entity, StatusEffects)
            status_effects.add(Invisible(time_remaining=orc_goblin_invisible_duration, owner=entity))
        # Add instant ability to play sound when round starts
        esper.add_component(
            entity,
            InstantAbilities(
                abilities=[
                    InstantAbility(
                        target_strategy=targetting_strategy,
                        trigger_conditions=[
                            Cooldown(duration=float("inf")),
                        ],
                        effects=[
                            AppliesStatusEffect(
                                status_effect=Invisible(time_remaining=orc_goblin_invisible_duration, owner=entity),
                                recipient=Recipient.OWNER
                            ),
                            PlaySound(SoundEffect(filename="orc_goblin_laugh.wav", volume=0.50))
                        ]
                    )
                ]
            )
        )
    
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.ORC_GOBLIN, tier))
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
            ])]
            for frame in [2, 5]
        },
    }))
    esper.add_component(entity,
        OnDeathEffect(
            [
                PlaySound([
                    (SoundEffect(filename=f"goblin_death_grunt_{i}.wav", volume=0.07), 1.0) for i in range(3)
                ] + [
                    (SoundEffect(filename=f"wilhelm_scream.wav", volume=0.07), gc.WILHELM_CHANCE*3)
                ]),
            ]
        )
    )
    return entity

def create_orc_warg_rider(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create an orc warg rider entity with all necessary components."""
    # Calculate tier-specific values
    warg_rider_damage = gc.ORC_WARG_RIDER_ATTACK_DAMAGE
    warg_rider_movement_speed = gc.ORC_WARG_RIDER_MOVEMENT_SPEED
    
    # Advanced tier: 25% increased attack and movement speed
    if tier == UnitTier.ADVANCED or tier == UnitTier.ELITE:
        warg_rider_movement_speed = warg_rider_movement_speed * 1.25
    
    # Elite tier: 50% increased damage
    if tier == UnitTier.ELITE:
        warg_rider_damage = warg_rider_damage * 1.5
    
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.ORC_WARG_RIDER,
        movement_speed=warg_rider_movement_speed,
        health=gc.ORC_WARG_RIDER_HP,
        hitbox=Hitbox(
            width=32,
            height=46,
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )

    # Orcs start at 50% life
    health_component = esper.component_for_entity(entity, Health)
    health_component.current = int(health_component.maximum * 0.5)
    
    # Add OnKillEffects component for orc healing
    esper.add_component(
        entity,
        OnKillEffects(
            effects=[
                HealPercentageMax(
                    recipient=Recipient.OWNER,
                    percentage=0.5,
                    duration=1.0
                ),
                PlaySound([
                    (SoundEffect(filename=f"orc_warg_rider_kill_sound{i+1}.wav", volume=0.50), 1.0) for i in range(4)
                ]),
                CreatesAttachedVisual(
                    recipient=Recipient.OWNER,
                    visual=Visual.Healing,
                    animation_duration=1,
                    expiration_duration=1,
                    scale=2,
                    random_starting_frame=True,
                    layer=1,
                    on_death=lambda e: esper.delete_entity(e),
                )
            ]
        )
    )
    
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.ORC_WARG_RIDER_ATTACK_RANGE*2/3)
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
                                    distance=gc.ORC_WARG_RIDER_ATTACK_RANGE,
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
                                    distance=gc.ORC_WARG_RIDER_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=3
                                ),
                            ])
                        )
                    ],
                    effects={
                        1: [
                            PlaySound([
                                (SoundEffect(filename=f"warg_bite.wav", volume=0.40), 1.0)
                            ]),
                        ],
                        2: [
                            Damages(
                                damage=warg_rider_damage * 2/3, 
                                recipient=Recipient.TARGET,
                                is_melee=True
                            ),
                            Damages(
                                damage=warg_rider_damage * 1/3, 
                                recipient=Recipient.TARGET,
                                is_melee=True
                            ),
                            PlaySound([
                                (SoundEffect(filename=f"sword_swoosh{i+1}.wav", volume=0.50), 1.0) for i in range(3)
                            ]),
                        ]
                    }
                )
            ]
        )
    )
    
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.ORC_WARG_RIDER, tier))
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"horse_footsteps_grass{i+1}.wav", volume=0.15), 1.0) for i in range(4)
            ])]
            for frame in [2, 5]
        },
    }))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(ORC_DEATH_SOUNDS)
    return entity

def create_core_wizard(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a wizard entity with all necessary components."""
    # Calculate tier-specific damage
    wizard_damage = gc.CORE_WIZARD_ATTACK_DAMAGE
    
    # Advanced tier: 50% more damage
    if tier == UnitTier.ADVANCED:
        wizard_damage = wizard_damage * 1.5
    
    # Elite tier: 100% more damage total
    elif tier == UnitTier.ELITE:
        wizard_damage = wizard_damage * 2.0
    
    # Calculate tier-specific range
    attack_range = gc.CORE_WIZARD_ATTACK_RANGE
    
    # Advanced tier: 15% more range
    if tier == UnitTier.ADVANCED:
        attack_range = attack_range * 1.15
    
    # Elite tier: 30% more range total (15% + 15%)
    elif tier == UnitTier.ELITE:
        attack_range = attack_range * 1.30
    
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
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=0)
    )
    esper.add_component(entity, RangeIndicator(ranges=[attack_range]))
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
                                    distance=attack_range,
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
                                    distance=attack_range + gc.TARGETTING_GRACE_DISTANCE,
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
                                    CreatesCircleAoE(
                                        effects=[
                                            Damages(damage=wizard_damage, recipient=Recipient.TARGET, is_melee=False),
                                        ],
                                        radius=gc.CORE_WIZARD_FIREBALL_AOE_RADIUS,
                                        unit_condition=All([Alive(), Grounded()]),
                                        location=Recipient.PARENT,
                                    ),
                                    CreatesVisual(
                                        recipient=Recipient.PARENT,
                                        visual=Visual.Explosion,
                                        animation_duration=gc.CORE_WIZARD_FIREBALL_AOE_DURATION,
                                        scale=gc.CORE_WIZARD_FIREBALL_AOE_RADIUS * gc.EXPLOSION_VISUAL_SCALE_RATIO,
                                        duration=gc.CORE_WIZARD_FIREBALL_AOE_DURATION,
                                        layer=2,
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
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.CORE_WIZARD, tier))
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
            ])]
            for frame in [1, 4]
        },
    }))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(OLD_MALE_DEATH_SOUNDS)
    return entity

def _create_skeleton_necromancer(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        unit_type: UnitType,
        summoned_type: UnitType,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a skeleton necromancer that summons a corresponding unit."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=unit_type,
        movement_speed=gc.SKELETON_NECROMANCER_MOVEMENT_SPEED,
        health=gc.SKELETON_NECROMANCER_HP,
        hitbox=Hitbox(
            width=16,
            height=32,
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    # Target isn't used, this just prevents constant summoning after all enemies are dead.
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
    )
    # Make skeleton necromancers followers
    esper.add_component(entity, Follower())
    target_leader = TargetStrategy(
        rankings=[
            WeightedRanking(
                rankings={
                    ByDistance(entity=entity, y_bias=None, ascending=True): 1,
                    ConditionPenalty(condition_to_check=RememberedBy(entity=entity), value=-10000): 1,
                }
            ),
        ],
        unit_condition=Not(HasComponent(component=Follower)),
        targetting_group=TargetingGroup.TEAM1_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM2_LIVING_VISIBLE
    )
    esper.add_component(
        entity,
        Destination(
            target_strategy=target_leader,
            x_offset=gc.SKELETON_NECROMANCER_ATTACK_RANGE/3,
            use_team_x_offset=True,
        )
    )
    esper.add_component(entity, RangeIndicator(ranges=[gc.SKELETON_NECROMANCER_ATTACK_RANGE]))
    # Cooldown and batch size from game constants
    if unit_type == UnitType.SKELETON_ARCHER_NECROMANCER:
        summon_cooldown = gc.SKELETON_ARCHER_NECROMANCER_COOLDOWN
        batch_size = gc.SKELETON_ARCHER_NECROMANCER_BATCH_SIZE
    elif unit_type == UnitType.SKELETON_HORSEMAN_NECROMANCER:
        summon_cooldown = gc.SKELETON_HORSEMAN_NECROMANCER_COOLDOWN
        batch_size = gc.SKELETON_HORSEMAN_NECROMANCER_BATCH_SIZE
    elif unit_type == UnitType.SKELETON_MAGE_NECROMANCER:
        summon_cooldown = gc.SKELETON_MAGE_NECROMANCER_COOLDOWN
        batch_size = gc.SKELETON_MAGE_NECROMANCER_BATCH_SIZE
    else:
        summon_cooldown = gc.SKELETON_SWORDSMAN_NECROMANCER_COOLDOWN
        batch_size = gc.SKELETON_SWORDSMAN_NECROMANCER_BATCH_SIZE
    esper.add_component(
        entity,
        Abilities(
            abilities=[
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        Cooldown(duration=summon_cooldown),
                        HasTarget(
                            unit_condition=All([
                                Alive(), # Just to prevent constant summoning after all enemies are dead.
                            ])
                        )
                    ],
                    persistent_conditions=[],
                    effects={
                        0: [
                            PlaySound(SoundEffect(filename="skeleton_spawn.wav", volume=0.1)),
                        ],
                        5: [
                            CreatesUnit(
                                recipient=Recipient.OWNER,
                                unit_type=summoned_type,
                                team=team,
                                offset=(gc.SKELETON_NECROMANCER_SUMMON_OFFSET_X, 0),
                                corruption_powers=corruption_powers,
                                batch_size=batch_size,
                                batch_spacing=gc.UNIT_PLACEMENT_MINIMUM_DISTANCE,
                            ),
                            PlaySound(SoundEffect(filename="necromancer_summon.wav", volume=0.1)),
                        ],
                    },
                )
            ]
        )
    )
    esper.add_component(entity, get_unit_sprite_sheet(unit_type, tier))
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
            ])]
            for frame in [1, 4]
        },
    }))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(OLD_MALE_DEATH_SOUNDS)
    return entity

def create_skeleton_archer_necromancer(x: int, y: int, team: TeamType, corruption_powers: Optional[List[CorruptionPower]], tier: UnitTier, play_spawning: bool = False, orientation: Optional[FacingDirection] = None) -> int:
    return _create_skeleton_necromancer(x, y, team, corruption_powers, tier, UnitType.SKELETON_ARCHER_NECROMANCER, UnitType.SKELETON_ARCHER, play_spawning, orientation)

def create_skeleton_horseman_necromancer(x: int, y: int, team: TeamType, corruption_powers: Optional[List[CorruptionPower]], tier: UnitTier, play_spawning: bool = False, orientation: Optional[FacingDirection] = None) -> int:
    return _create_skeleton_necromancer(x, y, team, corruption_powers, tier, UnitType.SKELETON_HORSEMAN_NECROMANCER, UnitType.SKELETON_HORSEMAN, play_spawning, orientation)

def create_skeleton_mage_necromancer(x: int, y: int, team: TeamType, corruption_powers: Optional[List[CorruptionPower]], tier: UnitTier, play_spawning: bool = False, orientation: Optional[FacingDirection] = None) -> int:
    return _create_skeleton_necromancer(x, y, team, corruption_powers, tier, UnitType.SKELETON_MAGE_NECROMANCER, UnitType.SKELETON_MAGE, play_spawning, orientation)

def create_skeleton_swordsman_necromancer(x: int, y: int, team: TeamType, corruption_powers: Optional[List[CorruptionPower]], tier: UnitTier, play_spawning: bool = False, orientation: Optional[FacingDirection] = None) -> int:
    return _create_skeleton_necromancer(x, y, team, corruption_powers, tier, UnitType.SKELETON_SWORDSMAN_NECROMANCER, UnitType.SKELETON_SWORDSMAN, play_spawning, orientation)

def create_skeleton_lich(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a skeleton lich entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.SKELETON_LICH,
        movement_speed=gc.SKELETON_LICH_MOVEMENT_SPEED,
        health=gc.SKELETON_LICH_HP,
        hitbox=Hitbox(
            width=16,
            height=32,
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    
    # Targeting strategy for corpses
    target_corpse_strategy = TargetStrategy(
        rankings=[
            WeightedRanking(
                rankings={
                    ByDistance(entity=entity, y_bias=None, ascending=True): 1,
                    ConditionPenalty(condition_to_check=HasStatusEffect(ReviveProgress), value=-100): 1,
                },
            ),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.USABLE_CORPSES
    )
    
    esper.add_component(
        entity,
        Destination(target_strategy=target_corpse_strategy, x_offset=0)
    )
    
    esper.add_component(entity, RangeIndicator(ranges=[gc.SKELETON_LICH_ABILITY_RANGE]))
    
    # Revive ability
    esper.add_component(
        entity,
        Abilities(
            abilities=[
                Ability(
                    target_strategy=target_corpse_strategy,
                    trigger_conditions=[
                        HasTarget(
                            unit_condition=All([
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.SKELETON_LICH_ABILITY_RANGE,
                                    y_bias=None
                                ),
                                HasComponent(component=SpriteSheet),
                            ])
                        ),
                    ],
                    persistent_conditions=[
                        SatisfiesUnitCondition(HasComponent(component=SpriteSheet)),
                    ],
                    effects={
                        2: [
                            AppliesStatusEffect(
                                status_effect=ReviveProgress(
                                    time_remaining=15.0,
                                    stacks=50,
                                    team=team,
                                    tier=tier,
                                    corruption_powers=corruption_powers,
                                    owner=entity
                                ),
                                recipient=Recipient.TARGET
                            ),
                            CreatesVisual(
                                recipient=Recipient.TARGET,
                                visual=Visual.Healing,
                                animation_duration=1.0,
                                scale=1.0,
                                duration=1.0
                            ),
                            PlaySound(SoundEffect(filename="skeleton_lich_spell.wav", volume=0.2)),
                            PlaySound(SoundEffect(filename="skeleton_lich_fire.wav", volume=0.5)),
                        ]
                    },
                ),
            ]
        )
    )
    
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.SKELETON_LICH, tier))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(SKELETON_DEATH_SOUNDS)
    esper.add_component(entity, UnusableCorpse())
    return entity

def create_infantry_banner_bearer(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a banner bearer entity with all necessary components."""
    # Calculate tier-specific health
    infantry_banner_bearer_health = gc.INFANTRY_BANNER_BEARER_HP
    
    # Advanced tier: 50% more health
    if tier == UnitTier.ADVANCED:
        infantry_banner_bearer_health = infantry_banner_bearer_health * 1.5
    
    # Elite tier: 100% more health total
    elif tier == UnitTier.ELITE:
        infantry_banner_bearer_health = infantry_banner_bearer_health * 2.0
    
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.INFANTRY_BANNER_BEARER,
        movement_speed=gc.INFANTRY_BANNER_BEARER_AURA_MOVEMENT_SPEED,
        health=infantry_banner_bearer_health,
        hitbox=Hitbox(
            width=16,
            height=36,
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    esper.add_component(entity, Follower())
    targetting_strategy = TargetStrategy(
        rankings=[
            WeightedRanking(
                rankings={
                    ByDistance(entity=entity, y_bias=None, ascending=True): 1,
                    ConditionPenalty(condition_to_check=RememberedBy(entity=entity), value=-10000): 1,
                }
            ),
        ],
        unit_condition=Not(HasComponent(component=Follower)),
        targetting_group=TargetingGroup.TEAM1_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM2_LIVING_VISIBLE
    )
    esper.add_component(
        entity,
        Destination(
            target_strategy=targetting_strategy,
            x_offset=gc.INFANTRY_BANNER_BEARER_AURA_RADIUS/3,
            use_team_x_offset=True,
        )
    )
    esper.add_component(
        entity,
        InstantAbilities(
            abilities=[
                InstantAbility(
                    target_strategy=targetting_strategy,
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
                        RememberTarget(recipient=Recipient.OWNER),
                    ]
                )
            ]
        )
    )
    # Build aura effects based on tier
    aura_effects = [
        # All tiers get movement speed buff
        AppliesStatusEffect(
            status_effect=InfantryBannerBearerMovementSpeedBuff(time_remaining=gc.DEFAULT_AURA_PERIOD, owner=entity),
            recipient=Recipient.TARGET
        )
    ]
    
    # Advanced and Elite tiers get damage buff back
    if tier == UnitTier.ADVANCED or tier == UnitTier.ELITE:
        aura_effects.append(
            AppliesStatusEffect(
                status_effect=InfantryBannerBearerEmpowered(time_remaining=gc.DEFAULT_AURA_PERIOD, owner=entity),
                recipient=Recipient.TARGET
            )
        )
    
    # Elite tier gets attack speed buff
    if tier == UnitTier.ELITE:
        aura_effects.append(
            AppliesStatusEffect(
                status_effect=InfantryBannerBearerAttackSpeedBuff(time_remaining=gc.DEFAULT_AURA_PERIOD, owner=entity),
                recipient=Recipient.TARGET
            )
        )
    
    # Create the auras component and add the banner bearer aura
    auras = Auras()
    banner_aura = Aura(
        owner=entity,
        radius=gc.INFANTRY_BANNER_BEARER_AURA_RADIUS,
        effects=aura_effects,
        period=gc.DEFAULT_AURA_PERIOD,
        owner_condition=Alive(),
        unit_condition=All([
            OnTeam(team=team),
            Alive()
        ]),
        color=(255, 215, 0),
        duration=float('inf')  # Permanent
    )
    auras.auras.append(banner_aura)
    esper.add_component(entity, auras)
    esper.add_component(entity, SmoothMovement())
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.INFANTRY_BANNER_BEARER, tier))
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            0: [PlaySound(SoundEffect("bannerbearer_drum_1.wav", volume=0.5, channel="drum"))],
            3: [PlaySound(SoundEffect("bannerbearer_drum_2.wav", volume=0.5, channel="drum"))],
        },
        AnimationType.IDLE: {
            0: [PlaySound(SoundEffect("bannerbearer_drum_1.wav", volume=0.5, channel="drum"))],
            2: [PlaySound(SoundEffect("bannerbearer_drum_2.wav", volume=0.5, channel="drum"))],
        },
    }))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(MALE_DEATH_SOUNDS)
    return entity

def create_crusader_black_knight(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a black knight entity with all necessary components."""
    # Calculate tier-specific values
    black_knight_health = gc.CRUSADER_BLACK_KNIGHT_HP
    black_knight_movement_speed = gc.CRUSADER_BLACK_KNIGHT_MOVEMENT_SPEED
    black_knight_damage = gc.CRUSADER_BLACK_KNIGHT_ATTACK_DAMAGE
    
    # Advanced tier (and Elite): 30% more health and speed
    if tier == UnitTier.ADVANCED or tier == UnitTier.ELITE:
        black_knight_health = black_knight_health * 1.3
        black_knight_movement_speed = black_knight_movement_speed * 1.3
    
    # Elite tier: 60% more damage
    if tier == UnitTier.ELITE:
        black_knight_damage = black_knight_damage * 1.6
    
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CRUSADER_BLACK_KNIGHT,
        movement_speed=black_knight_movement_speed,
        health=black_knight_health,
        hitbox=Hitbox(
            width=30,
            height=54,
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    
    # Add OnKillEffects component for black knight fear
    esper.add_component(
        entity,
        OnKillEffects(
            effects=[
                CreatesVisualAoE(
                    effects=[
                        AppliesStatusEffect(
                            status_effect=Fleeing(
                                time_remaining=gc.CRUSADER_BLACK_KNIGHT_FLEE_DURATION,
                                entity=entity,
                                owner=entity
                            ),
                            recipient=Recipient.TARGET
                        ),
                        CreatesAttachedVisual(
                            recipient=Recipient.TARGET,
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
                    location=Recipient.TARGET,
                ),
                PlaySound(SoundEffect(filename="black_knight_screech.wav", volume=0.50)),
            ]
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
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.CRUSADER_BLACK_KNIGHT_ATTACK_RANGE*2/3)
    )
    esper.add_component(entity, Armor(level=ArmorLevel.NORMAL))
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
                            damage=black_knight_damage,
                            recipient=Recipient.TARGET
                        ),
                        PlaySound([
                            (SoundEffect(filename=f"sword_swoosh{i+1}.wav", volume=0.50), 1.0) for i in range(3)
                        ]),
                    ]},
                )
            ]
        )
    )
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.CRUSADER_BLACK_KNIGHT, tier))
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"horse_footsteps_grass{i+1}.wav", volume=0.15), 1.0) for i in range(4)
            ])]
            for frame in [3]
        },
    }))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(HORSE_DEATH_SOUNDS)
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(FEMALE_DEATH_SOUNDS)
    return entity

def create_infantry_catapult(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a catapult entity with all necessary components."""
    # Calculate tier-specific values
    catapult_health = gc.INFANTRY_CATAPULT_HP
    catapult_damage = gc.INFANTRY_CATAPULT_DAMAGE
    catapult_min_range = gc.INFANTRY_CATAPULT_MINIMUM_RANGE
    catapult_max_range = gc.INFANTRY_CATAPULT_MAXIMUM_RANGE
    
    # Advanced tier (and Elite): 25% more health and damage
    if tier == UnitTier.ADVANCED or tier == UnitTier.ELITE:
        catapult_health = catapult_health * 1.25
        catapult_damage = catapult_damage * 1.25
    
    # Elite tier: 25% reduced minimum range
    if tier == UnitTier.ELITE:
        catapult_min_range = catapult_min_range * 0.75
    
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.INFANTRY_CATAPULT,
        movement_speed=0,
        health=catapult_health,
        hitbox=Hitbox(
            width=100,
            height=20,
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    # Add permanent immobilization effect
    immobilized_effect = Immobilized(time_remaining=float("inf"), owner=entity)
    esper.component_for_entity(entity, StatusEffects).add(immobilized_effect)
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=All(
            [
                Grounded(),
                MaximumDistanceFromEntity(
                    entity=entity,
                    distance=catapult_max_range,
                    y_bias=None
                ),
                MinimumDistanceFromEntity(
                    entity=entity,
                    distance=catapult_min_range,
                    y_bias=None
                )
            ]
        ),
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
    )
    esper.add_component(entity, Destination(target_strategy=targetting_strategy, x_offset=0))
    esper.add_component(entity, RangeIndicator(ranges=[catapult_min_range, catapult_max_range]))
    esper.add_component(
        entity,
        Abilities(
            abilities=[
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        HasTarget(unit_condition=Always()),
                        Cooldown(gc.INFANTRY_CATAPULT_COOLDOWN),
                    ],
                    persistent_conditions=[
                        HasTarget(unit_condition=All([Alive(), Grounded()]))
                    ],
                    effects={
                        0: [
                            PlaySound(SoundEffect(filename="catapult_firing.wav", volume=0.50)),
                        ],
                        1: [
                            CreatesLobbed(
                                effects=[
                                    CreatesCircleAoE(
                                        effects=[
                                            Damages(damage=catapult_damage, recipient=Recipient.TARGET, is_melee=False)
                                        ],
                                        radius=10 * gc.INFANTRY_CATAPULT_AOE_SCALE,
                                        unit_condition=All([Alive(), Grounded()]),
                                        location=Recipient.PARENT,
                                    ),
                                    CreatesVisual(
                                        recipient=Recipient.PARENT,
                                        visual=Visual.InfantryCatapultBallExplosion,
                                        animation_duration=gc.INFANTRY_CATAPULT_AOE_DURATION,
                                        scale=gc.TINY_RPG_SCALE,
                                        duration=gc.INFANTRY_CATAPULT_AOE_DURATION,
                                        layer=2,
                                    ),
                                    CreatesVisual(
                                        recipient=Recipient.PARENT,
                                        visual=Visual.InfantryCatapultBallRemains,
                                        scale=gc.TINY_RPG_SCALE,
                                        layer=0,
                                        animation_duration=1,
                                    ),
                                    PlaySound(SoundEffect(filename="boulder_impact.wav", volume=0.60)),
                                ],
                                max_range=catapult_max_range,
                                min_range=catapult_min_range,
                                visual=Visual.InfantryCatapultBall,
                                offset=(-50, -65),
                                angular_velocity=3,
                            ),
                        ],
                        4: [
                            PlaySound(SoundEffect(filename="catapult_reload_creak.wav", volume=0.50)),
                        ],
                    }
                )
            ]
        )
    )
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.INFANTRY_CATAPULT, tier))
    esper.add_component(entity, OnDeathEffect(
        [
            PlaySound([
                (SoundEffect(filename=f"catapult_death_{i}.wav", volume=0.07), 1.0) for i in range(3)
            ] + [
                (SoundEffect(filename=f"wilhelm_scream.wav", volume=0.07), gc.WILHELM_CHANCE*3)
            ]),
        ]
    ))
    return entity

def create_crusader_cleric(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a cleric entity with all necessary components."""
    # Calculate tier-specific range
    cleric_range = gc.CRUSADER_CLERIC_ATTACK_RANGE
    
    # Advanced tier (and Elite): 100% increased range
    if tier == UnitTier.ADVANCED or tier == UnitTier.ELITE:
        cleric_range = cleric_range * 2.0
    
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
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    esper.add_component(entity, Follower())
    target_leader = TargetStrategy(
        rankings=[
            WeightedRanking(
                rankings={
                    ByDistance(entity=entity, y_bias=None, ascending=True): 1,
                    ConditionPenalty(condition_to_check=RememberedBy(entity=entity), value=-10000): 1,
                }
            ),
        ],
        unit_condition=Not(HasComponent(component=Follower)),
        targetting_group=TargetingGroup.TEAM1_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM2_LIVING_VISIBLE
    )
    target_ally_to_heal = TargetStrategy(
        rankings=[
            WeightedRanking(
                rankings={
                    ByDistance(entity=entity, y_bias=None, ascending=True): 1,
                    ByMissingHealth(ascending=False): 0.6,
                    ConditionPenalty(condition_to_check=IsEntity(entity=entity), value=10000): 1,
                },
                unit_condition=HealthBelowPercent(percent=1)
            ),
            ByDistance(entity=entity, y_bias=None, ascending=True),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM1_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM2_LIVING_VISIBLE
    )
    esper.add_component(
        entity,
        Destination(
            target_strategy=target_leader,
            x_offset=gc.CRUSADER_CLERIC_ATTACK_RANGE/3,
            use_team_x_offset=True,
        )
    )
    esper.add_component(
        entity,
        RangeIndicator(ranges=[cleric_range])
    )
    esper.add_component(
        entity,
        InstantAbilities(
            abilities=[
                InstantAbility(
                    target_strategy=target_leader,
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
                        RememberTarget(recipient=Recipient.OWNER),
                    ]
                )
            ]
        )
    )
    esper.add_component(
        entity,
        Abilities(
            abilities=[
                Ability(
                    target_strategy=target_ally_to_heal,
                    trigger_conditions=[
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=cleric_range,
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
                                recipient=Recipient.TARGET,
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
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.CRUSADER_CLERIC, tier))
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
            ])]
            for frame in [3, 7]
        },
    }))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(FEMALE_DEATH_SOUNDS)
    return entity

def create_misc_commander(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a commander entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.MISC_COMMANDER,
        movement_speed=gc.MISC_COMMANDER_MOVEMENT_SPEED,
        health=gc.MISC_COMMANDER_HP,
        hitbox=Hitbox(
            width=16,
            height=36,
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.MISC_COMMANDER_ATTACK_RANGE*2/3)
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
                                    distance=gc.MISC_COMMANDER_ATTACK_RANGE,
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
                                    distance=gc.MISC_COMMANDER_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=5
                                ),
                            ])
                        )
                    ],
                    effects={4: [
                        Damages(damage=gc.MISC_COMMANDER_ATTACK_DAMAGE, recipient=Recipient.TARGET, is_melee=True),
                        PlaySound([
                            (SoundEffect(filename=f"sword_swoosh{i+1}.wav", volume=0.50), 1.0) for i in range(3)
                        ]),
                    ]},
                )
            ]
        )
    )
    # Create the auras component and add the commander aura
    auras = Auras()
    commander_aura = Aura(
        owner=entity,
        radius=gc.MISC_COMMANDER_AURA_RADIUS,
        effects=[
            AppliesStatusEffect(
                status_effect=InfantryBannerBearerEmpowered(time_remaining=gc.DEFAULT_AURA_PERIOD, owner=entity),
                recipient=Recipient.TARGET
            ),
        ],
        period=gc.DEFAULT_AURA_PERIOD,
        owner_condition=Alive(),
        unit_condition=All([
            Not(IsEntity(entity=entity)),
            OnTeam(team=team),
            Alive()
        ]),
        color=(255, 215, 0),
        duration=float('inf')  # Permanent
    )
    auras.auras.append(commander_aura)
    esper.add_component(entity, auras)
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.MISC_COMMANDER, tier))
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
            ])]
            for frame in [3, 7]
        },
    }))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(MALE_DEATH_SOUNDS)
    return entity

def create_infantry_crossbowman(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a crossbowman entity with all necessary components."""
    # Calculate tier-specific values
    crossbowman_damage = gc.INFANTRY_CROSSBOWMAN_ATTACK_DAMAGE
    crossbowman_attack_duration = gc.INFANTRY_CROSSBOWMAN_ANIMATION_ATTACK_DURATION
    crossbowman_reload_duration = gc.INFANTRY_CROSSBOWMAN_ANIMATION_RELOAD_DURATION
    
    # Advanced tier (gains heavy armor)
    # Elite tier: 25% increased damage and attack speed
    if tier == UnitTier.ELITE:
        crossbowman_damage = crossbowman_damage * 1.25
        crossbowman_attack_duration = crossbowman_attack_duration * 0.8  # 25% faster = 0.8x duration
        crossbowman_reload_duration = crossbowman_reload_duration * 0.8  # 25% faster = 0.8x duration
    
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.INFANTRY_CROSSBOWMAN,
        movement_speed=gc.INFANTRY_CROSSBOWMAN_MOVEMENT_SPEED,
        health=gc.INFANTRY_CROSSBOWMAN_HP,
        hitbox=Hitbox(
            width=16,
            height=36,
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
    )
    no_target_strategy = TargetStrategy(
        rankings=[ByDistance(entity=entity, y_bias=2, ascending=True)],
        unit_condition=Never(),
        targetting_group=TargetingGroup.EMPTY
    )
    esper.add_component(entity, Destination(target_strategy=targetting_strategy, x_offset=0))
    esper.add_component(
        entity,
        Ammo(
            gc.INFANTRY_CROSSBOWMAN_STARTING_AMMO,
            max=gc.INFANTRY_CROSSBOWMAN_MAX_AMMO
        )
    )
    # Add armor based on tier
    if tier == UnitTier.ADVANCED or tier == UnitTier.ELITE:
        esper.add_component(entity, Armor(level=ArmorLevel.HEAVILY))
    else:
        esper.add_component(entity, Armor(level=ArmorLevel.NORMAL))
    esper.add_component(entity, RangeIndicator(ranges=[gc.INFANTRY_CROSSBOWMAN_ATTACK_RANGE]))
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
                                distance=gc.INFANTRY_CROSSBOWMAN_ATTACK_RANGE,
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
                                distance=gc.INFANTRY_CROSSBOWMAN_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                y_bias=None
                            )
                        ])
                    )
                ],
                effects={
                    2: [
                        CreatesProjectile(
                            projectile_speed=gc.INFANTRY_CROSSBOWMAN_PROJECTILE_SPEED,
                            effects=[
                                Damages(damage=crossbowman_damage, recipient=Recipient.TARGET, is_melee=False),        
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
                    3: [
                        IncreaseAmmo(amount=1),
                        PlaySound(SoundEffect(filename="crossbow_reloading.wav", volume=0.05)),
                    ]
                }
            ),
        ]
    ))
    target_in_range = HasTarget(
        unit_condition=MaximumDistanceFromEntity(
            entity=entity,
            distance=gc.INFANTRY_CROSSBOWMAN_ATTACK_RANGE*1.1,
            y_bias=None
        )
    )
    target_not_in_range = HasTarget(
        unit_condition=MinimumDistanceFromEntity(
            entity=entity,
            distance=gc.INFANTRY_CROSSBOWMAN_ATTACK_RANGE*1.1,
            y_bias=None
        )
    )
    ammo_full = AmmoEquals(gc.INFANTRY_CROSSBOWMAN_MAX_AMMO)
    ammo_not_full = Not(AmmoEquals(gc.INFANTRY_CROSSBOWMAN_MAX_AMMO))
    ammo_empty = AmmoEquals(0)
    ammo_not_empty = Not(AmmoEquals(0))
    esper.add_component(entity, InstantAbilities(
        abilities=[
            # Switch to firing if ammo is full, or ammo is not empty and target in range
            # ammo is full
            InstantAbility(
                target_strategy=no_target_strategy,
                trigger_conditions=[
                    SatisfiesUnitCondition(
                        All([
                            InStance(RELOADING),
                            ammo_full,
                        ])
                    ),
                ],
                effects=[
                    StanceChange(stance=FIRING),
                ],
            ),
            # ammo is not empty, and target in range
            InstantAbility(
                target_strategy=targetting_strategy,
                trigger_conditions=[
                    SatisfiesUnitCondition(
                        All([
                            InStance(RELOADING),
                            ammo_not_empty,
                        ])
                    ),
                    target_in_range,
                ],
                effects=[StanceChange(stance=FIRING)],
            ),
            # Switch to reloading if ammo is empty, or ammo is not full and target is not in range
            # ammo is empty
            InstantAbility(
                target_strategy=targetting_strategy,
                trigger_conditions=[
                    SatisfiesUnitCondition(
                        All([
                            InStance(FIRING),
                            ammo_empty,
                        ])
                    ),
                ],
                effects=[
                    StanceChange(stance=RELOADING),
                ],
            ),
            # ammo is not full, and target is not in range
            InstantAbility(
                target_strategy=targetting_strategy,
                trigger_conditions=[
                    SatisfiesUnitCondition(
                        All([
                            InStance(FIRING),
                            ammo_not_full,
                        ])
                    ),
                    target_not_in_range,
                ],
                effects=[StanceChange(stance=RELOADING)],
            ),
        ]
    ))
    esper.add_component(
        entity,
        get_unit_sprite_sheet(UnitType.INFANTRY_CROSSBOWMAN, tier)
    )
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"armored_grass_footstep{i+1}.wav", volume=0.25), 1.0) for i in range(5)
            ])]
            for frame in [1, 5]
        },
    }))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(MALE_DEATH_SOUNDS)
    return entity

def create_core_defender(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a defender entity with all necessary components."""
    # Calculate tier-specific values
    defender_health = gc.CORE_DEFENDER_HP
    
    # Advanced tier: 25% more health
    if tier == UnitTier.ADVANCED:
        defender_health = defender_health * 1.25
    
    # Elite tier: 75% more health total
    elif tier == UnitTier.ELITE:
        defender_health = defender_health * 1.75
    
    if tier == UnitTier.ADVANCED or tier == UnitTier.ELITE:
        armor_component = Armor(level=ArmorLevel.HEAVILY)
    else:
        armor_component = Armor(level=ArmorLevel.NORMAL)
    
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CORE_DEFENDER,
        movement_speed=gc.CORE_DEFENDER_MOVEMENT_SPEED,
        health=defender_health,
        hitbox=Hitbox(
            width=16,
            height=32,
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.CORE_DEFENDER_ATTACK_RANGE*2/3)
    )
    esper.add_component(entity, armor_component)
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
                                    distance=gc.CORE_DEFENDER_ATTACK_RANGE,
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
                                    distance=gc.CORE_DEFENDER_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=3
                                ),
                            ])
                        )
                    ],
                    effects={4: [
                        Damages(damage=gc.CORE_DEFENDER_ATTACK_DAMAGE, recipient=Recipient.TARGET, is_melee=True),
                        PlaySound([
                            (SoundEffect(filename=f"sword_swoosh{i+1}.wav", volume=0.50), 1.0) for i in range(3)
                        ]),
                    ]},
                )
            ]
        )
    )
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.CORE_DEFENDER, tier))
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"armored_grass_footstep{i+1}.wav", volume=0.25), 1.0) for i in range(5)
            ])]
            for frame in [1, 5]
        },
    }))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(MALE_DEATH_SOUNDS)
    return entity

def create_crusader_gold_knight(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a gold knight entity with all necessary components."""
    # Calculate tier-specific values
    gold_knight_health = gc.CRUSADER_GOLD_KNIGHT_HP
    gold_knight_damage = gc.CRUSADER_GOLD_KNIGHT_ATTACK_DAMAGE
    gold_knight_healing = gc.CRUSADER_GOLD_KNIGHT_ATTACK_HEAL
    
    # Advanced tier: 20% increased damage, healing, and health
    if tier == UnitTier.ADVANCED:
        gold_knight_health = gold_knight_health * 1.2
        gold_knight_damage = gold_knight_damage * 1.2
        gold_knight_healing = gold_knight_healing * 1.2
    
    # Elite tier: 40% increased damage, healing, and health (total)
    elif tier == UnitTier.ELITE:
        gold_knight_health = gold_knight_health * 1.4
        gold_knight_damage = gold_knight_damage * 1.4
        gold_knight_healing = gold_knight_healing * 1.4
    
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CRUSADER_GOLD_KNIGHT,
        movement_speed=gc.CRUSADER_GOLD_KNIGHT_MOVEMENT_SPEED,
        health=gold_knight_health,
        hitbox=Hitbox(
            width=16,
            height=38,
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.CRUSADER_GOLD_KNIGHT_ATTACK_RANGE*2/3)
    )
    esper.add_component(entity, Armor(level=ArmorLevel.NORMAL))
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
                            CreatesVisualAoE(
                                effects=[
                                    Damages(damage=gold_knight_damage, recipient=Recipient.TARGET, is_melee=True),
                                    Heals(amount=gold_knight_healing, recipient=Recipient.OWNER)
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
                        ],
                        2: [
                            PlaySound(SoundEffect(filename="normal_swoosh.wav", volume=0.2)),
                        ]
                    },
                )
            ]
        )
    )
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.CRUSADER_GOLD_KNIGHT, tier))
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
            ])]
            for frame in [3, 7]
        },
    }))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(MALE_DEATH_SOUNDS)
    return entity

def create_crusader_guardian_angel(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create an angel entity with all necessary components."""
    # Calculate tier-specific healing
    guardian_angel_healing = gc.CRUSADER_GUARDIAN_ANGEL_HEALING
    
    # Advanced tier: 50% increased healing
    if tier == UnitTier.ADVANCED:
        guardian_angel_healing = guardian_angel_healing * 1.5
    
    # Elite tier: 100% increased healing (total)
    elif tier == UnitTier.ELITE:
        guardian_angel_healing = guardian_angel_healing * 2.0
    
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
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    esper.add_component(entity, SmoothMovement())
    esper.add_component(entity, Follower())
    targetting_strategy = TargetStrategy(
        rankings=[
            WeightedRanking(
                rankings={
                    ByDistance(entity=entity, y_bias=None, ascending=True): 1,
                    ConditionPenalty(condition_to_check=RememberedBy(entity=entity), value=-10000): 1,
                }
            ),
        ],
        unit_condition=Not(HasComponent(component=Follower)),
        targetting_group=TargetingGroup.TEAM1_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM2_LIVING_VISIBLE
    )
    esper.add_component(
        entity,
        Destination(
            target_strategy=targetting_strategy,
            x_offset=gc.CRUSADER_GUARDIAN_ANGEL_ATTACHMENT_RANGE,
            use_team_x_offset=True,
        )
    )
    esper.add_component(entity, NoNudge())
    esper.add_component(
        entity,
        InstantAbilities(
            abilities=[
                InstantAbility(
                    target_strategy=targetting_strategy,
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
                        RememberTarget(recipient=Recipient.OWNER),
                    ]
                ),
                InstantAbility(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        Cooldown(duration=gc.CRUSADER_GUARDIAN_ANGEL_HEAL_COOLDOWN),
                        HasTarget(
                            unit_condition=All([
                                OnTeam(team=team),
                                RememberedBy(entity=entity),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.CRUSADER_GUARDIAN_ANGEL_ATTACHMENT_RANGE*2,
                                    y_bias=None
                                ),
                                Alive()
                            ])
                        )
                    ],
                    effects=[
                        AppliesStatusEffect(
                            status_effect=Healing(time_remaining=gc.CRUSADER_GUARDIAN_ANGEL_HEAL_COOLDOWN, dps=guardian_angel_healing/gc.CRUSADER_GUARDIAN_ANGEL_HEAL_COOLDOWN, owner=entity),
                            recipient=Recipient.TARGET
                        ),
                        CreatesAttachedVisual(
                            recipient=Recipient.TARGET,
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
        get_unit_sprite_sheet(UnitType.CRUSADER_GUARDIAN_ANGEL, tier)
    )
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
            ])]
            for frame in [3, 7]
        },
    }))
    esper.add_component(entity, OnDeathEffect(
        [
            PlaySound([
                (SoundEffect(filename=f"crusader_guardian_angel_death_grunt_{i}.wav", volume=0.07), 1.0) for i in range(3)
            ] + [
                (SoundEffect(filename=f"wilhelm_scream.wav", volume=0.07), gc.WILHELM_CHANCE*3)
            ]),
        ]
    ))
    return entity

def create_crusader_paladin(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a paladin entity with all necessary components."""
    # Calculate tier-specific values
    paladin_damage = gc.CRUSADER_PALADIN_ATTACK_DAMAGE
    paladin_movement_speed = gc.CRUSADER_PALADIN_MOVEMENT_SPEED
    
    # Advanced tier (and Elite): 100% increased damage
    if tier == UnitTier.ADVANCED or tier == UnitTier.ELITE:
        paladin_damage = paladin_damage * 2.0
    
    # Elite tier: 25% increased movement speed
    if tier == UnitTier.ELITE:
        paladin_movement_speed = paladin_movement_speed * 1.25
    
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.CRUSADER_PALADIN,
        movement_speed=paladin_movement_speed,
        health=gc.CRUSADER_PALADIN_HP,
        hitbox=Hitbox(
            width=30,
            height=54,
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.CRUSADER_PALADIN_ATTACK_RANGE*2/3)
    )
    esper.add_component(entity, Armor(level=ArmorLevel.NORMAL))
    esper.add_component(
        entity,
        Abilities(
            abilities=[
                Ability(
                    target_strategy=TargetStrategy(
                        rankings=[ByDistance(entity=entity, y_bias=2, ascending=True)],
                        unit_condition=Never(),
                        targetting_group=TargetingGroup.EMPTY
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
                            Heals(amount=gc.CRUSADER_PALADIN_SKILL_HEAL, recipient=Recipient.OWNER),
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
                        Damages(damage=paladin_damage, recipient=Recipient.TARGET, is_melee=True),
                        PlaySound([
                            (SoundEffect(filename=f"sword_swoosh{i+1}.wav", volume=0.50), 1.0) for i in range(3)
                        ]),
                    ]},
                )
            ]
        )
    )
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.CRUSADER_PALADIN, tier))
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"horse_footsteps_grass{i+1}.wav", volume=0.15), 1.0) for i in range(4)
            ])]
            for frame in [3]
        },
    }))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(HORSE_DEATH_SOUNDS)
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(MALE_DEATH_SOUNDS)
    return entity

def create_infantry_pikeman(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a pikeman entity with all necessary components."""
    # Calculate tier-specific values
    pikeman_health = gc.INFANTRY_PIKEMAN_HP
    pikeman_damage = gc.INFANTRY_PIKEMAN_ATTACK_DAMAGE
    
    # Advanced tier: 30% increased damage, 15% increased health
    if tier == UnitTier.ADVANCED:
        pikeman_damage = pikeman_damage * 1.3
        pikeman_health = pikeman_health * 1.15
    
    # Elite tier: 60% increased damage total, 30% increased health total
    elif tier == UnitTier.ELITE:
        pikeman_damage = pikeman_damage * 1.6
        pikeman_health = pikeman_health * 1.3
    
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.INFANTRY_PIKEMAN,
        movement_speed=gc.INFANTRY_PIKEMAN_MOVEMENT_SPEED,
        health=pikeman_health,
        hitbox=Hitbox(
            width=16,
            height=32,
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.INFANTRY_PIKEMAN_ATTACK_RANGE*4/5)
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
                                    distance=gc.INFANTRY_PIKEMAN_ATTACK_RANGE,
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
                                    distance=gc.INFANTRY_PIKEMAN_ATTACK_RANGE,
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
                                    distance=gc.INFANTRY_PIKEMAN_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE*3,
                                    y_bias=10
                                ),
                            ])
                        ),
                        SatisfiesUnitCondition(unit_condition=InStance(stance=PIKE_DOWN))
                    ],
                    effects={3: [
                        Damages(damage=pikeman_damage, recipient=Recipient.TARGET, is_melee=True),
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
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.INFANTRY_PIKEMAN, tier))
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
            ])]
            for frame in [1, 4]
        },
    }))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(MALE_DEATH_SOUNDS)
    return entity

def create_misc_red_knight(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a red knight entity with all necessary components."""
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.MISC_RED_KNIGHT,
        movement_speed=gc.MISC_RED_KNIGHT_MOVEMENT_SPEED,
        health=gc.MISC_RED_KNIGHT_HP,
        hitbox=Hitbox(
            width=16,
            height=34,
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.MISC_RED_KNIGHT_ATTACK_RANGE*2/3)
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
                                    distance=gc.MISC_RED_KNIGHT_SKILL_RANGE,
                                    y_bias=2
                                ),
                            ])
                        ),
                        Cooldown(duration=gc.MISC_RED_KNIGHT_SKILL_COOLDOWN)
                    ],
                    persistent_conditions=[],
                    effects={7: [
                        CreatesVisualAoE(
                            effects=[
                                Damages(damage=gc.MISC_RED_KNIGHT_SKILL_DAMAGE, recipient=Recipient.TARGET, is_melee=True),
                                AppliesStatusEffect(
                                    status_effect=DamageOverTime(
                                        dps=gc.MISC_RED_KNIGHT_SKILL_IGNITE_DAMAGE/gc.MISC_RED_KNIGHT_SKILL_IGNITED_DURATION,
                                        time_remaining=gc.MISC_RED_KNIGHT_SKILL_IGNITED_DURATION,
                                        owner=entity
                                    ),
                                    recipient=Recipient.TARGET
                                )
                            ],
                            visual=Visual.MiscRedKnightFireSlash,
                            duration=gc.MISC_RED_KNIGHT_SKILL_AOE_DURATION,
                            scale=gc.MISC_RED_KNIGHT_SKILL_AOE_SCALE,
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
                                    distance=gc.MISC_RED_KNIGHT_ATTACK_RANGE,
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
                                    distance=gc.MISC_RED_KNIGHT_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=3
                                )
                            ])
                        )
                    ],
                    effects={
                        3: [
                            Damages(damage=gc.MISC_RED_KNIGHT_ATTACK_DAMAGE, recipient=Recipient.TARGET, is_melee=True),
                            PlaySound([
                                (SoundEffect(filename=f"sword_swoosh{i+1}.wav", volume=0.50), 1.0) for i in range(3)
                            ]),
                        ],
                        7: [
                            Damages(damage=gc.MISC_RED_KNIGHT_ATTACK_DAMAGE, recipient=Recipient.TARGET, is_melee=True),
                            PlaySound([
                                (SoundEffect(filename=f"sword_swoosh{i+1}.wav", volume=0.50), 1.0) for i in range(3)
                            ]),
                        ]
                    },
                )
            ]
        )
    )
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.MISC_RED_KNIGHT, tier))
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
            ])]
            for frame in [3, 7]
        },
    }))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(MALE_DEATH_SOUNDS)
    return entity

def create_infantry_soldier(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a soldier entity with all necessary components."""
    # Calculate tier-specific values
    soldier_health = gc.INFANTRY_SOLDIER_HP
    soldier_melee_damage = gc.INFANTRY_SOLDIER_MELEE_DAMAGE
    soldier_ranged_damage = gc.CORE_ARCHER_ATTACK_DAMAGE
    soldier_ranged_range = gc.INFANTRY_SOLDIER_RANGED_RANGE
    
    # Advanced tier: 20% increased health, damage, and range (bow only)
    if tier == UnitTier.ADVANCED:
        soldier_health = soldier_health * 1.2
        soldier_melee_damage = soldier_melee_damage * 1.2
        soldier_ranged_damage = soldier_ranged_damage * 1.2
        soldier_ranged_range = soldier_ranged_range * 1.2
    
    # Elite tier: 40% increased health, damage, and range (bow only) total
    elif tier == UnitTier.ELITE:
        soldier_health = soldier_health * 1.4
        soldier_melee_damage = soldier_melee_damage * 1.4
        soldier_ranged_damage = soldier_ranged_damage * 1.4
        soldier_ranged_range = soldier_ranged_range * 1.4
    
    MELEE = 0
    RANGED = 1
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.INFANTRY_SOLDIER,
        movement_speed=gc.INFANTRY_SOLDIER_MOVEMENT_SPEED,
        health=soldier_health,
        hitbox=Hitbox(
            width=16,
            height=32,
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.INFANTRY_SOLDIER_MELEE_RANGE*2/3)
    )
    esper.add_component(
        entity,
        RangeIndicator(ranges=[soldier_ranged_range])
    )
    esper.add_component(entity, Stance(stance=RANGED))
    esper.add_component(entity, Armor(level=ArmorLevel.NORMAL))
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
                                    distance=gc.INFANTRY_SOLDIER_SWITCH_STANCE_RANGE + gc.TARGETTING_GRACE_DISTANCE,
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
                                    distance=gc.INFANTRY_SOLDIER_SWITCH_STANCE_RANGE,
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
                                    distance=gc.INFANTRY_SOLDIER_MELEE_RANGE,
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
                                    distance=gc.INFANTRY_SOLDIER_MELEE_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=3
                                ),
                            ])
                        )
                    ],
                    effects={
                        3: [
                            Damages(damage=soldier_melee_damage, recipient=Recipient.TARGET, is_melee=True),
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
                                    distance=soldier_ranged_range,
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
                                    distance=soldier_ranged_range + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=None
                                ),
                                MinimumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.INFANTRY_SOLDIER_SWITCH_STANCE_RANGE,
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
                                    Damages(damage=soldier_ranged_damage, recipient=Recipient.TARGET, is_melee=False),
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
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.INFANTRY_SOLDIER, tier))
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"armored_grass_footstep{i+1}.wav", volume=0.25), 1.0) for i in range(5)
            ])]
            for frame in [3, 7]
        },
    }))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(MALE_DEATH_SOUNDS)
    return entity


def create_pirate_crew(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a pirate crew entity with all necessary components."""
    # Calculate tier-specific values
    pirate_crew_health = gc.PIRATE_CREW_HP
    pirate_crew_damage = gc.PIRATE_CREW_ATTACK_DAMAGE
    pirate_crew_movement_speed = gc.PIRATE_CREW_MOVEMENT_SPEED
    
    # Advanced tier: 25% increased attack and movement speed
    if tier == UnitTier.ADVANCED:
        pirate_crew_movement_speed = pirate_crew_movement_speed * 1.25
    
    # Elite tier: 50% more damage total
    elif tier == UnitTier.ELITE:
        pirate_crew_damage = pirate_crew_damage * 1.5
    
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.PIRATE_CREW,
        movement_speed=pirate_crew_movement_speed,
        health=pirate_crew_health,
        hitbox=Hitbox(
            width=16,
            height=32,
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.PIRATE_CREW_ATTACK_RANGE*2/3)
    )
    esper.add_component(entity, RangeIndicator([gc.PIRATE_CREW_MINIMUM_JUMP_RANGE, gc.PIRATE_CREW_MAXIMUM_JUMP_RANGE]))
    esper.add_component(
        entity,
        Abilities(
            abilities=[
                # Basic melee attack
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                Grounded(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.PIRATE_CREW_ATTACK_RANGE,
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
                                    distance=gc.PIRATE_CREW_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=3
                                ),
                            ])
                        )
                    ],
                    effects={
                        2: [
                            Damages(damage=pirate_crew_damage, recipient=Recipient.TARGET, is_melee=True),
                            PlaySound([
                                (SoundEffect(filename=f"sword_swoosh{i+1}.wav", volume=0.50), 1.0) for i in range(3)
                            ]),
                        ]
                    },
                ),
                # Jump attack ability
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        Cooldown(duration=gc.PIRATE_CREW_JUMP_COOLDOWN),
                        SatisfiesUnitCondition(Grounded()),
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                Grounded(),
                                MinimumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.PIRATE_CREW_MINIMUM_JUMP_RANGE,
                                    y_bias=None
                                ),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.PIRATE_CREW_MAXIMUM_JUMP_RANGE,
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
                                    distance=gc.PIRATE_CREW_MAXIMUM_JUMP_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=None
                                ),
                            ])
                        )
                    ],
                    effects={0: [
                        PlaySound(SoundEffect(filename="pirate_crew_jump.wav", volume=0.50)),
                        Jump(
                            min_range=gc.PIRATE_CREW_MINIMUM_JUMP_RANGE,
                            max_range=gc.PIRATE_CREW_MAXIMUM_JUMP_RANGE,
                            max_angle=gc.PIRATE_CREW_MAXIMUM_JUMP_ANGLE,
                            effects=[
                                CreatesCircleAoE(
                                    radius=gc.PIRATE_CREW_JUMP_RADIUS,
                                    effects=[
                                        Damages(damage=gc.PIRATE_CREW_JUMP_DAMAGE, recipient=Recipient.TARGET, is_melee=True),
                                    ],
                                    unit_condition=All([OnTeam(team=team.other()), Alive(), Grounded()]),
                                    location=Recipient.OWNER,
                                ),
                                PlaySound(SoundEffect(filename="pirate_crew_jump_land.wav", volume=0.50)),
                            ],
                        )
                    ]},
                )
            ]
        )
    )
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.PIRATE_CREW, tier))
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
            ])]
            for frame in [2, 5]
        },
    }))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(MALE_DEATH_SOUNDS)
    return entity

def create_pirate_gunner(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a pirate gunner entity with all necessary components."""
    # Calculate tier-specific values
    pirate_gunner_gun_damage = gc.PIRATE_GUNNER_GUN_DAMAGE
    
    # Advanced tier: 70% increased gun damage
    if tier == UnitTier.ADVANCED:
        pirate_gunner_gun_damage = pirate_gunner_gun_damage * 1.7
    
    # Elite tier: 140% increased gun damage total (70% + 70%)
    elif tier == UnitTier.ELITE:
        pirate_gunner_gun_damage = pirate_gunner_gun_damage * 2.4
    
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.PIRATE_GUNNER,
        movement_speed=gc.PIRATE_GUNNER_MOVEMENT_SPEED,
        health=gc.PIRATE_GUNNER_HP,
        hitbox=Hitbox(
            width=16,
            height=32,
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=0, min_distance=gc.PIRATE_GUNNER_GUN_RANGE)
    )
    esper.add_component(entity, RangeIndicator(ranges=[gc.PIRATE_GUNNER_GUN_RANGE]))
    
    MELEE = 0
    RANGED = 1
    esper.add_component(entity, Stance(stance=RANGED))
    
    esper.add_component(
        entity,
        InstantAbilities(
            abilities=[
                # Switch to ranged stance when enemies move away
                InstantAbility(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        SatisfiesUnitCondition(InStance(stance=MELEE)),
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                MinimumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.PIRATE_GUNNER_SWITCH_STANCE_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=None,
                                ),
                            ])
                        )
                    ],
                    effects=[StanceChange(stance=RANGED)]
                ),
                # Switch to melee stance when enemies get close
                InstantAbility(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        SatisfiesUnitCondition(InStance(stance=RANGED)),
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.PIRATE_GUNNER_SWITCH_STANCE_RANGE,
                                    y_bias=None,
                                ),
                            ])
                        )
                    ],
                    effects=[StanceChange(stance=MELEE)]
                )
            ]
        )
    )
    
    esper.add_component(
        entity,
        Abilities(
            abilities=[
                # Gun attack (ranged long cooldown)
                # Note that unlike some other stance units, they can still use their gun in melee range.
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        Cooldown(duration=gc.PIRATE_GUNNER_GUN_COOLDOWN),
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                Grounded(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.PIRATE_GUNNER_GUN_RANGE,
                                    y_bias=None
                                ),
                            ])
                        )
                    ],
                    persistent_conditions=[
                        HasTarget(
                            unit_condition=All([
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.PIRATE_GUNNER_GUN_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=None
                                ),
                            ])
                        )
                    ],
                    effects={
                        2: [
                            Damages(damage=pirate_gunner_gun_damage, recipient=Recipient.TARGET, is_melee=False),
                            PlaySound(SoundEffect(filename="pirate_gunner_gun.wav", volume=0.75)),
                        ]
                    },
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
                                    distance=gc.PIRATE_GUNNER_MELEE_RANGE,
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
                                    distance=gc.PIRATE_GUNNER_MELEE_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=3
                                ),
                            ])
                        )
                    ],
                    effects={
                        3: [
                            Damages(damage=gc.PIRATE_GUNNER_MELEE_DAMAGE, recipient=Recipient.TARGET, is_melee=True),
                            PlaySound([
                                (SoundEffect(filename=f"sword_swoosh{i+1}.wav", volume=0.50), 1.0) for i in range(3)
                            ]),
                        ]
                    },
                )
            ]
        )
    )
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.PIRATE_GUNNER, tier))
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
            ])]
            for frame in [2, 5]
        },
    }))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(FEMALE_DEATH_SOUNDS)
    return entity

def create_pirate_cannon(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a pirate cannon entity with all necessary components."""
    # Calculate tier-specific values
    cannon_damage = gc.PIRATE_CANNON_DAMAGE
    cannon_range = gc.PIRATE_CANNON_RANGE
    
    # Advanced tier: 50% increased damage
    if tier == UnitTier.ADVANCED:
        cannon_damage = cannon_damage * 1.5
    
    # Elite tier: 100% increased damage total
    elif tier == UnitTier.ELITE:
        cannon_damage = cannon_damage * 2.0
    
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.PIRATE_CANNON,
        movement_speed=gc.PIRATE_CANNON_MOVEMENT_SPEED,
        health=gc.PIRATE_CANNON_HP,
        hitbox=Hitbox(
            width=40,
            height=20,
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
    )
    esper.add_component(entity, Destination(target_strategy=targetting_strategy, x_offset=0, min_distance=cannon_range))
    esper.add_component(entity, RangeIndicator(ranges=[cannon_range]))
    esper.add_component(
        entity,
        Abilities(
            abilities=[
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        Cooldown(duration=gc.PIRATE_CANNON_COOLDOWN),
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                Grounded(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=cannon_range,
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
                                    distance=cannon_range + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=None
                                )
                            ])
                        )
                    ],
                    effects={
                        0: [
                            PlaySound(SoundEffect(filename="pirate_cannon.wav", volume=0.75)),
                            CreatesProjectile(
                                projectile_speed=gc.PIRATE_CANNON_PROJECTILE_SPEED,
                                effects=[
                                    Damages(damage=cannon_damage, recipient=Recipient.TARGET, is_melee=False),
                                ],
                                visual=Visual.PirateCannonBall,
                                projectile_offset_x=5*gc.MINIFOLKS_SCALE,
                                projectile_offset_y=0,
                                unit_condition=All([OnTeam(team=team.other()), Alive(), Grounded()]),
                                pierce=1000,
                            ),


                        ]
                    }
                )
            ]
        )
    )
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.PIRATE_CANNON, tier))
    esper.add_component(entity, OnDeathEffect(
        [
            PlaySound([
                (SoundEffect(filename=f"cannon_death_{i}.wav", volume=0.07), 1.0) for i in range(3)
            ] + [
                (SoundEffect(filename=f"wilhelm_scream.wav", volume=0.07), gc.WILHELM_CHANCE*3)
            ]),
        ]
    ))
    return entity

def create_pirate_captain(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a pirate captain entity with all necessary components."""
    # Calculate tier-specific values
    pirate_captain_gun_damage = gc.PIRATE_CAPTAIN_GUN_DAMAGE
    pirate_captain_melee_damage = gc.PIRATE_CAPTAIN_MELEE_DAMAGE
    pirate_captain_health = gc.PIRATE_CAPTAIN_HP
    
    # Advanced tier: 50% reduced cooldown on gun attack
    gun_cooldown = gc.PIRATE_CAPTAIN_GUN_COOLDOWN
    if tier == UnitTier.ADVANCED:
        gun_cooldown = gun_cooldown * 0.5
    
    # Elite tier: 30% increased damage and health
    if tier == UnitTier.ELITE:
        pirate_captain_gun_damage = pirate_captain_gun_damage * 1.3
        pirate_captain_melee_damage = pirate_captain_melee_damage * 1.3
        pirate_captain_health = pirate_captain_health * 1.3
    
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.PIRATE_CAPTAIN,
        movement_speed=gc.PIRATE_CAPTAIN_MOVEMENT_SPEED,
        health=pirate_captain_health,
        hitbox=Hitbox(
            width=16,
            height=32,
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=0)
    )
    esper.add_component(entity, RangeIndicator(ranges=[gc.PIRATE_CAPTAIN_MAXIMUM_GUN_RANGE]))
    esper.add_component(
        entity,
        Abilities(
            abilities=[
                # Gun attack (ranged, with cooldown)
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        Cooldown(duration=gun_cooldown),
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                Grounded(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.PIRATE_CAPTAIN_MAXIMUM_GUN_RANGE,
                                    y_bias=None
                                ),
                            ])
                        )
                    ],
                    persistent_conditions=[
                        HasTarget(
                            unit_condition=All([
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.PIRATE_CAPTAIN_MAXIMUM_GUN_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=None
                                ),
                            ])
                        )
                    ],
                    effects={
                        3: [
                            Damages(damage=pirate_captain_gun_damage, recipient=Recipient.TARGET, is_melee=False),
                            PlaySound(SoundEffect(filename="pirate_captain_pistol.wav", volume=0.75)),
                        ]
                    },
                ),
                # Melee attack
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                Grounded(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.PIRATE_CAPTAIN_MELEE_RANGE,
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
                                    distance=gc.PIRATE_CAPTAIN_MELEE_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=3
                                ),
                            ])
                        )
                    ],
                    effects={
                        2: [
                            Damages(damage=pirate_captain_melee_damage, recipient=Recipient.TARGET, is_melee=True),
                            PlaySound([
                                (SoundEffect(filename=f"sword_swoosh{i+1}.wav", volume=0.50), 1.0) for i in range(3)
                            ]),
                        ]
                    },
                )
            ]
        )
    )
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.PIRATE_CAPTAIN, tier))
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
            ])]
            for frame in [2, 5]
        },
    }))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(MALE_DEATH_SOUNDS)
    return entity



def create_werebear(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
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
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
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
                    effects={5: [Damages(damage=gc.WEREBEAR_ATTACK_DAMAGE, recipient=Recipient.TARGET, is_melee=True)]},
                )
            ]
        )
    )
    esper.add_component(
        entity,
        get_unit_sprite_sheet(UnitType.WEREBEAR, tier)
    )
    return entity

def create_zombie_basic_zombie(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a zombie entity with all necessary components."""
    # Calculate tier-specific health
    zombie_health = gc.ZOMBIE_BASIC_ZOMBIE_HP
    
    # Advanced tier: 50% increased health
    if tier == UnitTier.ADVANCED:
        zombie_health = zombie_health * 1.5
    
    # Elite tier: 100% increased health total
    elif tier == UnitTier.ELITE:
        zombie_health = zombie_health * 2.0
    
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.ZOMBIE_BASIC_ZOMBIE,
        movement_speed=gc.ZOMBIE_BASIC_ZOMBIE_MOVEMENT_SPEED,
        health=zombie_health,
        hitbox=Hitbox(width=16, height=32),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    
    # Add OnHitEffects component for zombie infection
    esper.add_component(
        entity,
        OnHitEffects(
            effects=[
                AppliesStatusEffect(
                    status_effect=ZombieInfection(time_remaining=gc.ZOMBIE_INFECTION_DURATION, team=team, corruption_powers=corruption_powers, owner=entity),
                    recipient=Recipient.TARGET
                )
            ]
        )
    )
    
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
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
                    effects={1: [
                        Damages(damage=gc.ZOMBIE_BASIC_ZOMBIE_ATTACK_DAMAGE, recipient=Recipient.TARGET, is_melee=True)
                    ]},
                )
            ]
        )
    )
    esper.add_component(entity, UnusableCorpse())
    esper.add_component(
        entity,
        get_unit_sprite_sheet(UnitType.ZOMBIE_BASIC_ZOMBIE, tier)
    )
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
            ])]
            for frame in [1, 3]
        },
    }))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(ZOMBIE_DEATH_SOUNDS)
    return entity

def create_zombie_fighter(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a zombie fighter entity with all necessary components."""
    # Calculate tier-specific health and damage
    fighter_health = gc.ZOMBIE_FIGHTER_HP
    fighter_damage = gc.ZOMBIE_FIGHTER_ATTACK_DAMAGE
    
    # Advanced tier: 30% increased health and damage
    if tier == UnitTier.ADVANCED:
        fighter_health = fighter_health * 1.3
        fighter_damage = fighter_damage * 1.3
    
    # Elite tier: 60% increased health and damage total
    elif tier == UnitTier.ELITE:
        fighter_health = fighter_health * 1.6
        fighter_damage = fighter_damage * 1.6
    
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.ZOMBIE_FIGHTER,
        movement_speed=gc.ZOMBIE_FIGHTER_MOVEMENT_SPEED,
        health=fighter_health,
        hitbox=Hitbox(width=16, height=32),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    
    # Add OnHitEffects component for zombie infection
    esper.add_component(
        entity,
        OnHitEffects(
            effects=[
                AppliesStatusEffect(
                    status_effect=ZombieInfection(time_remaining=gc.ZOMBIE_INFECTION_DURATION, team=team, corruption_powers=corruption_powers, owner=entity),
                    recipient=Recipient.TARGET
                )
            ]
        )
    )
    
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.ZOMBIE_FIGHTER_ATTACK_RANGE*2/3)
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
                                    distance=gc.ZOMBIE_FIGHTER_ATTACK_RANGE,
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
                                    distance=gc.ZOMBIE_FIGHTER_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=3
                                ),
                            ])
                        )
                    ],
                    effects={3: [
                        Damages(damage=fighter_damage, recipient=Recipient.TARGET, is_melee=True)
                    ]},
                )
            ]
        )
    )
    esper.add_component(entity, UnusableCorpse())
    esper.add_component(
        entity,
        get_unit_sprite_sheet(UnitType.ZOMBIE_FIGHTER, tier)
    )
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
            ])]
            for frame in [1, 3]
        },
    }))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(ZOMBIE_DEATH_SOUNDS)
    return entity

def create_misc_brute(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a misc brute entity with all necessary components."""
    # Calculate tier-specific values
    brute_health = gc.MISC_BRUTE_HP
    brute_damage = gc.MISC_BRUTE_ATTACK_DAMAGE
    
    # Advanced tier: 25% increased health and damage
    if tier == UnitTier.ADVANCED:
        brute_health = brute_health * 1.25
        brute_damage = brute_damage * 1.25
    
    # Elite tier: 50% increased health and damage total
    elif tier == UnitTier.ELITE:
        brute_health = brute_health * 1.5
        brute_damage = brute_damage * 1.5
    
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.MISC_BRUTE,
        movement_speed=gc.MISC_BRUTE_MOVEMENT_SPEED,
        health=brute_health,
        hitbox=Hitbox(width=24, height=48),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.MISC_BRUTE_ATTACK_RANGE*2/3)
    )
    esper.add_component(entity, Ammo(1, 1))
    
    # Add on death effect to spawn zombies if ammo is 1
    # TODO: Add on death sounds (right now can't use different conditions for each effect)
    esper.add_component(
        entity,
        OnDeathEffect(
            effects=[
                CreatesUnit(
                    unit_type=UnitType.ZOMBIE_BASIC_ZOMBIE,
                    team=team,
                    offset=(0, 10),
                    recipient=Recipient.OWNER,
                    corruption_powers=corruption_powers,
                ),
                CreatesUnit(
                    unit_type=UnitType.ZOMBIE_BASIC_ZOMBIE,
                    team=team,
                    offset=(0, -10),
                    recipient=Recipient.OWNER,
                    corruption_powers=corruption_powers,
                ),
            ],
            condition=AmmoEquals(1)
        )
    )
    
    esper.add_component(
        entity,
        Abilities(
            abilities=[
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        SatisfiesUnitCondition(Not(AmmoEquals(0))),
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.MISC_BRUTE_ZOMBIE_DROP_RANGE,
                                    y_bias=None,
                                ),
                            ])
                        )
                    ],
                    persistent_conditions=[],
                    effects={
                        3: [
                            CreatesUnit(
                                unit_type=UnitType.ZOMBIE_BASIC_ZOMBIE,
                                team=team,
                                offset=(0, 10),
                                recipient=Recipient.OWNER,
                                corruption_powers=corruption_powers,
                            ),
                            CreatesUnit(
                                unit_type=UnitType.ZOMBIE_BASIC_ZOMBIE,
                                team=team,
                                offset=(0, -10),
                                recipient=Recipient.OWNER,
                                corruption_powers=corruption_powers,
                            ),
                            IncreaseAmmo(amount=-1),
                        ],
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
                                    distance=gc.MISC_BRUTE_ATTACK_RANGE,
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
                                    distance=gc.MISC_BRUTE_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=3
                                ),
                            ])
                        )
                    ],
                    effects={3: [
                        Damages(damage=brute_damage, recipient=Recipient.TARGET, is_melee=True),
                        AppliesStatusEffect(
                            status_effect=ZombieInfection(time_remaining=gc.ZOMBIE_INFECTION_DURATION, team=team, corruption_powers=corruption_powers, owner=entity),
                            recipient=Recipient.TARGET
                        )
                    ]},
                )
            ]
        )
    )
    esper.add_component(entity, UnusableCorpse())
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.MISC_BRUTE, tier))
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
            ])]
            for frame in [1, 3]
        },
    }))
    return entity

def create_zombie_jumper(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a jumper zombie entity with all necessary components."""
    # Calculate tier-specific values
    jumper_health = gc.ZOMBIE_JUMPER_HP
    jumper_movement_speed = gc.ZOMBIE_JUMPER_MOVEMENT_SPEED
    
    # Advanced tier: 30% more health, 15% more movement speed
    if tier == UnitTier.ADVANCED:
        jumper_health = jumper_health * 1.3
        jumper_movement_speed = jumper_movement_speed * 1.15
    
    # Elite tier: 60% more health total, 30% more movement speed total
    elif tier == UnitTier.ELITE:
        jumper_health = jumper_health * 1.6
        jumper_movement_speed = jumper_movement_speed * 1.3
    
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.ZOMBIE_JUMPER,
        movement_speed=jumper_movement_speed,
        health=jumper_health,
        hitbox=Hitbox(width=32, height=28),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    
    # Add OnHitEffects component for zombie infection
    esper.add_component(
        entity,
        OnHitEffects(
            effects=[
                AppliesStatusEffect(
                    status_effect=ZombieInfection(time_remaining=gc.ZOMBIE_INFECTION_DURATION, team=team, corruption_powers=corruption_powers, owner=entity),
                    recipient=Recipient.TARGET
                )
            ]
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
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
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
                    effects={2: [
                        Damages(damage=gc.ZOMBIE_JUMPER_ATTACK_DAMAGE, recipient=Recipient.TARGET, is_melee=True)
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
    esper.add_component(entity, UnusableCorpse())
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.ZOMBIE_JUMPER, tier))
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
            ])]
            for frame in [1, 3]
        },
    }))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(ZOMBIE_DEATH_SOUNDS)
    return entity

def create_zombie_spitter(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a spitter entity with all necessary components."""
    # Calculate tier-specific damage values
    spitter_damage = gc.ZOMBIE_SPITTER_RANGED_ATTACK_DAMAGE
    melee_damage = gc.ZOMBIE_SPITTER_MELEE_ATTACK_DAMAGE
    
    # Advanced tier: 50% increased damage
    if tier == UnitTier.ADVANCED:
        spitter_damage = spitter_damage * 1.5
        melee_damage = melee_damage * 1.5
    
    # Elite tier: 100% increased damage total
    elif tier == UnitTier.ELITE:
        spitter_damage = spitter_damage * 2.0
        melee_damage = melee_damage * 2.0
    
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
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    
    # Add OnHitEffects component for zombie infection
    esper.add_component(
        entity,
        OnHitEffects(
            effects=[
                AppliesStatusEffect(
                    status_effect=ZombieInfection(time_remaining=gc.ZOMBIE_INFECTION_DURATION, team=team, corruption_powers=corruption_powers, owner=entity),
                    recipient=Recipient.TARGET
                )
            ]
        )
    )
    
    targetting_strategy = TargetStrategy(
        rankings=[
            WeightedRanking(
                rankings={
                    ByDistance(entity=entity, y_bias=2, ascending=True): 1,
                    ConditionPenalty(condition_to_check=Infected(), value=300): 1,
                },
                ascending=True,
            ),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=0)
    )
    esper.add_component(entity, RangeIndicator(ranges=[gc.ZOMBIE_SPITTER_RANGED_ATTACK_RANGE]))
    esper.add_component(entity, UnusableCorpse())
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
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.ZOMBIE_SPITTER_RANGED_ATTACK_RANGE,
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
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.ZOMBIE_SPITTER_RANGED_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=None
                                )
                            ])
                        )
                    ],
                    effects={
                        2: [
                            CreatesProjectile(
                                projectile_speed=gc.ZOMBIE_SPITTER_PROJECTILE_SPEED,
                                effects=[
                                    AppliesStatusEffect(
                                        status_effect=DamageOverTime(
                                            time_remaining=gc.ZOMBIE_INFECTION_DURATION,
                                            dps=spitter_damage/gc.ZOMBIE_INFECTION_DURATION,
                                            owner=entity
                                        ),
                                        recipient=Recipient.TARGET
                                    ),
                                    AppliesStatusEffect(
                                        status_effect=ZombieInfection(
                                            time_remaining=gc.ZOMBIE_INFECTION_DURATION,
                                            team=team,
                                            corruption_powers=corruption_powers,
                                            owner=entity
                                        ),
                                        recipient=Recipient.TARGET
                                    )
                                ],
                                visual=Visual.ZombieSpit,
                                projectile_offset_x=5*gc.MINIFOLKS_SCALE,
                                projectile_offset_y=0,
                                unit_condition=All([OnTeam(team=team.other()), Alive(), Grounded(), Not(Infected())]),
                            ),
                            PlaySound([
                                (SoundEffect(filename=f"zombie_spitter_attack.wav", volume=0.20), 1.0) for i in range(3)
                            ]),
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
                                    distance=gc.ZOMBIE_SPITTER_MELEE_ATTACK_RANGE,
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
                                    distance=gc.ZOMBIE_SPITTER_MELEE_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=3
                                ),
                            ])
                        )
                    ],
                    effects={1: [
                        Damages(damage=melee_damage/2, recipient=Recipient.TARGET, is_melee=True),
                        Damages(damage=melee_damage/2, recipient=Recipient.TARGET, is_melee=True)
                    ]},
                )
            ]
        )
    )
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(ZOMBIE_DEATH_SOUNDS)
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.ZOMBIE_SPITTER, tier))
    return entity

def create_zombie_tank(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a tank zombie entity with all necessary components."""
    # Calculate tier-specific health
    tank_health = gc.ZOMBIE_TANK_HP
    
    # Advanced tier: 50% increased health
    if tier == UnitTier.ADVANCED:
        tank_health = tank_health * 1.5
    
    # Elite tier: 100% increased health total
    elif tier == UnitTier.ELITE:
        tank_health = tank_health * 2.0
    
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.ZOMBIE_TANK,
        movement_speed=gc.ZOMBIE_TANK_MOVEMENT_SPEED,
        health=tank_health,
        hitbox=Hitbox(width=40, height=44),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    
    # Add OnHitEffects component for zombie infection
    esper.add_component(
        entity,
        OnHitEffects(
            effects=[
                AppliesStatusEffect(
                    status_effect=ZombieInfection(time_remaining=gc.ZOMBIE_INFECTION_DURATION, team=team, corruption_powers=corruption_powers, owner=entity),
                    recipient=Recipient.TARGET
                )
            ]
        )
    )
    
    targetting_strategy = TargetStrategy(
        rankings=[
            ByDistance(entity=entity, y_bias=2, ascending=True),
        ],
        unit_condition=None,
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
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
                        Damages(damage=gc.ZOMBIE_TANK_ATTACK_DAMAGE, recipient=Recipient.TARGET, is_melee=True)
                    ]},
                )
            ]
        )
    )
    esper.add_component(entity,
        OnDeathEffect(
            [
                PlaySound([
                    (SoundEffect(filename=f"tank_zombie_grunt_{i}.wav", volume=0.07), 1.0) for i in range(3)
                ] + [
                    (SoundEffect(filename=f"wilhelm_scream.wav", volume=0.07), gc.WILHELM_CHANCE*3)
                ]),
            ]
        )
    )
    esper.add_component(entity, UnusableCorpse())
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.ZOMBIE_TANK, tier))
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
            ])]
            for frame in [1, 3]
        },
    }))
    return entity

def create_misc_grabber(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a grabber entity with all necessary components."""
    # Calculate tier-specific values
    grabber_health = gc.MISC_GRABBER_HP
    grab_damage = gc.MISC_GRABBER_GRAB_DAMAGE
    melee_damage = gc.ZOMBIE_BASIC_ZOMBIE_ATTACK_DAMAGE
    
    # Advanced tier: 50% increased health and damage
    if tier == UnitTier.ADVANCED:
        grabber_health = grabber_health * 1.5
        grab_damage = grab_damage * 1.5
        melee_damage = melee_damage * 1.5
    
    # Elite tier: 100% increased health and damage total
    elif tier == UnitTier.ELITE:
        grabber_health = grabber_health * 2.0
        grab_damage = grab_damage * 2.0
        melee_damage = melee_damage * 2.0
    
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.MISC_GRABBER,
        movement_speed=gc.MISC_GRABBER_MOVEMENT_SPEED,
        health=grabber_health,
        hitbox=Hitbox(
            width=16,
            height=32,
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            WeightedRanking(
                rankings={
                    ByDistance(entity=entity, y_bias=2, ascending=True): 1,
                },
                ascending=True,
            ),
        ],
        unit_condition=Not(HasStatusEffect(Immobilized)),
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=0)
    )
    esper.add_component(entity, RangeIndicator(ranges=[gc.MISC_GRABBER_GRAB_MINIMUM_RANGE, gc.MISC_GRABBER_GRAB_MAXIMUM_RANGE]))
    esper.add_component(entity, UnusableCorpse())
    esper.add_component(
        entity,
        Abilities(
            abilities=[
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        SatisfiesUnitCondition(
                            unit_condition=RememberedSatisfies(
                                condition=Any([
                                    HasComponent(ForcedMovement),
                                    HasComponent(Projectile),
                                ])
                            )
                        )
                    ],
                    persistent_conditions=[
                        SatisfiesUnitCondition(
                            unit_condition=RememberedSatisfies(
                                condition=Any([
                                    HasComponent(ForcedMovement),
                                    HasComponent(Projectile),
                                ])
                            )
                        )
                    ],
                    effects={},
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
                                    distance=gc.MISC_GRABBER_GRAB_MAXIMUM_RANGE,
                                    y_bias=None
                                ),
                                MinimumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.MISC_GRABBER_GRAB_MINIMUM_RANGE,
                                    y_bias=None
                                )
                            ])
                        ),
                        Cooldown(duration=gc.MISC_GRABBER_GRAB_COOLDOWN),
                    ],
                    persistent_conditions=[],
                    effects={
                        3: [
                            CreatesProjectile(
                                projectile_speed=gc.MISC_GRABBER_GRAB_PROJECTILE_SPEED,
                                effects=[
                                    RememberTarget(recipient=Recipient.OWNER),
                                    Damages(damage=grab_damage, recipient=Recipient.TARGET, is_melee=True),
                                    AppliesStatusEffect(
                                        status_effect=ZombieInfection(time_remaining=gc.ZOMBIE_INFECTION_DURATION, team=team, corruption_powers=corruption_powers, owner=entity),
                                        recipient=Recipient.TARGET
                                    ),
                                    AddsForcedMovement(
                                        recipient=Recipient.TARGET,
                                        destination=Recipient.OWNER,
                                        speed=gc.MISC_GRABBER_GRAB_FORCED_MOVEMENT_SPEED,
                                        offset_x=30,
                                        offset_y=0,
                                    ),
                                    CreatesVisualLink(
                                        start_entity=Recipient.TARGET,
                                        other_entity=Recipient.OWNER,
                                        visual=Visual.Tongue,
                                        tile_size=4,
                                        entity_delete_condition=Not(HasComponent(ForcedMovement)),
                                    )
                                ],
                                visual=Visual.TongueTip,
                                projectile_offset_x=5*gc.MINIFOLKS_SCALE,
                                projectile_offset_y=0,
                                unit_condition=All([OnTeam(team=team.other()), Alive(), Grounded()]),
                                max_distance=gc.MISC_GRABBER_GRAB_MAXIMUM_RANGE,
                                on_create=lambda projectile: (
                                    esper.add_component(entity, EntityMemory(projectile)),
                                    esper.add_component(entity, VisualLink(
                                        other_entity=projectile,
                                        visual=Visual.Tongue,
                                        tile_size=4,
                                    )),
                                ),
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
                        Damages(damage=melee_damage, recipient=Recipient.TARGET, is_melee=True),
                        AppliesStatusEffect(
                            status_effect=ZombieInfection(time_remaining=gc.ZOMBIE_INFECTION_DURATION, team=team, corruption_powers=corruption_powers, owner=entity),
                            recipient=Recipient.TARGET
                        )
                    ]},
                )
            ]
        )
    )
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(ZOMBIE_DEATH_SOUNDS)
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.MISC_GRABBER, tier))
    return entity

def create_pirate_harpooner(
        x: int,
        y: int,
        team: TeamType,
        corruption_powers: Optional[List[CorruptionPower]],
        tier: UnitTier,
        play_spawning: bool = False,
        orientation: Optional[FacingDirection] = None,
    ) -> int:
    """Create a pirate harpooner entity with all necessary components."""
    # Calculate tier-specific values
    harpooner_health = gc.PIRATE_HARPOONER_HP
    harpoon_damage = gc.PIRATE_HARPOONER_HARPOON_DAMAGE
    melee_damage = gc.PIRATE_HARPOONER_ATTACK_DAMAGE
    harpoon_cooldown = gc.PIRATE_HARPOONER_HARPOON_COOLDOWN
    
    # Advanced tier: 50% cooldown recovery (faster cooldown)
    if tier == UnitTier.ADVANCED:
        harpoon_cooldown = harpoon_cooldown * 0.5
    
    # Elite tier: 25% increased attack damage and health
    elif tier == UnitTier.ELITE:
        harpooner_health = harpooner_health * 1.25
        harpoon_damage = harpoon_damage * 1.25
        melee_damage = melee_damage * 1.25
        harpoon_cooldown = harpoon_cooldown * 0.5  # Keep the cooldown improvement from advanced
    
    entity = unit_base_entity(
        x=x,
        y=y,
        team=team,
        unit_type=UnitType.PIRATE_HARPOONER,
        movement_speed=gc.PIRATE_HARPOONER_MOVEMENT_SPEED,
        health=harpooner_health,
        hitbox=Hitbox(
            width=16,
            height=32,
        ),
        corruption_powers=corruption_powers,
        tier=tier,
        play_spawning=play_spawning,
        orientation=orientation
    )
    targetting_strategy = TargetStrategy(
        rankings=[
            WeightedRanking(
                rankings={
                    ByDistance(entity=entity, y_bias=2, ascending=True): 1,
                },
                ascending=True,
            ),
        ],
        unit_condition=Not(HasStatusEffect(Immobilized)),
        targetting_group=TargetingGroup.TEAM2_LIVING_VISIBLE if team == TeamType.TEAM1 else TargetingGroup.TEAM1_LIVING_VISIBLE
    )
    esper.add_component(
        entity,
        Destination(target_strategy=targetting_strategy, x_offset=gc.PIRATE_HARPOONER_ATTACK_RANGE*2/3)
    )
    esper.add_component(entity, RangeIndicator(ranges=[gc.PIRATE_HARPOONER_HARPOON_MINIMUM_RANGE, gc.PIRATE_HARPOONER_HARPOON_MAXIMUM_RANGE]))
    esper.add_component(
        entity,
        Abilities(
            abilities=[
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        SatisfiesUnitCondition(
                            unit_condition=RememberedSatisfies(
                                condition=Any([
                                    HasComponent(ForcedMovement),
                                    HasComponent(Projectile),
                                ])
                            )
                        )
                    ],
                    persistent_conditions=[
                        SatisfiesUnitCondition(
                            unit_condition=RememberedSatisfies(
                                condition=Any([
                                    HasComponent(ForcedMovement),
                                    HasComponent(Projectile),
                                ])
                            )
                        )
                    ],
                    effects={},
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
                                    distance=gc.PIRATE_HARPOONER_HARPOON_MAXIMUM_RANGE,
                                    y_bias=None
                                ),
                                MinimumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.PIRATE_HARPOONER_HARPOON_MINIMUM_RANGE,
                                    y_bias=None
                                )
                            ])
                        ),
                        Cooldown(duration=harpoon_cooldown),
                    ],
                    persistent_conditions=[],
                    effects={
                        0: [
                            CreatesProjectile(
                                projectile_speed=gc.PIRATE_HARPOONER_HARPOON_PROJECTILE_SPEED,
                                effects=[
                                    RememberTarget(recipient=Recipient.OWNER),
                                    Damages(damage=harpoon_damage, recipient=Recipient.TARGET, is_melee=False),
                                    AddsForcedMovement(
                                        recipient=Recipient.TARGET,
                                        destination=Recipient.OWNER,
                                        speed=gc.PIRATE_HARPOONER_HARPOON_FORCED_MOVEMENT_SPEED,
                                        offset_x=30,
                                        offset_y=0,
                                    ),
                                    CreatesVisualLink(
                                        start_entity=Recipient.TARGET,
                                        other_entity=Recipient.OWNER,
                                        visual=Visual.Rope,
                                        tile_size=2,
                                        entity_delete_condition=Not(HasComponent(ForcedMovement)),
                                    ),
                                    CreatesRepeat(
                                        recipient=Recipient.TARGET,
                                        effects=[
                                            PlaySound(sound_effects=[
                                                (SoundEffect(filename=f"harpoon_click{i}.wav", volume=1.0), 1.0)
                                                for i in range(11)
                                            ])
                                        ],
                                        interval=0.05,
                                        stop_condition=Not(HasComponent(ForcedMovement)),
                                    )
                                ],
                                visual=Visual.PirateHarpoon,
                                projectile_offset_x=5*gc.MINIFOLKS_SCALE,
                                projectile_offset_y=0,
                                unit_condition=All([OnTeam(team=team.other()), Alive(), Grounded()]),
                                max_distance=gc.PIRATE_HARPOONER_HARPOON_MAXIMUM_RANGE,
                                on_create=lambda projectile: (
                                    esper.add_component(entity, EntityMemory(projectile)),
                                    esper.add_component(entity, VisualLink(
                                        other_entity=projectile,
                                        visual=Visual.Rope,
                                        tile_size=1,
                                    )),
                                    CreatesRepeat(
                                        recipient=Recipient.OWNER,
                                        effects=[
                                            PlaySound(sound_effects=[
                                                (SoundEffect(filename=f"harpoon_click{i}.wav", volume=1.0), 1.0)
                                                for i in range(11)
                                            ])
                                        ],
                                        interval=0.05,
                                        stop_condition=Not(HasComponent(VisualLink)),
                                    ).apply(owner=entity, parent=entity, target=entity)
                                ),
                            ),
                            PlaySound(SoundEffect(filename="pirate_harpoon.wav", volume=0.6)),
                        ]
                    },
                ),
                # Uses melee attack otherwise
                Ability(
                    target_strategy=targetting_strategy,
                    trigger_conditions=[
                        HasTarget(
                            unit_condition=All([
                                Alive(),
                                Grounded(),
                                MaximumDistanceFromEntity(
                                    entity=entity,
                                    distance=gc.PIRATE_HARPOONER_ATTACK_RANGE,
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
                                    distance=gc.PIRATE_HARPOONER_ATTACK_RANGE + gc.TARGETTING_GRACE_DISTANCE,
                                    y_bias=3
                                ),
                            ])
                        )
                    ],
                    effects={2: [
                        Damages(damage=melee_damage, recipient=Recipient.TARGET, is_melee=True),
                    ]},
                )
            ]
        )
    )
    esper.add_component(entity, get_unit_sprite_sheet(UnitType.PIRATE_HARPOONER, tier))
    esper.add_component(entity, AnimationEffects({
        AnimationType.WALKING: {
            frame: [PlaySound(sound_effects=[
                (SoundEffect(filename=f"grass_footstep{i+1}.wav", volume=0.15), 1.0) for i in range(3)
            ])]
            for frame in [2, 5]
        },
    }))
    esper.component_for_entity(entity, OnDeathEffect).effects.extend(MALE_DEATH_SOUNDS)
    return entity

def get_unit_sprite_sheet(unit_type: UnitType, tier: UnitTier) -> SpriteSheet:
    if unit_type == UnitType.CORE_ARCHER:
        # Advanced tier gets 50% faster rate of fire (attack animation 50% faster)
        # Elite tier keeps this upgrade plus gets additional range
        attack_animation_duration = gc.CORE_ARCHER_ANIMATION_ATTACK_DURATION
        if tier == UnitTier.ADVANCED or tier == UnitTier.ELITE:
            attack_animation_duration = attack_animation_duration * 2/3  # 50% faster = 2/3 duration
        
        return SpriteSheet(
            surface=sprite_sheets[UnitType.CORE_ARCHER],
            frame_width=32,
            frame_height=32,
            scale=gc.MINIFOLKS_SCALE,
            frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ABILITY1: 11, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 3, AnimationType.DYING: 6},
            animation_durations={
                AnimationType.IDLE: gc.CORE_ARCHER_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.CORE_ARCHER_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: attack_animation_duration,
                AnimationType.DYING: gc.CORE_ARCHER_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(0, -8),
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    if unit_type == UnitType.CORE_VETERAN:
        # Elite tier gets 25% faster attack speed and idle animation (25% faster)
        attack_animation_duration = gc.CORE_VETERAN_ANIMATION_ATTACK_DURATION
        idle_animation_duration = gc.CORE_VETERAN_ANIMATION_IDLE_DURATION
        if tier == UnitTier.ELITE:
            attack_animation_duration = attack_animation_duration * 0.8  # 25% faster = 0.8x duration
            idle_animation_duration = idle_animation_duration * 0.8  # 25% faster = 0.8x duration
        
        return SpriteSheet(
            surface=sprite_sheets[UnitType.CORE_VETERAN],
            frame_width=32,
            frame_height=32,
            scale=gc.MINIFOLKS_SCALE,
            frames={AnimationType.IDLE:4, AnimationType.WALKING: 6, AnimationType.ABILITY1: 10, AnimationType.DYING: 7},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 3, AnimationType.DYING: 6},
            animation_durations={
                AnimationType.IDLE: idle_animation_duration,
                AnimationType.WALKING: gc.CORE_VETERAN_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: attack_animation_duration,
                AnimationType.DYING: gc.CORE_VETERAN_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(0, -8),
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    if unit_type == UnitType.CORE_CAVALRY:
        return SpriteSheet(
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
        synchronized_animations={
            AnimationType.IDLE: True,
        }
    )
    if unit_type == UnitType.CORE_DUELIST:
        return SpriteSheet(
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
        synchronized_animations={
            AnimationType.IDLE: True,
        }
    )
    if unit_type == UnitType.CORE_LONGBOWMAN:
        return SpriteSheet(
            surface=sprite_sheets[UnitType.CORE_LONGBOWMAN],
            frame_width=100,
            frame_height=100,
            scale=gc.TINY_RPG_SCALE,
            frames={AnimationType.IDLE: 6, AnimationType.WALKING: 7, AnimationType.ABILITY1: 8, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 2, AnimationType.DYING: 5},
            animation_durations={
                AnimationType.IDLE: gc.CORE_LONGBOWMAN_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.CORE_LONGBOWMAN_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: gc.CORE_LONGBOWMAN_ANIMATION_ATTACK_DURATION,
                AnimationType.DYING: gc.CORE_LONGBOWMAN_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(0, 2),
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    if unit_type == UnitType.CORE_SWORDSMAN:
        return SpriteSheet(
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
        synchronized_animations={
            AnimationType.IDLE: True,
        }
    )
    if unit_type == UnitType.SKELETON_ARCHER:
        # Advanced tier gets 50% faster rate of fire (attack animation 50% faster)
        # Elite tier keeps this upgrade plus gets additional range
        attack_animation_duration = gc.SKELETON_ARCHER_ANIMATION_ATTACK_DURATION
        if tier == UnitTier.ADVANCED or tier == UnitTier.ELITE:
            attack_animation_duration = attack_animation_duration * 2/3  # 50% faster = 2/3 duration
        
        return SpriteSheet(
        surface=sprite_sheets[UnitType.SKELETON_ARCHER],
        frame_width=32,
        frame_height=32,
        scale=gc.MINIFOLKS_SCALE,
        frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ABILITY1: 9, AnimationType.DYING: 6},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 3, AnimationType.DYING: 6},
        animation_durations={
            AnimationType.IDLE: gc.SKELETON_ARCHER_ANIMATION_IDLE_DURATION,
            AnimationType.WALKING: gc.SKELETON_ARCHER_ANIMATION_WALKING_DURATION,
            AnimationType.ABILITY1: attack_animation_duration,
            AnimationType.DYING: gc.SKELETON_ARCHER_ANIMATION_DYING_DURATION,
        },
        sprite_center_offset=(0, -8),
        synchronized_animations={
            AnimationType.IDLE: True,
        }
    )
    
    if unit_type == UnitType.SKELETON_MAGE:
        return SpriteSheet(
            surface=sprite_sheets[UnitType.SKELETON_MAGE],
            frame_width=32,
            frame_height=32,
            scale=gc.MINIFOLKS_SCALE,
            frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ABILITY1: 7, AnimationType.DYING: 8},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 3, AnimationType.DYING: 6},
            animation_durations={
                AnimationType.IDLE: gc.SKELETON_MAGE_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.SKELETON_MAGE_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: gc.SKELETON_MAGE_ANIMATION_ATTACK_DURATION,
                AnimationType.DYING: gc.SKELETON_MAGE_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(0, -8),
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    
    if unit_type == UnitType.SKELETON_SWORDSMAN:
        return SpriteSheet(
        surface=sprite_sheets[UnitType.SKELETON_SWORDSMAN],
        frame_width=32,
        frame_height=32,
        scale=gc.MINIFOLKS_SCALE,
        frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ABILITY1: 5, AnimationType.DYING: 6},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 3, AnimationType.DYING: 5},
        animation_durations={
            AnimationType.IDLE: gc.SKELETON_SWORDSMAN_ANIMATION_IDLE_DURATION,
            AnimationType.WALKING: gc.SKELETON_SWORDSMAN_ANIMATION_WALKING_DURATION,
            AnimationType.ABILITY1: gc.SKELETON_SWORDSMAN_ANIMATION_ATTACK_DURATION,
            AnimationType.DYING: gc.SKELETON_SWORDSMAN_ANIMATION_DYING_DURATION,
        },
        sprite_center_offset=(0, -8),
        synchronized_animations={
            AnimationType.IDLE: True,
        }
    )
    if unit_type == UnitType.SKELETON_HORSEMAN:
        return SpriteSheet(
        surface=sprite_sheets[UnitType.SKELETON_HORSEMAN],
        frame_width=32,
        frame_height=32,
        scale=gc.MINIFOLKS_SCALE,
        frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ABILITY1: 9, AnimationType.DYING: 9},
        rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 3, AnimationType.DYING: 5},
        animation_durations={
            AnimationType.IDLE: gc.SKELETON_HORSEMAN_ANIMATION_IDLE_DURATION,
            AnimationType.WALKING: gc.SKELETON_HORSEMAN_ANIMATION_WALKING_DURATION,
            AnimationType.ABILITY1: gc.SKELETON_HORSEMAN_ANIMATION_ATTACK_DURATION,
            AnimationType.DYING: gc.SKELETON_HORSEMAN_ANIMATION_DYING_DURATION,
        },
        sprite_center_offset=(1, -6),
        synchronized_animations={
            AnimationType.IDLE: True,
        }
    )
    if unit_type == UnitType.ORC_BERSERKER:
        # No animation speed upgrades for orc berserker
        idle_animation_duration = gc.ORC_BERSERKER_ANIMATION_IDLE_DURATION
        throwing_animation_duration = gc.ORC_BERSERKER_ANIMATION_THROWING_DURATION
        melee_animation_duration = gc.ORC_BERSERKER_ANIMATION_MELEE_DURATION
        
        return SpriteSheet(
            surface=sprite_sheets[UnitType.ORC_BERSERKER],
            frame_width=32,
            frame_height=32,
            scale=gc.MINIFOLKS_SCALE,
            frames={
                AnimationType.IDLE: 4, 
                AnimationType.WALKING: 6, 
                AnimationType.ABILITY1: 4, # switch stance
                AnimationType.ABILITY2: 6, # melee  
                AnimationType.ABILITY3: 6, # ranged attack
                AnimationType.DYING: 4
            },
            rows={
                AnimationType.IDLE: 0, 
                AnimationType.WALKING: 1, 
                AnimationType.ABILITY1: 0, # switch stance
                AnimationType.ABILITY2: 5, # melee attack
                AnimationType.ABILITY3: 4, # ranged attack
                AnimationType.DYING: 8
            },
            animation_durations={
                AnimationType.IDLE: idle_animation_duration,
                AnimationType.WALKING: gc.ORC_BERSERKER_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: gc.ORC_BERSERKER_ANIMATION_TRANSITION_DURATION,
                AnimationType.ABILITY2: melee_animation_duration,
                AnimationType.ABILITY3: throwing_animation_duration,
                AnimationType.DYING: gc.ORC_BERSERKER_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(0, -8),
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    if unit_type == UnitType.ORC_GOBLIN:
        # Calculate tier-specific animation durations
        attack_animation_duration = gc.ORC_GOBLIN_ANIMATION_ATTACK_DURATION
        idle_animation_duration = gc.ORC_GOBLIN_ANIMATION_IDLE_DURATION
        
        # Elite tier: 25% faster attack and idle animations
        if tier == UnitTier.ELITE:
            attack_animation_duration = attack_animation_duration * 0.8  # 25% faster = 0.8x duration
            idle_animation_duration = idle_animation_duration * 0.8  # 25% faster = 0.8x duration
        
        return SpriteSheet(
            surface=sprite_sheets[UnitType.ORC_GOBLIN],
            frame_width=32,
            frame_height=32,
            scale=gc.MINIFOLKS_SCALE,
            frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ABILITY1: 4, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 4, AnimationType.DYING: 6},
            animation_durations={
                AnimationType.IDLE: idle_animation_duration,
                AnimationType.WALKING: gc.ORC_GOBLIN_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: attack_animation_duration,
                AnimationType.DYING: gc.ORC_GOBLIN_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(0, -10),
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    if unit_type == UnitType.ORC_WARG_RIDER:
        # Calculate tier-specific animation durations
        attack_animation_duration = gc.ORC_WARG_RIDER_ANIMATION_ATTACK_DURATION
        idle_animation_duration = gc.ORC_WARG_RIDER_ANIMATION_IDLE_DURATION
        
        # Advanced tier: 25% faster attack, idle, and walking animations
        if tier == UnitTier.ADVANCED or tier == UnitTier.ELITE:
            attack_animation_duration = attack_animation_duration * 0.8  # 25% faster = 0.8x duration
            idle_animation_duration = idle_animation_duration * 0.8  # 25% faster = 0.8x duration
        
        return SpriteSheet(
            surface=sprite_sheets[UnitType.ORC_WARG_RIDER],
            frame_width=32,
            frame_height=32,
            scale=gc.MINIFOLKS_SCALE,
            frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ABILITY1: 6, AnimationType.DYING: 5},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 3, AnimationType.DYING: 5},
            animation_durations={
                AnimationType.IDLE: idle_animation_duration,
                AnimationType.WALKING: gc.ORC_WARG_RIDER_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: attack_animation_duration,
                AnimationType.DYING: gc.ORC_WARG_RIDER_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(1, -6),
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    if unit_type == UnitType.ORC_WARRIOR:
        # Elite tier: 30% faster attack animation
        idle_animation_duration = gc.ORC_WARRIOR_ANIMATION_IDLE_DURATION
        attack_animation_duration = gc.ORC_WARRIOR_ANIMATION_ATTACK_DURATION
        if tier == UnitTier.ELITE:
            attack_animation_duration = attack_animation_duration * 0.77
            idle_animation_duration = idle_animation_duration * 0.77
        
        return SpriteSheet(
            surface=sprite_sheets[UnitType.ORC_WARRIOR],
            frame_width=32,
            frame_height=32,
            scale=gc.MINIFOLKS_SCALE,
            frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ABILITY1: 5, AnimationType.DYING: 6},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 3, AnimationType.DYING: 5},
            animation_durations={
                AnimationType.IDLE: idle_animation_duration,
                AnimationType.WALKING: gc.ORC_WARRIOR_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: attack_animation_duration,
                AnimationType.DYING: gc.ORC_WARRIOR_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(0, -8),
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    if unit_type == UnitType.ORC_WARCHIEF:
        # No animation speed upgrades for orc warchief
        return SpriteSheet(
            surface=sprite_sheets[UnitType.ORC_WARCHIEF],
            frame_width=32,
            frame_height=32,
            scale=gc.MINIFOLKS_SCALE,
            frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ABILITY1: 5, AnimationType.DYING: 6},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 3, AnimationType.DYING: 5},
            animation_durations={
                AnimationType.IDLE: gc.ORC_WARCHIEF_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.ORC_WARCHIEF_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: gc.ORC_WARCHIEF_ANIMATION_ATTACK_DURATION,
                AnimationType.DYING: gc.ORC_WARCHIEF_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(0, -8),
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    if unit_type == UnitType.CORE_WIZARD:
        return SpriteSheet(
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
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    if unit_type in (
        UnitType.SKELETON_ARCHER_NECROMANCER,
        UnitType.SKELETON_HORSEMAN_NECROMANCER,
        UnitType.SKELETON_MAGE_NECROMANCER,
        UnitType.SKELETON_SWORDSMAN_NECROMANCER,
    ):
        # Necromancers use consistent frame/row layout per provided animation info
        return SpriteSheet(
            surface=sprite_sheets[unit_type],
            frame_width=32,
            frame_height=32,
            scale=gc.MINIFOLKS_SCALE,
            frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ABILITY1: 7, AnimationType.DYING: 8},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 4, AnimationType.DYING: 6},
            animation_durations={
                AnimationType.IDLE: gc.CORE_WIZARD_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.CORE_WIZARD_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: gc.CORE_WIZARD_ANIMATION_ATTACK_DURATION,
                AnimationType.DYING: gc.CORE_WIZARD_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(0, -8),
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    if unit_type == UnitType.INFANTRY_BANNER_BEARER:
        return SpriteSheet(
            surface=sprite_sheets[UnitType.INFANTRY_BANNER_BEARER],
            frame_width=100,
            frame_height=100,
            scale=gc.TINY_RPG_SCALE,
            frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.DYING: 2},
            animation_durations={
                AnimationType.IDLE: gc.INFANTRY_BANNER_BEARER_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.INFANTRY_BANNER_BEARER_ANIMATION_WALKING_DURATION,
                AnimationType.DYING: gc.INFANTRY_BANNER_BEARER_ANIMATION_DYING_DURATION,
            },
            synchronized_animations={
                AnimationType.WALKING: True,
                AnimationType.IDLE: True,
            },
            sprite_center_offset=(2, -5),
        )
    if unit_type == UnitType.CRUSADER_BLACK_KNIGHT:
        return SpriteSheet(
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
            synchronized_animations={
                AnimationType.IDLE: True,
            },
            sprite_center_offset=(0, 7),
        )
    if unit_type == UnitType.INFANTRY_CATAPULT:
        return SpriteSheet(
            surface=sprite_sheets[UnitType.INFANTRY_CATAPULT],
            frame_width=128,
            frame_height=288//3,
            scale=gc.TINY_RPG_SCALE,
            frames={AnimationType.IDLE: 1, 
                    AnimationType.WALKING: 1,
                    AnimationType.ABILITY1: 10, 
                    AnimationType.DYING: 3},
            rows={AnimationType.IDLE: 0, 
                AnimationType.WALKING: 0,
                AnimationType.ABILITY1: 0, 
                AnimationType.DYING: 2},
            animation_durations={
                AnimationType.IDLE: gc.INFANTRY_CATAPULT_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.INFANTRY_CATAPULT_ANIMATION_IDLE_DURATION,
                AnimationType.ABILITY1: gc.INFANTRY_CATAPULT_ANIMATION_ATTACK_DURATION,
                AnimationType.DYING: gc.INFANTRY_CATAPULT_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(-10, -7),
            flip_frames=True,   
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    if unit_type == UnitType.CRUSADER_CLERIC:
        # Elite tier: 50% faster casting speed
        attack_animation_duration = gc.CRUSADER_CLERIC_ANIMATION_ATTACK_DURATION
        if tier == UnitTier.ELITE:
            attack_animation_duration = attack_animation_duration * 2/3  # 50% faster = 2/3 duration
        
        return SpriteSheet(
            surface=sprite_sheets[UnitType.CRUSADER_CLERIC],
            frame_width=100,
            frame_height=100,
            scale=gc.TINY_RPG_SCALE,
            frames={AnimationType.IDLE: 6, AnimationType.WALKING: 8, AnimationType.ABILITY1: 6, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 4, AnimationType.DYING: 7},
            animation_durations={
                AnimationType.IDLE: gc.CRUSADER_CLERIC_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.CRUSADER_CLERIC_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: attack_animation_duration,
                AnimationType.DYING: gc.CRUSADER_CLERIC_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(0, 2),
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    if unit_type == UnitType.MISC_COMMANDER:
        return SpriteSheet(
            surface=sprite_sheets[UnitType.MISC_COMMANDER],
            frame_width=100,
            frame_height=100,
            scale=gc.TINY_RPG_SCALE,
            frames={AnimationType.IDLE: 6, AnimationType.WALKING: 8, AnimationType.ABILITY1: 7, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 4, AnimationType.DYING: 8},
            animation_durations={
                AnimationType.IDLE: gc.MISC_COMMANDER_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.MISC_COMMANDER_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: gc.MISC_COMMANDER_ANIMATION_ATTACK_DURATION,
                AnimationType.DYING: gc.MISC_COMMANDER_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(0, 2),
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    if unit_type == UnitType.INFANTRY_CROSSBOWMAN:
        # Elite tier: 25% faster attack, reload, and idle animations
        attack_animation_duration = gc.INFANTRY_CROSSBOWMAN_ANIMATION_ATTACK_DURATION
        reload_animation_duration = gc.INFANTRY_CROSSBOWMAN_ANIMATION_RELOAD_DURATION
        idle_animation_duration = gc.INFANTRY_CROSSBOWMAN_ANIMATION_IDLE_DURATION
        
        if tier == UnitTier.ELITE:
            attack_animation_duration = attack_animation_duration * 0.8  # 25% faster = 0.8x duration
            reload_animation_duration = reload_animation_duration * 0.8  # 25% faster = 0.8x duration
            idle_animation_duration = idle_animation_duration * 0.8  # 25% faster = 0.8x duration
        
        return SpriteSheet(
            surface=sprite_sheets[UnitType.INFANTRY_CROSSBOWMAN],
            frame_width=32,
            frame_height=32,
            scale=gc.MINIFOLKS_SCALE,
            frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ABILITY1: 5, AnimationType.ABILITY2: 5, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 3, AnimationType.ABILITY2: 7, AnimationType.DYING: 6},
            animation_durations={
                AnimationType.IDLE: idle_animation_duration,
                AnimationType.WALKING: gc.INFANTRY_CROSSBOWMAN_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: attack_animation_duration,
                AnimationType.ABILITY2: reload_animation_duration,
                AnimationType.DYING: gc.INFANTRY_CROSSBOWMAN_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(0, -8),
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    if unit_type == UnitType.CORE_DEFENDER:
        # Advanced tier (and Elite): 35% increased attack speed
        attack_animation_duration = gc.CORE_DEFENDER_ANIMATION_ATTACK_DURATION
        if tier == UnitTier.ADVANCED or tier == UnitTier.ELITE:
            attack_animation_duration = attack_animation_duration / 1.35  # 35% faster
        
        return SpriteSheet(
            surface=sprite_sheets[UnitType.CORE_DEFENDER],
            frame_width=32,
            frame_height=32,
            scale=gc.MINIFOLKS_SCALE,
            frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ABILITY1: 6, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 3, AnimationType.DYING: 6},
            animation_durations={
                AnimationType.IDLE: gc.CORE_DEFENDER_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.CORE_DEFENDER_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: attack_animation_duration,
                AnimationType.DYING: gc.CORE_DEFENDER_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(0, -8),
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    if unit_type == UnitType.CRUSADER_GOLD_KNIGHT:
        return SpriteSheet(
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
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    if unit_type == UnitType.CRUSADER_GUARDIAN_ANGEL:
        return SpriteSheet(
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
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    if unit_type == UnitType.CRUSADER_PALADIN:
        # Elite tier: 25% increased attack speed (idle, healing, and attack animation)
        idle_animation_duration = gc.CRUSADER_PALADIN_ANIMATION_IDLE_DURATION
        healing_animation_duration = gc.CRUSADER_PALADIN_ANIMATION_SKILL_DURATION
        attack_animation_duration = gc.CRUSADER_PALADIN_ANIMATION_ATTACK_DURATION
        
        if tier == UnitTier.ELITE:
            idle_animation_duration = idle_animation_duration * 0.8  # 25% faster = 0.8x duration
            healing_animation_duration = healing_animation_duration * 0.8  # 25% faster = 0.8x duration
            attack_animation_duration = attack_animation_duration * 0.8  # 25% faster = 0.8x duration
        
        return SpriteSheet(
            surface=sprite_sheets[UnitType.CRUSADER_PALADIN],
            frame_width=100,
            frame_height=100,
            scale=gc.TINY_RPG_SCALE,
            frames={AnimationType.IDLE: 6, AnimationType.WALKING: 8, AnimationType.ABILITY1: 13, AnimationType.ABILITY2: 6, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 7, AnimationType.ABILITY2: 3, AnimationType.DYING: 6},
            animation_durations={
                AnimationType.IDLE: idle_animation_duration,
                AnimationType.WALKING: gc.CRUSADER_PALADIN_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: healing_animation_duration,
                AnimationType.ABILITY2: attack_animation_duration,
                AnimationType.DYING: gc.CRUSADER_PALADIN_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(0, 7),
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    if unit_type == UnitType.INFANTRY_PIKEMAN:
        return SpriteSheet(
            surface=sprite_sheets[UnitType.INFANTRY_PIKEMAN],
            frame_width=120,
            frame_height=120,
            scale=gc.TINY_RPG_SCALE,
            frames={AnimationType.IDLE: 6, AnimationType.WALKING: 7, AnimationType.ABILITY1: 2, AnimationType.ABILITY2: 6, AnimationType.ABILITY3: 2, AnimationType.DYING: 3},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 2, AnimationType.ABILITY2: 3, AnimationType.ABILITY3: 4, AnimationType.DYING: 5},
            animation_durations={
                AnimationType.IDLE: gc.INFANTRY_PIKEMAN_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.INFANTRY_PIKEMAN_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: gc.INFANTRY_PIKEMAN_ANIMATION_STANCE_CHANGE_DURATION,
                AnimationType.ABILITY2: gc.INFANTRY_PIKEMAN_ANIMATION_ATTACK_DURATION,
                AnimationType.ABILITY3: gc.INFANTRY_PIKEMAN_ANIMATION_STANCE_CHANGE_DURATION,
                AnimationType.DYING: gc.INFANTRY_PIKEMAN_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(25, -30),
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    if unit_type == UnitType.MISC_RED_KNIGHT:
        return SpriteSheet(
            surface=sprite_sheets[UnitType.MISC_RED_KNIGHT],
            frame_width=100,
            frame_height=100,
            scale=gc.TINY_RPG_SCALE,
            frames={AnimationType.IDLE: 6, AnimationType.WALKING: 8, AnimationType.ABILITY1: 11, AnimationType.ABILITY2: 10, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 4, AnimationType.ABILITY2: 3, AnimationType.DYING: 7},
            animation_durations={
                AnimationType.IDLE: gc.MISC_RED_KNIGHT_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.MISC_RED_KNIGHT_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: gc.MISC_RED_KNIGHT_ANIMATION_SKILL_DURATION,
                AnimationType.ABILITY2: gc.MISC_RED_KNIGHT_ANIMATION_ATTACK_DURATION,
                AnimationType.DYING: gc.MISC_RED_KNIGHT_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(0, 1),
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    if unit_type == UnitType.INFANTRY_SOLDIER:
        return SpriteSheet(
            surface=sprite_sheets[UnitType.INFANTRY_SOLDIER],
            frame_width=100,
            frame_height=100,
            scale=gc.TINY_RPG_SCALE,
            frames={AnimationType.IDLE: 6, AnimationType.WALKING: 8, AnimationType.ABILITY1: 3, AnimationType.ABILITY2: 6, AnimationType.ABILITY3: 9, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 7, AnimationType.ABILITY2: 2, AnimationType.ABILITY3: 4, AnimationType.DYING: 6},
            animation_durations={
                AnimationType.IDLE: gc.INFANTRY_SOLDIER_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.INFANTRY_SOLDIER_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: gc.INFANTRY_SOLDIER_ANIMATION_SWITCH_STANCE_DURATION,
                AnimationType.ABILITY2: gc.INFANTRY_SOLDIER_ANIMATION_MELEE_ATTACK_DURATION,
                AnimationType.ABILITY3: gc.INFANTRY_SOLDIER_ANIMATION_RANGED_ATTACK_DURATION,
                AnimationType.DYING: gc.INFANTRY_SOLDIER_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(0, 1),
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    if unit_type == UnitType.WEREBEAR:
        return SpriteSheet(
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
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    if unit_type == UnitType.ZOMBIE_BASIC_ZOMBIE:
        return SpriteSheet(
            surface=sprite_sheets[UnitType.ZOMBIE_BASIC_ZOMBIE],
            frame_width=32,
            frame_height=32,
            scale=gc.MINIFOLKS_SCALE,
            frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ABILITY1: 4, AnimationType.DYING: 4, AnimationType.SPAWNING: 9},
            rows={AnimationType.IDLE: 1, AnimationType.WALKING: 2, AnimationType.ABILITY1: 5, AnimationType.DYING: 8, AnimationType.SPAWNING: 0},
            animation_durations={
                AnimationType.IDLE: gc.ZOMBIE_BASIC_ZOMBIE_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.ZOMBIE_BASIC_ZOMBIE_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: gc.ZOMBIE_BASIC_ZOMBIE_ANIMATION_ATTACK_DURATION,
                AnimationType.DYING: gc.ZOMBIE_BASIC_ZOMBIE_ANIMATION_DYING_DURATION,
                AnimationType.SPAWNING: gc.ZOMBIE_BASIC_ZOMBIE_ANIMATION_SPAWNING_DURATION,
            },
            sprite_center_offset=(0, -9),
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    if unit_type == UnitType.ZOMBIE_FIGHTER:
        return SpriteSheet(
            surface=sprite_sheets[UnitType.ZOMBIE_FIGHTER],
            frame_width=32,
            frame_height=32,
            scale=gc.MINIFOLKS_SCALE,
            frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ABILITY1: 12, AnimationType.DYING: 4, AnimationType.SPAWNING: 9},
            rows={AnimationType.IDLE: 1, AnimationType.WALKING: 2, AnimationType.ABILITY1: 7, AnimationType.DYING: 9, AnimationType.SPAWNING: 0},
            animation_durations={
                AnimationType.IDLE: gc.ZOMBIE_FIGHTER_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.ZOMBIE_FIGHTER_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: gc.ZOMBIE_FIGHTER_ANIMATION_ATTACK_DURATION,
                AnimationType.DYING: gc.ZOMBIE_FIGHTER_ANIMATION_DYING_DURATION,
                AnimationType.SPAWNING: gc.ZOMBIE_FIGHTER_ANIMATION_SPAWNING_DURATION,
            },
            sprite_center_offset=(0, -9),
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    if unit_type == UnitType.MISC_BRUTE:
        return SpriteSheet(
            surface=sprite_sheets[UnitType.MISC_BRUTE],
            frame_width=100,
            frame_height=100,
            scale=1.5*gc.TINY_RPG_SCALE,
            frames={AnimationType.IDLE: 3, AnimationType.WALKING: 4, AnimationType.ABILITY1: 5, AnimationType.ABILITY2: 5, AnimationType.DYING: 6},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 2, AnimationType.ABILITY2: 2, AnimationType.DYING: 3},
            animation_durations={
                AnimationType.IDLE: gc.MISC_BRUTE_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.MISC_BRUTE_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: gc.MISC_BRUTE_ANIMATION_ATTACK_DURATION,
                AnimationType.ABILITY2: gc.MISC_BRUTE_ANIMATION_ATTACK_DURATION,
                AnimationType.DYING: gc.MISC_BRUTE_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(2, 8),
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    if unit_type == UnitType.ZOMBIE_JUMPER:
        # Advanced tier (and Elite): 15% faster action speed (idle and attack)
        # Elite tier: 30% faster action speed total (idle and attack)
        idle_animation_duration = gc.ZOMBIE_JUMPER_ANIMATION_IDLE_DURATION
        attack_animation_duration = gc.ZOMBIE_JUMPER_ANIMATION_ATTACK_DURATION
        
        if tier == UnitTier.ADVANCED:
            idle_animation_duration = idle_animation_duration / 1.15  # 15% faster
            attack_animation_duration = attack_animation_duration / 1.15  # 15% faster
        elif tier == UnitTier.ELITE:
            idle_animation_duration = idle_animation_duration / 1.3  # 30% faster
            attack_animation_duration = attack_animation_duration / 1.3  # 30% faster
        
        return SpriteSheet(
            surface=sprite_sheets[UnitType.ZOMBIE_JUMPER],
            frame_width=32,
            frame_height=32,
            scale=gc.MINIFOLKS_SCALE,
            frames={
                AnimationType.IDLE: 4,
                AnimationType.WALKING: 6,
                AnimationType.ABILITY1: 6,
                AnimationType.ABILITY2: 1,
                AnimationType.DYING: 4,
                AnimationType.AIRBORNE: 1,
            },
            rows={
                AnimationType.IDLE: 0,
                AnimationType.WALKING: 1,
                AnimationType.ABILITY1: 4,
                AnimationType.ABILITY2: 2,
                AnimationType.DYING: 7,
                AnimationType.AIRBORNE: 8,
            },
            animation_durations={
                AnimationType.IDLE: idle_animation_duration,
                AnimationType.WALKING: gc.ZOMBIE_JUMPER_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: attack_animation_duration,
                AnimationType.ABILITY2: gc.ZOMBIE_JUMPER_ANIMATION_JUMPING_DURATION,
                AnimationType.DYING: gc.ZOMBIE_JUMPER_ANIMATION_DYING_DURATION,
                AnimationType.AIRBORNE: gc.ZOMBIE_JUMPER_ANIMATION_AIRBORNE_DURATION,
            },
            sprite_center_offset=(1, -10),
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    if unit_type == UnitType.ZOMBIE_SPITTER:
        return SpriteSheet(
            surface=sprite_sheets[UnitType.ZOMBIE_SPITTER],
            frame_width=32,
            frame_height=32,
            scale=gc.MINIFOLKS_SCALE,
            frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ABILITY1: 6, AnimationType.ABILITY2: 4, AnimationType.DYING: 4},
            rows={AnimationType.IDLE: 1, AnimationType.WALKING: 2, AnimationType.ABILITY1: 6, AnimationType.ABILITY2: 5, AnimationType.DYING: 8},
            animation_durations={
                AnimationType.IDLE: gc.ZOMBIE_SPITTER_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.ZOMBIE_SPITTER_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: gc.ZOMBIE_SPITTER_ANIMATION_MELEE_ATTACK_DURATION,
                AnimationType.ABILITY2: gc.ZOMBIE_SPITTER_ANIMATION_RANGED_ATTACK_DURATION,
                AnimationType.DYING: gc.ZOMBIE_SPITTER_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(0, -8),
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    if unit_type == UnitType.ZOMBIE_TANK:
        return SpriteSheet(
            surface=sprite_sheets[UnitType.ZOMBIE_TANK],
            frame_width=32,
            frame_height=32,
            scale=gc.MINIFOLKS_SCALE,
            frames={AnimationType.IDLE: 4, AnimationType.WALKING: 6, AnimationType.ABILITY1: 7, AnimationType.DYING: 6},
            rows={AnimationType.IDLE: 1, AnimationType.WALKING: 2, AnimationType.ABILITY1: 4, AnimationType.DYING: 8},
            animation_durations={
                AnimationType.IDLE: gc.ZOMBIE_TANK_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.ZOMBIE_TANK_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: gc.ZOMBIE_TANK_ANIMATION_ATTACK_DURATION,
                AnimationType.DYING: gc.ZOMBIE_TANK_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(0, -6),
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    if unit_type == UnitType.MISC_GRABBER:
        return SpriteSheet(
            surface=sprite_sheets[UnitType.MISC_GRABBER],
            frame_width=100,
            frame_height=100,
            scale=gc.TINY_RPG_SCALE,
            frames={
                AnimationType.IDLE: 3,
                AnimationType.WALKING: 4,
                AnimationType.ABILITY1: 5,
                AnimationType.ABILITY2: 5,
                AnimationType.ABILITY3: 5,
                AnimationType.DYING: 6,
            },
            rows={
                AnimationType.IDLE: 0,
                AnimationType.WALKING: 1,
                AnimationType.ABILITY1: 2,
                AnimationType.ABILITY2: 2,
                AnimationType.ABILITY3: 2,
                AnimationType.DYING: 3,
            },
            animation_durations={
                AnimationType.IDLE: gc.MISC_GRABBER_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.MISC_GRABBER_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: gc.MISC_GRABBER_ANIMATION_CHANNELING_DURATION,
                AnimationType.ABILITY2: gc.MISC_GRABBER_ANIMATION_GRAB_DURATION,
                AnimationType.ABILITY3: gc.MISC_GRABBER_ANIMATION_ATTACK_DURATION,
                AnimationType.DYING: gc.MISC_GRABBER_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(2, 8),
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    if unit_type == UnitType.PIRATE_HARPOONER:
        # Advanced tier: 50% cooldown recovery
        # Elite tier: 25% increased attack damage and health
        harpoon_animation_duration = gc.PIRATE_HARPOONER_ANIMATION_HARPOON_DURATION
        channeling_animation_duration = gc.PIRATE_HARPOONER_ANIMATION_CHANNELING_DURATION
        attack_animation_duration = gc.PIRATE_HARPOONER_ANIMATION_ATTACK_DURATION
        
        if tier == UnitTier.ADVANCED:
            harpoon_animation_duration = harpoon_animation_duration * 0.5  # 50% faster cooldown
            channeling_animation_duration = channeling_animation_duration * 0.5
        elif tier == UnitTier.ELITE:
            harpoon_animation_duration = harpoon_animation_duration * 0.5  # Keep the speed improvement
            channeling_animation_duration = channeling_animation_duration * 0.5
        
        return SpriteSheet(
            surface=sprite_sheets[UnitType.PIRATE_HARPOONER],
            frame_width=32,
            frame_height=32,
            scale=gc.MINIFOLKS_SCALE,
            frames={
                AnimationType.IDLE: 4,
                AnimationType.WALKING: 6,
                AnimationType.ABILITY1: 4,
                AnimationType.ABILITY2: 10,
                AnimationType.ABILITY3: 4,
                AnimationType.DYING: 5,
            },
            rows={
                AnimationType.IDLE: 0,
                AnimationType.WALKING: 1,
                AnimationType.ABILITY1: 0,
                AnimationType.ABILITY2: 3,
                AnimationType.ABILITY3: 4,
                AnimationType.DYING: 6,
            },
            animation_durations={
                AnimationType.IDLE: gc.PIRATE_HARPOONER_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.PIRATE_HARPOONER_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: channeling_animation_duration,
                AnimationType.ABILITY2: harpoon_animation_duration,
                AnimationType.ABILITY3: attack_animation_duration,
                AnimationType.DYING: gc.PIRATE_HARPOONER_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(0, -8),
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    if unit_type == UnitType.PIRATE_CREW:
        # Advanced tier: 25% increased attack and movement speed
        # Elite tier: 50% more damage total
        idle_animation_duration = gc.PIRATE_CREW_ANIMATION_IDLE_DURATION
        attack_animation_duration = gc.PIRATE_CREW_ANIMATION_ATTACK_DURATION
        
        if tier == UnitTier.ADVANCED:
            idle_animation_duration = idle_animation_duration / 1.25  # 25% faster
            attack_animation_duration = attack_animation_duration / 1.25  # 25% faster
        
        return SpriteSheet(
            surface=sprite_sheets[UnitType.PIRATE_CREW],
            frame_width=32,
            frame_height=32,
            scale=gc.MINIFOLKS_SCALE,
            frames={
                AnimationType.IDLE: 4, 
                AnimationType.WALKING: 6, 
                AnimationType.ABILITY1: 5, 
                AnimationType.ABILITY2: 1,
                AnimationType.DYING: 4,
                AnimationType.AIRBORNE: 1,
            },
            rows={
                AnimationType.IDLE: 0, 
                AnimationType.WALKING: 1, 
                AnimationType.ABILITY1: 3, 
                AnimationType.ABILITY2: 2,
                AnimationType.DYING: 5,
                AnimationType.AIRBORNE: 4,
            },
            animation_durations={
                AnimationType.IDLE: idle_animation_duration,
                AnimationType.WALKING: gc.PIRATE_CREW_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: attack_animation_duration,
                AnimationType.ABILITY2: gc.PIRATE_CREW_ANIMATION_JUMP_DURATION,
                AnimationType.DYING: gc.PIRATE_CREW_ANIMATION_DYING_DURATION,
                AnimationType.AIRBORNE: gc.PIRATE_CREW_ANIMATION_AIRBORNE_DURATION,
            },
            sprite_center_offset=(0, -8),
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    if unit_type == UnitType.PIRATE_GUNNER:
        return SpriteSheet(
            surface=sprite_sheets[UnitType.PIRATE_GUNNER],
            frame_width=32,
            frame_height=32,
            scale=gc.MINIFOLKS_SCALE,
            frames={
                AnimationType.IDLE: 4, 
                AnimationType.WALKING: 6, 
                AnimationType.ABILITY1: 7, 
                AnimationType.ABILITY2: 6,
                AnimationType.DYING: 4,
            },
            rows={
                AnimationType.IDLE: 0, 
                AnimationType.WALKING: 1, 
                AnimationType.ABILITY1: 3, 
                AnimationType.ABILITY2: 4,
                AnimationType.DYING: 6,
            },
            animation_durations={
                AnimationType.IDLE: gc.PIRATE_GUNNER_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.PIRATE_GUNNER_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: gc.PIRATE_GUNNER_ANIMATION_GUN_DURATION,
                AnimationType.ABILITY2: gc.PIRATE_GUNNER_ANIMATION_MELEE_DURATION,
                AnimationType.DYING: gc.PIRATE_GUNNER_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(0, -8),
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    if unit_type == UnitType.PIRATE_CAPTAIN:
        return SpriteSheet(
            surface=sprite_sheets[UnitType.PIRATE_CAPTAIN],
            frame_width=32,
            frame_height=32,
            scale=gc.MINIFOLKS_SCALE,
            frames={
                AnimationType.IDLE: 4, 
                AnimationType.WALKING: 6, 
                AnimationType.ABILITY1: 7, 
                AnimationType.ABILITY2: 5,
                AnimationType.DYING: 5,
            },
            rows={
                AnimationType.IDLE: 0, 
                AnimationType.WALKING: 1, 
                AnimationType.ABILITY1: 4, 
                AnimationType.ABILITY2: 3,
                AnimationType.DYING: 6,
            },
            animation_durations={
                AnimationType.IDLE: gc.PIRATE_CAPTAIN_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.PIRATE_CAPTAIN_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: gc.PIRATE_CAPTAIN_ANIMATION_GUN_DURATION,
                AnimationType.ABILITY2: gc.PIRATE_CAPTAIN_ANIMATION_MELEE_DURATION,
                AnimationType.DYING: gc.PIRATE_CAPTAIN_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(0, -8),
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    if unit_type == UnitType.PIRATE_CANNON:
        return SpriteSheet(
            surface=sprite_sheets[UnitType.PIRATE_CANNON],
            frame_width=32,
            frame_height=32,
            scale=gc.MINIFOLKS_SCALE,
            frames={
                AnimationType.IDLE: 1, 
                AnimationType.WALKING: 4, 
                AnimationType.ABILITY1: 2, 
                AnimationType.DYING: 4
            },
            rows={
                AnimationType.IDLE: 0, 
                AnimationType.WALKING: 1, 
                AnimationType.ABILITY1: 2, 
                AnimationType.DYING: 5
            },
            animation_durations={
                AnimationType.IDLE: gc.PIRATE_CANNON_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.PIRATE_CANNON_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: gc.PIRATE_CANNON_ANIMATION_ATTACK_DURATION,
                AnimationType.DYING: gc.PIRATE_CANNON_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(0, -10),
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    if unit_type == UnitType.SKELETON_LICH:
        return SpriteSheet(
            surface=sprite_sheets[UnitType.SKELETON_LICH],
            frame_width=32,
            frame_height=32,
            scale=gc.MINIFOLKS_SCALE,
            frames={AnimationType.IDLE: 4, AnimationType.WALKING: 4, AnimationType.ABILITY1: 6, AnimationType.DYING: 7},
            rows={AnimationType.IDLE: 0, AnimationType.WALKING: 1, AnimationType.ABILITY1: 4, AnimationType.DYING: 6},
            animation_durations={
                AnimationType.IDLE: gc.SKELETON_LICH_ANIMATION_IDLE_DURATION,
                AnimationType.WALKING: gc.SKELETON_LICH_ANIMATION_WALKING_DURATION,
                AnimationType.ABILITY1: gc.SKELETON_LICH_ANIMATION_ABILITY_DURATION,
                AnimationType.DYING: gc.SKELETON_LICH_ANIMATION_DYING_DURATION,
            },
            sprite_center_offset=(0, -8),
            synchronized_animations={
                AnimationType.IDLE: True,
            }
        )
    raise NotImplementedError(unit_type)
