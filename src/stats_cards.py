"""Module for generating stats card text for different unit types."""

from typing import List
from components.unit_type import UnitType
from game_constants import gc
from unit_values import unit_values

def get_stats_card_text(unit_type: UnitType) -> List[str]:
    """Get the stats card text for a given unit type.
    
    Args:
        unit_type: The type of unit to get stats for
        
    Returns:
        List of text lines for the stats card
    """
    if unit_type == UnitType.CORE_ARCHER:
        return [
            f"Name: Archer",
            f"Faction: Core",
            f"Value: {unit_values[unit_type]}",
            f"Health: {gc.CORE_ARCHER_HP}",
            f"Attack: {gc.CORE_ARCHER_ATTACK_DAMAGE}",
            f"DPS: {round(gc.CORE_ARCHER_ATTACK_DAMAGE/gc.CORE_ARCHER_ANIMATION_ATTACK_DURATION, 2)}",
            f"Speed: {gc.CORE_ARCHER_MOVEMENT_SPEED}",
            f"Range: {gc.CORE_ARCHER_ATTACK_RANGE}",
            f"Projectile Speed: {gc.CORE_ARCHER_PROJECTILE_SPEED}",
            f"AI: Targets the nearest enemy, preferring units at the same height on the y-axis",
        ]
    elif unit_type == UnitType.CORE_BARBARIAN:
        return [
            f"Name: Barbarian",
            f"Faction: Core",
            f"Value: {unit_values[unit_type]}",
            f"Health: {gc.CORE_BARBARIAN_HP}",
            f"Attack: {gc.CORE_BARBARIAN_ATTACK_DAMAGE}",
            f"DPS: {round(gc.CORE_BARBARIAN_ATTACK_DAMAGE/gc.CORE_BARBARIAN_ANIMATION_ATTACK_DURATION, 2)}",
            f"Speed: {gc.CORE_BARBARIAN_MOVEMENT_SPEED}",
            f"Range: {gc.CORE_BARBARIAN_ATTACK_RANGE}",
        ]
    elif unit_type == UnitType.CORE_CAVALRY:
        return [
            f"Name: Cavalry",
            f"Faction: Core",
            f"Value: {unit_values[unit_type]}",
            f"Health: {gc.CORE_CAVALRY_HP}",
            f"Attack: {gc.CORE_CAVALRY_ATTACK_DAMAGE}",
            f"DPS: {round(gc.CORE_CAVALRY_ATTACK_DAMAGE/gc.CORE_CAVALRY_ANIMATION_ATTACK_DURATION, 2)}",
            f"Speed: {gc.CORE_CAVALRY_MOVEMENT_SPEED}",
            f"Range: {gc.CORE_CAVALRY_ATTACK_RANGE}",
            f"AI: Targets the nearest enemy, preferring units at the same height on the y-axis",
        ]
    if unit_type == UnitType.CORE_DUELIST:
        return [
            f"Name: Duelist",
            f"Faction: Core",
            f"Value: {unit_values[unit_type]}",
            f"Health: {gc.CORE_DUELIST_HP}",
            f"Attack: {round(gc.CORE_DUELIST_ATTACK_DAMAGE/7, 2)} * 7",
            f"DPS: {round(gc.CORE_DUELIST_ATTACK_DAMAGE/gc.CORE_DUELIST_ANIMATION_ATTACK_DURATION, 2)}",
            f"Speed: {gc.CORE_DUELIST_MOVEMENT_SPEED}",
            f"Range: {gc.CORE_DUELIST_ATTACK_RANGE}",
            f"AI: Targets the nearest enemy, preferring units at the same height on the y-axis",
        ]
    if unit_type == UnitType.CORE_SWORDSMAN:
        return [
            f"Name: Swordsman",
            f"Faction: Core",
            f"Value: {unit_values[unit_type]}",
            f"Health: {gc.CORE_SWORDSMAN_HP}",
            f"Attack: {gc.CORE_SWORDSMAN_ATTACK_DAMAGE}",
            f"DPS: {round(gc.CORE_SWORDSMAN_ATTACK_DAMAGE/gc.CORE_SWORDSMAN_ANIMATION_ATTACK_DURATION, 2)}",
            f"Speed: {gc.CORE_SWORDSMAN_MOVEMENT_SPEED}",
            f"Range: {gc.CORE_SWORDSMAN_ATTACK_RANGE}",
            f"AI: Targets the nearest enemy, preferring units at the same height on the y-axis",
        ]
    if unit_type == UnitType.CORE_WIZARD:
        return [
            f"Name: Wizard",
            f"Faction: Core",
            f"Value: {unit_values[unit_type]}",
            f"Health: {gc.CORE_WIZARD_HP}",
            f"Attack: {gc.CORE_WIZARD_ATTACK_DAMAGE}",
            f"DPS: {round(gc.CORE_WIZARD_ATTACK_DAMAGE/gc.CORE_WIZARD_ANIMATION_ATTACK_DURATION, 2)}",
            f"Speed: {gc.CORE_WIZARD_MOVEMENT_SPEED}",
            f"Range: {gc.CORE_WIZARD_ATTACK_RANGE}",
            f"Projectile Speed: {gc.CORE_WIZARD_PROJECTILE_SPEED}",
            f"Special: Fireball attack explodes, damaging all units in an area, including allies and the wizard itself.",
            f"AI: Targets the nearest enemy, preferring units at the same height on the y-axis",
        ]
    if unit_type == UnitType.CRUSADER_BANNER_BEARER:
        return [
            f"Name: Banner Bearer",
            f"Faction: Crusader",
            f"Value: {unit_values[unit_type]}",
            f"Health: {gc.CRUSADER_BANNER_BEARER_HP}",
            f"Speed: {gc.CRUSADER_BANNER_BEARER_MOVEMENT_SPEED}",
            f"Special: Banner Bearers have an aura which gives allied units {round(gc.CRUSADER_BANNER_BEARER_AURA_DAMAGE_PERCENTAGE*100)}% increased damage (does not stack with itself).",
            f"AI: Locks on to the nearest ally, and follows them from behind until they die, then finds a new ally to follow.",
        ]
    if unit_type == UnitType.CRUSADER_BLACK_KNIGHT:
        return [
            f"Name: Black Knight",
            f"Faction: Crusader",
            f"Value: {unit_values[unit_type]}",
            f"Health: {gc.CRUSADER_BLACK_KNIGHT_HP}",
            f"Attack: {gc.CRUSADER_BLACK_KNIGHT_ATTACK_DAMAGE}",
            f"DPS: {round(gc.CRUSADER_BLACK_KNIGHT_ATTACK_DAMAGE/gc.CRUSADER_BLACK_KNIGHT_ANIMATION_ATTACK_DURATION, 2)}",
            f"Speed: {gc.CRUSADER_BLACK_KNIGHT_MOVEMENT_SPEED}",
            f"Range: {gc.CRUSADER_BLACK_KNIGHT_ATTACK_RANGE}",
            f"Fear Duration: {gc.CRUSADER_BLACK_KNIGHT_FLEE_DURATION}",
            f"Special: Killing blows inflict fear on all other units in an AoE around the black knight.",
            f"AI: Targets nearby enemies, prioritizing enemies with low current health.",
        ]
    if unit_type == UnitType.CRUSADER_CATAPULT:
        return [
            f"Name: Catapult",
            f"Faction: Crusader",
            f"Value: {unit_values[unit_type]}",
            f"Health: {gc.CRUSADER_CATAPULT_HP}",
            f"Attack: {gc.CRUSADER_CATAPULT_DAMAGE}",
            f"DPS: {round(gc.CRUSADER_CATAPULT_DAMAGE/gc.CRUSADER_CATAPULT_ANIMATION_ATTACK_DURATION, 2)}",
            f"Speed: Immobile",
            f"Range: {gc.CRUSADER_CATAPULT_MINIMUM_RANGE} to {gc.CRUSADER_CATAPULT_MAXIMUM_RANGE}",
            f"Special: Lobs AoE projectiles that deal damage on impact.",
            f"AI: Targets the nearest enemy, preferring units at the same height on the y-axis",
        ]
    if unit_type == UnitType.CRUSADER_CLERIC:
        return [
            f"Name: Healer",
            f"Faction: Crusader",
            f"Value: {unit_values[unit_type]}",
            f"Health: {gc.CRUSADER_CLERIC_HP}",
            f"Healing: {gc.CRUSADER_CLERIC_HEALING}",
            f"Healing DPS: {round(gc.CRUSADER_CLERIC_HEALING/gc.CRUSADER_CLERIC_ANIMATION_ATTACK_DURATION, 2)}",
            f"Speed: {gc.CRUSADER_CLERIC_MOVEMENT_SPEED}",
            f"Range: {gc.CRUSADER_CLERIC_ATTACK_RANGE}",
            f"AI: Targets nearby allies, prioritizing allies who are closer and missing more health.",
        ]
    if unit_type == UnitType.CRUSADER_COMMANDER:
        return [
            f"Name: Commander",
            f"Faction: Crusader",
            f"Value: {unit_values[unit_type]}",
            f"Health: {gc.CRUSADER_COMMANDER_HP}",
            f"Attack: {gc.CRUSADER_COMMANDER_ATTACK_DAMAGE}",
            f"DPS: {round(gc.CRUSADER_COMMANDER_ATTACK_DAMAGE/gc.CRUSADER_COMMANDER_ANIMATION_ATTACK_DURATION, 2)}",
            f"Speed: {gc.CRUSADER_COMMANDER_MOVEMENT_SPEED}",
            f"Range: {gc.CRUSADER_COMMANDER_ATTACK_RANGE}",
            f"Special: Commanders have an aura which gives allied units {round(gc.CRUSADER_COMMANDER_EMPOWERED_DAMAGE_PERCENTAGE*100)}% increased damage (does not stack with itself).",
        ]
    if unit_type == UnitType.CRUSADER_CROSSBOWMAN:
        return [
            f"Name: Crossbowman",
            f"Faction: Crusader",
            f"Value: {unit_values[unit_type]}",
            f"Health: {gc.CRUSADER_CROSSBOWMAN_HP}",
            f"Attack: {gc.CRUSADER_CROSSBOWMAN_ATTACK_DAMAGE}",
            f"Firing DPS: {round(gc.CRUSADER_CROSSBOWMAN_ATTACK_DAMAGE/gc.CRUSADER_CROSSBOWMAN_ANIMATION_ATTACK_DURATION, 2)}",
            f"Average DPS: {round(gc.CRUSADER_CROSSBOWMAN_ATTACK_DAMAGE/(gc.CRUSADER_CROSSBOWMAN_ANIMATION_ATTACK_DURATION + gc.CRUSADER_CROSSBOWMAN_ANIMATION_RELOAD_DURATION), 2)}",
            f"Speed: {gc.CRUSADER_CROSSBOWMAN_MOVEMENT_SPEED}",
            f"Range: {gc.CRUSADER_CROSSBOWMAN_ATTACK_RANGE}",
            f"AI: Targets the nearest enemy, preferring units at the same height on the y-axis",
            f"Special: Has {gc.CRUSADER_CROSSBOWMAN_STARTING_AMMO} ammo to start with, and can reload to regain ammo, up to {gc.CRUSADER_CROSSBOWMAN_MAX_AMMO}.",
        ]
    if unit_type == UnitType.CRUSADER_DEFENDER:
        return [
            f"Name: Defender",
            f"Faction: Crusader",
            f"Value: {unit_values[unit_type]}",
            f"Health: {gc.CRUSADER_DEFENDER_HP}",
            f"Attack: {gc.CRUSADER_DEFENDER_ATTACK_DAMAGE}",
            f"DPS: {round(gc.CRUSADER_DEFENDER_ATTACK_DAMAGE/gc.CRUSADER_DEFENDER_ANIMATION_ATTACK_DURATION, 2)}",
            f"Speed: {gc.CRUSADER_DEFENDER_MOVEMENT_SPEED}",
            f"Range: {gc.CRUSADER_DEFENDER_ATTACK_RANGE}",
            f"AI: Targets the nearest enemy, preferring units at the same height on the y-axis",
            f"Special: Defenders have {gc.CRUSADER_DEFENDER_ARMOR_FLAT_REDUCTION}% flat armor (applied first), followed by {round(gc.CRUSADER_DEFENDER_ARMOR_PERCENT_REDUCTION*100)}% percent armor, reducing damage taken by up to {round(gc.MAX_ARMOR_DAMAGE_REDUCTION*100)}%.",
        ]
    if unit_type == UnitType.CRUSADER_GOLD_KNIGHT:
        return [
            f"Name: Gold Knight",
            f"Faction: Crusader",
            f"Value: {unit_values[unit_type]}",
            f"Health: {gc.CRUSADER_GOLD_KNIGHT_HP}",
            f"Attack: {gc.CRUSADER_GOLD_KNIGHT_ATTACK_DAMAGE}",
            f"DPS: {round(gc.CRUSADER_GOLD_KNIGHT_ATTACK_DAMAGE/gc.CRUSADER_GOLD_KNIGHT_ANIMATION_ATTACK_DURATION, 2)}",
            f"Speed: {gc.CRUSADER_GOLD_KNIGHT_MOVEMENT_SPEED}",
            f"Range: {gc.CRUSADER_GOLD_KNIGHT_ATTACK_RANGE}",
            f"AI: Targets the nearest enemy, preferring units at the same height on the y-axis",
            f"Special: Gold Knights hit all enemies in the radius of their attack, and heal for {gc.CRUSADER_GOLD_KNIGHT_ATTACK_HEAL} per enemy hit.",
        ]
    if unit_type == UnitType.CRUSADER_GUARDIAN_ANGEL:
        return [
            f"Name: Guardian Angel",
            f"Faction: Crusader",
            f"Value: {unit_values[unit_type]}",
            f"Health: {gc.CRUSADER_GUARDIAN_ANGEL_HP}",
            f"Healing: {gc.CRUSADER_GUARDIAN_ANGEL_HEALING}",
            f"Healing DPS: {round(gc.CRUSADER_GUARDIAN_ANGEL_HEALING/gc.CRUSADER_GUARDIAN_ANGEL_HEAL_COOLDOWN, 2)}",
            f"Speed: {gc.CRUSADER_GUARDIAN_ANGEL_MOVEMENT_SPEED}",
            f"Attachment Range: {gc.CRUSADER_GUARDIAN_ANGEL_ATTACHMENT_RANGE}",
            f"AI: Targets the nearest ally.",
            f"Special: Attaches to the nearest ally and heals them until they die.",
        ]
    if unit_type == UnitType.CRUSADER_LONGBOWMAN:
        return [
            f"Name: Longbowman",
            f"Faction: Crusader",
            f"Value: {unit_values[unit_type]}",
            f"Health: {gc.CRUSADER_LONGBOWMAN_HP}",
            f"Attack: {gc.CRUSADER_LONGBOWMAN_ATTACK_DAMAGE}",
            f"DPS: {round(gc.CRUSADER_LONGBOWMAN_ATTACK_DAMAGE/gc.CRUSADER_LONGBOWMAN_ANIMATION_ATTACK_DURATION, 2)}",
            f"Speed: {gc.CRUSADER_LONGBOWMAN_MOVEMENT_SPEED}",
            f"Range: {gc.CRUSADER_LONGBOWMAN_ATTACK_RANGE}",
            f"AI: Targets the nearest enemy, preferring units at the same height on the y-axis",
        ]
    if unit_type == UnitType.CRUSADER_PALADIN:
        return [
            f"Name: Paladin",
            f"Faction: Crusader",
            f"Value: {unit_values[unit_type]}",
            f"Health: {gc.CRUSADER_PALADIN_HP}",
            f"Attack: {gc.CRUSADER_PALADIN_ATTACK_DAMAGE}",
            f"DPS: {round(gc.CRUSADER_PALADIN_ATTACK_DAMAGE/gc.CRUSADER_PALADIN_ANIMATION_ATTACK_DURATION, 2)}",
            f"Speed: {gc.CRUSADER_PALADIN_MOVEMENT_SPEED}",
            f"Range: {gc.CRUSADER_PALADIN_ATTACK_RANGE}",
            f"AI: Targets the nearest enemy, preferring units at the same height on the y-axis",
            f"Special: Heals self by {round(gc.CRUSADER_PALADIN_SKILL_HEAL_PERCENT*100)}% when their health is below {round(gc.CRUSADER_PALADIN_SKILL_HEALTH_PERCENT_THRESHOLD*100)}%, cooldown {gc.CRUSADER_PALADIN_SKILL_COOLDOWN}s. (Heal per second is at most {round(gc.CRUSADER_PALADIN_SKILL_HEAL_PERCENT * gc.CRUSADER_PALADIN_HP/gc.CRUSADER_PALADIN_SKILL_COOLDOWN, 2)} per second)",
        ]
    if unit_type == UnitType.CRUSADER_PIKEMAN:
        return [
            f"Name: Pikeman",
            f"Faction: Crusader",
            f"Value: {unit_values[unit_type]}",
            f"Health: {gc.CRUSADER_PIKEMAN_HP}",
            f"Attack: {gc.CRUSADER_PIKEMAN_ATTACK_DAMAGE}",
            f"DPS: {round(gc.CRUSADER_PIKEMAN_ATTACK_DAMAGE/gc.CRUSADER_PIKEMAN_ANIMATION_ATTACK_DURATION, 2)}",
            f"Speed: {gc.CRUSADER_PIKEMAN_MOVEMENT_SPEED}",
            f"Range: {gc.CRUSADER_PIKEMAN_ATTACK_RANGE}",
            f"AI: Targets the nearest enemy, preferring units at the same height on the y-axis",
        ]
    if unit_type == UnitType.CRUSADER_RED_KNIGHT:
        return [
            f"Name: Red Knight",
            f"Faction: Crusader",
            f"Value: {unit_values[unit_type]}",
            f"Health: {gc.CRUSADER_RED_KNIGHT_HP}",
            f"Attack: {gc.CRUSADER_RED_KNIGHT_ATTACK_DAMAGE}",
            f"DPS: {round(gc.CRUSADER_RED_KNIGHT_ATTACK_DAMAGE/gc.CRUSADER_RED_KNIGHT_ANIMATION_ATTACK_DURATION, 2)}",
            f"Speed: {gc.CRUSADER_RED_KNIGHT_MOVEMENT_SPEED}",
            f"Range: {gc.CRUSADER_RED_KNIGHT_ATTACK_RANGE}",
            f"AI: Targets the nearest enemy, preferring units at the same height on the y-axis",
            f"Special: Creates an AoE of fire that hits enemies, dealing {gc.CRUSADER_RED_KNIGHT_SKILL_DAMAGE} damage and igniting for {gc.CRUSADER_RED_KNIGHT_SKILL_IGNITE_DAMAGE} over {gc.CRUSADER_RED_KNIGHT_SKILL_IGNITED_DURATION} seconds, cooldown {gc.CRUSADER_RED_KNIGHT_SKILL_COOLDOWN}s.",
        ]
    if unit_type == UnitType.CRUSADER_SOLDIER:
        return [
            f"Name: Soldier",
            f"Faction: Crusader",
            f"Value: {unit_values[unit_type]}",
            f"Health: {gc.CRUSADER_SOLDIER_HP}",
            f"Melee Attack: {gc.CRUSADER_SOLDIER_MELEE_DAMAGE}",
            f"Melee DPS: {round(gc.CRUSADER_SOLDIER_MELEE_DAMAGE/gc.CRUSADER_SOLDIER_ANIMATION_MELEE_ATTACK_DURATION, 2)}",
            f"Melee Range: {gc.CRUSADER_SOLDIER_MELEE_RANGE}",
            f"Ranged Attack: {gc.CRUSADER_SOLDIER_RANGED_DAMAGE}",
            f"Ranged DPS: {round(gc.CRUSADER_SOLDIER_RANGED_DAMAGE/gc.CRUSADER_SOLDIER_ANIMATION_RANGED_ATTACK_DURATION, 2)}",
            f"Ranged Range: {gc.CRUSADER_SOLDIER_RANGED_RANGE}",
            f"Speed: {gc.CRUSADER_SOLDIER_MOVEMENT_SPEED}",
            f"AI: Targets the nearest enemy, preferring units at the same height on the y-axis",
            f"Special: Soldiers switch from ranged attacks to melee attacks when their target is within {gc.CRUSADER_SOLDIER_SWITCH_STANCE_RANGE} units of them, and switch back to ranged attacks when their target is out of range.",
        ]
    if unit_type == UnitType.WEREBEAR:
        return [
            f"Name: Werebear",
            f"Faction: Cursed Forest",
            f"Value: {unit_values[unit_type]}",
            f"Health: {gc.WEREBEAR_HP}",
            f"Attack: {gc.WEREBEAR_ATTACK_DAMAGE}",
            f"DPS: {round(gc.WEREBEAR_ATTACK_DAMAGE/gc.WEREBEAR_ANIMATION_ATTACK_DURATION, 2)}",
            f"Speed: {gc.WEREBEAR_MOVEMENT_SPEED}",
            f"Range: {gc.WEREBEAR_ATTACK_RANGE}",
            f"AI: Targets the nearest enemy, preferring units at the same height on the y-axis",
        ]
    if unit_type == UnitType.ZOMBIE_BASIC_ZOMBIE:
        return [
            f"Name: Zombie",
            f"Faction: Zombie",
            f"Value: {unit_values[unit_type]}",
            f"Health: {gc.ZOMBIE_BASIC_ZOMBIE_HP}",
            f"Attack: {gc.ZOMBIE_BASIC_ZOMBIE_ATTACK_DAMAGE}",
            f"DPS: {round(gc.ZOMBIE_BASIC_ZOMBIE_ATTACK_DAMAGE/gc.ZOMBIE_BASIC_ZOMBIE_ANIMATION_ATTACK_DURATION, 2)}",
            f"Speed: {gc.ZOMBIE_BASIC_ZOMBIE_MOVEMENT_SPEED}",
            f"Range: {gc.ZOMBIE_BASIC_ZOMBIE_ATTACK_RANGE}",
            "Special: Zombies infect units they hit for {gc.ZOMBIE_INFECTION_DURATION} seconds, causing them to turn into zombies when they die.",
            "AI: Targets the nearest enemy, preferring units at the same height on the y-axis",
        ]
    if unit_type == UnitType.ZOMBIE_JUMPER:
        return [
            f"Name: Jumper",
            f"Faction: Zombie",
            f"Value: {unit_values[unit_type]}",
            f"Health: {gc.ZOMBIE_JUMPER_HP}",
            f"Attack: {gc.ZOMBIE_JUMPER_ATTACK_DAMAGE}",
            f"DPS: {round(gc.ZOMBIE_JUMPER_ATTACK_DAMAGE/gc.ZOMBIE_JUMPER_ANIMATION_ATTACK_DURATION, 2)}",
            f"Speed: {gc.ZOMBIE_JUMPER_MOVEMENT_SPEED}",
            f"Range: {gc.ZOMBIE_JUMPER_ATTACK_RANGE}",
            "Special: Zombies infect units they hit for {gc.ZOMBIE_INFECTION_DURATION} seconds, causing them to turn into zombies when they die.",
            f"Special: Jumps to the nearest enemy, dealing {gc.ZOMBIE_JUMPER_JUMP_DAMAGE} damage. Has a range of {gc.ZOMBIE_JUMPER_MINIMUM_JUMP_RANGE}-{gc.ZOMBIE_JUMPER_MAXIMUM_JUMP_RANGE} units, and a cooldown of {gc.ZOMBIE_JUMPER_JUMP_COOLDOWN}s.",
            f"AI: Targets nearby enemies, prioritizing enemies with low current health.",
        ]
    if unit_type == UnitType.ZOMBIE_SPITTER:
        return [
            f"Name: Spitter",
            f"Faction: Zombie",
            f"Value: {unit_values[unit_type]}",
            f"Health: {gc.ZOMBIE_SPITTER_HP}",
            f"Poison DPS: {round(gc.ZOMBIE_SPITTER_ATTACK_DAMAGE/gc.ZOMBIE_INFECTION_DURATION, 2)}",
            f"Maximum Poison DPS: {round(gc.ZOMBIE_SPITTER_ATTACK_DAMAGE/gc.ZOMBIE_SPITTER_ANIMATION_ATTACK_DURATION, 2)}",
            f"Melee Damage: {gc.ZOMBIE_BASIC_ZOMBIE_ATTACK_DAMAGE}",
            f"Melee DPS: {round(gc.ZOMBIE_BASIC_ZOMBIE_ATTACK_DAMAGE/gc.ZOMBIE_BASIC_ZOMBIE_ANIMATION_ATTACK_DURATION, 2)}",
            f"Speed: {gc.ZOMBIE_SPITTER_MOVEMENT_SPEED}",
            f"Range: {gc.ZOMBIE_SPITTER_ATTACK_RANGE}",
            f"Projectile Speed: {gc.ZOMBIE_SPITTER_PROJECTILE_SPEED}",
            f"Special: Spitters projectiles infect units they hit for {gc.ZOMBIE_INFECTION_DURATION} seconds, causing them to turn into zombies when they die.",
            f"Special: Spitter projectiles can only collide with non-infected enemies.",
            f"Special: Spitter projectiles deal {gc.ZOMBIE_SPITTER_ATTACK_DAMAGE} damage over {gc.ZOMBIE_INFECTION_DURATION} seconds.",
            f"AI: Targets the nearest enemy, preferring units that are infectable and are at the same height on the y-axis",
        ]
    if unit_type == UnitType.ZOMBIE_TANK:
        return [
            f"Name: Tank",
            f"Faction: Zombie",
            f"Value: {unit_values[unit_type]}",
            f"Health: {gc.ZOMBIE_TANK_HP}",
            f"Attack: {gc.ZOMBIE_TANK_ATTACK_DAMAGE}",
            f"DPS: {round(gc.ZOMBIE_TANK_ATTACK_DAMAGE/gc.ZOMBIE_TANK_ANIMATION_ATTACK_DURATION, 2)}",
            f"Speed: {gc.ZOMBIE_TANK_MOVEMENT_SPEED}",
            f"Range: {gc.ZOMBIE_TANK_ATTACK_RANGE}",
            f"Special: Zombies infect units they hit for {gc.ZOMBIE_INFECTION_DURATION} seconds, causing them to turn into zombies when they die.",
            "AI: Targets the nearest enemy, preferring units at the same height on the y-axis",
        ]
    raise NotImplementedError(unit_type)
