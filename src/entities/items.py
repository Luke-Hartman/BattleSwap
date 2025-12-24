"""Module for handling items in the game."""

from abc import ABC, abstractmethod
from typing import Dict
import esper
import pygame
import os
from components.health import Health
from components.on_death_effects import OnDeathEffect
from components.on_hit_effects import OnHitEffects
from components.armor import Armor, ArmorLevel
from components.aura import Auras, Aura
from components.position import Position
from components.attached import Attached
from components.expiration import Expiration
from components.movement import Movement
from components.corruption import IncreasedMovementSpeedComponent
from components.team import Team
from components.instant_ability import InstantAbilities, InstantAbility
from components.ability import TargetStrategy, Cooldown
from components.status_effect import Invisible, StatusEffects
from unit_condition import All, Alive, Grounded, Always, HasComponent, NotHeavilyArmored, HasDefaultTargetingStrategies, Not, IsUnitType, HasItem
from effects import CreatesCircleAoE, CreatesVisual, Damages, PlaySound, Recipient, SoundEffect, Effect, AppliesStatusEffect, OnKillEffects, HealPercentageMax, CreatesAttachedVisual
from visuals import Visual
from components.status_effect import DamageOverTime, ZombieInfection
from components.unit_type import UnitType
from components.item import ItemType
from components.static import StaticComponent
from game_constants import gc
from unit_condition import UnitCondition

class Item(ABC):
    """Base class for all items."""
    
    @abstractmethod
    def apply(self, entity: int) -> None:
        """Apply the item's effect to the given entity."""
        pass
    
    @classmethod
    @abstractmethod
    def get_unit_condition(cls) -> UnitCondition:
        """Return the unit condition that determines which units this item can be applied to."""
        pass

class ExtraHealth(Item):
    """Grants extra HP to the equipped unit."""

    def apply(self, entity: int) -> None:
        """Apply health bonus to the entity."""
        if esper.has_component(entity, Health):
            health = esper.component_for_entity(entity, Health)
            health.current += gc.ITEM_EXTRA_HEALTH_HEALTH_BONUS
            health.maximum += gc.ITEM_EXTRA_HEALTH_HEALTH_BONUS
    
    
    @classmethod
    def get_unit_condition(cls) -> UnitCondition:
        """Return the unit condition for this item."""
        return Always()


class ExplodeOnDeath(Item):
    """An item that creates an explosion when the unit dies, damaging all nearby units."""
    
    def apply(self, entity: int) -> None:
        """Add death explosion effect to the entity."""
        death_effect = esper.component_for_entity(entity, OnDeathEffect)
        death_effect.effects.extend([
            CreatesCircleAoE(
                effects=[
                    Damages(damage=gc.ITEM_EXPLODE_ON_DEATH_DAMAGE, recipient=Recipient.TARGET, is_melee=False),
                ],
                radius=gc.ITEM_EXPLODE_ON_DEATH_AOE_RADIUS,
                unit_condition=All([Alive(), Grounded()]),  # Hits both allies and enemies
                location=Recipient.OWNER,
            ),
            CreatesVisual(
                recipient=Recipient.OWNER,
                visual=Visual.Explosion,
                animation_duration=gc.CORE_WIZARD_FIREBALL_AOE_DURATION,  # Same duration as wizard fireball
                scale=gc.ITEM_EXPLODE_ON_DEATH_AOE_RADIUS * gc.EXPLOSION_VISUAL_SCALE_RATIO,
                duration=gc.CORE_WIZARD_FIREBALL_AOE_DURATION,
                layer=2,
            ),
            PlaySound(SoundEffect(filename="fireball_impact.wav", volume=0.50)),  # Same sound as wizard fireball
        ])
    
    
    @classmethod
    def get_unit_condition(cls) -> UnitCondition:
        """Return the unit condition for this item."""
        return Always()


class UpgradeArmor(Item):
    """Upgrades a unit's armor. If no armor, adds normal armor. If normal armor, upgrades to heavily armored."""
    
    def apply(self, entity: int) -> None:
        """Apply armor upgrade to the entity."""
        if not esper.has_component(entity, Armor):
            # No armor - add normal armor
            esper.add_component(entity, Armor(level=ArmorLevel.NORMAL))
        else:
            # Has armor - upgrade to heavily armored
            armor = esper.component_for_entity(entity, Armor)
            armor.level = ArmorLevel.HEAVILY
    
    
    @classmethod
    def get_unit_condition(cls) -> UnitCondition:
        """Return the unit condition for this item - can only be applied to units that are not heavily armored."""
        return NotHeavilyArmored()


class DamageAura(Item):
    """Grants the unit a red aura that deals damage to all units in range, including itself."""
    
    def apply(self, entity: int) -> None:
        """Apply damage aura to the entity."""
        # Get or create the Auras component
        if esper.has_component(entity, Auras):
            auras = esper.component_for_entity(entity, Auras)
        else:
            auras = Auras()
            esper.add_component(entity, auras)
        
        # Create and add the damage aura
        damage_aura = Aura(
            owner=entity,
            radius=gc.ITEM_DAMAGE_AURA_RADIUS,
            effects=[
                AppliesStatusEffect(
                    status_effect=DamageOverTime(dps=gc.ITEM_DAMAGE_AURA_DAMAGE_PER_SECOND, time_remaining=gc.DEFAULT_AURA_PERIOD, owner=entity),
                    recipient=Recipient.TARGET
                )
            ],
            color=(255, 0, 0),  # Red color
            period=gc.DEFAULT_AURA_PERIOD,
            owner_condition=Alive(),
            unit_condition=Alive(),
            duration=float('inf')  # Permanent
        )
        # Add a marker to identify this as a damage aura
        damage_aura._aura_type = DamageAura
        auras.auras.append(damage_aura)
    
    
    @classmethod
    def get_unit_condition(cls) -> UnitCondition:
        """Return the unit condition for this item."""
        return Always()


class ExtraMovementSpeed(Item):
    """Grants extra movement speed to the equipped unit."""
    
    def apply(self, entity: int) -> None:
        """Apply movement speed bonus to the entity."""
        movement = esper.component_for_entity(entity, Movement)
        movement.speed += gc.ITEM_EXTRA_MOVEMENT_SPEED_BONUS
    
    
    @classmethod
    def get_unit_condition(cls) -> UnitCondition:
        """Return the unit condition for this item."""
        return HasComponent(Movement)


class InfectOnHit(Item):
    """Grants zombie infection on hit."""
    
    def apply(self, entity: int) -> None:
        """Apply infect on hit effect to the entity."""
        # Add OnHitEffects component for zombie infection on hit
        esper.add_component(
            entity,
            OnHitEffects(
                effects=[
                    AppliesStatusEffect(
                        status_effect=ZombieInfection(
                            time_remaining=gc.ZOMBIE_INFECTION_DURATION, 
                            team=esper.component_for_entity(entity, Team).type,
                            corruption_powers=None, 
                            owner=entity
                        ),
                        recipient=Recipient.TARGET
                    )
                ]
            )
        )
    
    
    @classmethod
    def get_unit_condition(cls) -> UnitCondition:
        """Return the unit condition for this item."""
        return Always()


class Hunter(Item):
    """Grants hunter targeting behavior - prioritizes low health enemies."""
    
    def apply(self, entity: int) -> None:
        """Apply hunter targeting to the entity."""
        from targeting_strategy_factory import replace_targeting_strategies, TargetingStrategyType
        
        # Replace all DEFAULT targeting strategies with HUNTER
        replace_targeting_strategies(entity, TargetingStrategyType.DEFAULT, TargetingStrategyType.HUNTER)
    
    @classmethod
    def get_unit_condition(cls) -> UnitCondition:
        """Return the unit condition for this item."""
        return HasDefaultTargetingStrategies()


class HealOnKill(Item):
    """Grants healing for half of maximum health when the unit gets a kill."""
    
    def apply(self, entity: int) -> None:
        """Apply heal on kill effect to the entity."""
        # Add OnKillEffects component for healing on kill
        if not esper.has_component(entity, OnKillEffects):
            esper.add_component(entity, OnKillEffects(effects=[]))
        on_kill_effects = esper.component_for_entity(entity, OnKillEffects)
        on_kill_effects.effects.extend(
            [
                HealPercentageMax(
                    recipient=Recipient.OWNER,
                    percentage=0.5,
                    duration=1.0
                ),
                PlaySound([
                    (SoundEffect(filename=f"heal.wav", volume=0.50), 1.0)
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
    
    @classmethod
    def get_unit_condition(cls) -> UnitCondition:
        """Return the unit condition for this item."""
        return Always()


class ReflectDamage(Item):
    """Reflects a percentage of melee damage taken back to the attacker."""
    
    def apply(self, entity: int) -> None:
        """Apply reflect damage effect to the entity."""
        # pass
        # This is handled in the Damages effect.
    
    @classmethod
    def get_unit_condition(cls) -> UnitCondition:
        """Return the unit condition for this item."""
        return Always()


class StartInvisible(Item):
    """Grants invisibility at the start of combat."""
    
    def apply(self, entity: int) -> None:
        """Apply start invisible effect to the entity."""
        from target_strategy import TargetingGroup, TargetStrategy, ByDistance
        from unit_condition import Never
        # Apply invisibility status effect directly so unit starts invisible
        if esper.has_component(entity, StatusEffects):
            status_effects = esper.component_for_entity(entity, StatusEffects)
            status_effects.add(Invisible(time_remaining=gc.ITEM_START_INVISIBLE_DURATION, owner=entity))
        # Add instant ability to play sound when round starts
        if not esper.has_component(entity, InstantAbilities):
            esper.add_component(entity, InstantAbilities(abilities=[]))
        instant_abilities = esper.component_for_entity(entity, InstantAbilities)
        instant_abilities.abilities.append(
            InstantAbility(
                target_strategy=TargetStrategy(
                    rankings=[ByDistance(entity=entity, y_bias=2, ascending=True)],
                    unit_condition=Never(),
                    targetting_group=TargetingGroup.EMPTY
                ),
                trigger_conditions=[
                    Cooldown(duration=float("inf")),
                ],
                effects=[
                    AppliesStatusEffect(
                        status_effect=Invisible(time_remaining=gc.ITEM_START_INVISIBLE_DURATION, owner=entity),
                        recipient=Recipient.OWNER
                    ),
                    PlaySound(SoundEffect(filename="start_invisible.wav", volume=0.30))
                ]
            )
        )

    @classmethod
    def get_unit_condition(cls) -> UnitCondition:
        """Return the unit condition for this item."""
        return All([
            Not(IsUnitType(UnitType.ORC_GOBLIN)),
            Not(HasItem(ItemType.START_INVISIBLE))
        ])


class StaticDischarge(Item):
    """Grants static buildup that discharges as extra damage when dealing damage."""
    
    def apply(self, entity: int) -> None:
        """Apply static discharge effect to the entity."""
        if not esper.has_component(entity, StaticComponent):
            esper.add_component(entity, StaticComponent())
        else:
            static_component = esper.component_for_entity(entity, StaticComponent)
            static_component.stacks += 1
    
    @classmethod
    def get_unit_condition(cls) -> UnitCondition:
        """Return the unit condition for this item."""
        return Always()


# Item theme IDs for UI styling
item_theme_ids: Dict[ItemType, str] = {
    ItemType.EXTRA_HEALTH: "#extra_health_icon",
    ItemType.EXPLODE_ON_DEATH: "#explode_on_death_icon",
    ItemType.UPGRADE_ARMOR: "#upgrade_armor_icon",
    ItemType.DAMAGE_AURA: "#damage_aura_icon",
    ItemType.EXTRA_MOVEMENT_SPEED: "#extra_movement_speed_icon",
    ItemType.HEAL_ON_KILL: "#heal_on_kill_icon",
    ItemType.INFECT_ON_HIT: "#infect_on_hit_icon",
    ItemType.HUNTER: "#hunter_icon",
    ItemType.REFLECT_DAMAGE: "#reflect_damage_icon",
    ItemType.START_INVISIBLE: "#start_invisible_icon",
    ItemType.STATIC_DISCHARGE: "#static_discharge_icon"
}

# Item icon surfaces for rendering
item_icon_surfaces: Dict[ItemType, pygame.Surface] = {}

# Item registry
item_registry: Dict[ItemType, Item] = {
    ItemType.EXTRA_HEALTH: ExtraHealth(),
    ItemType.EXPLODE_ON_DEATH: ExplodeOnDeath(),
    ItemType.UPGRADE_ARMOR: UpgradeArmor(),
    ItemType.DAMAGE_AURA: DamageAura(),
    ItemType.EXTRA_MOVEMENT_SPEED: ExtraMovementSpeed(),
    ItemType.HEAL_ON_KILL: HealOnKill(),
    ItemType.INFECT_ON_HIT: InfectOnHit(),
    ItemType.HUNTER: Hunter(),
    ItemType.REFLECT_DAMAGE: ReflectDamage(),
    ItemType.START_INVISIBLE: StartInvisible(),
    ItemType.STATIC_DISCHARGE: StaticDischarge()
}


def load_item_icons() -> None:
    """Load all item icons."""
    item_icon_paths: Dict[ItemType, str] = {
        ItemType.EXTRA_HEALTH: "ExtraHealthIcon.png",
        ItemType.EXPLODE_ON_DEATH: "ExplodeOnDeathIcon.png",
        ItemType.UPGRADE_ARMOR: "UpgradeArmorIcon.png",
        ItemType.DAMAGE_AURA: "DamageAuraIcon.png",
        ItemType.EXTRA_MOVEMENT_SPEED: "ExtraMovementSpeedIcon.png",
        ItemType.HEAL_ON_KILL: "HealOnKillIcon.png",
        ItemType.INFECT_ON_HIT: "InfectOnHitIcon.png",
        ItemType.HUNTER: "HunterIcon.png",
        ItemType.REFLECT_DAMAGE: "ReflectDamageIcon.png",
        ItemType.START_INVISIBLE: "StartInvisibleIcon.png",
        ItemType.STATIC_DISCHARGE: "StaticDischargeIcon.png"
    }
    
    for item_type, filename in item_icon_paths.items():
        if item_type in item_icon_surfaces:
            continue
        path = os.path.join("assets", "icons", filename)
        item_icon_surfaces[item_type] = pygame.image.load(path).convert_alpha()