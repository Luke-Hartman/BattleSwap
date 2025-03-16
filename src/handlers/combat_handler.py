"""Combat handler module for Battle Swap.

This module contains the CombatHandler class, which is responsible for
handling attack/skill/AoE/etc logic and applying damage/healing from attacks/skills/AoEs/etc.
"""

import esper
from components.ability import Abilities
from components.aoe import VisualAoE, CircleAoE
from components.aura import Aura
from components.instant_ability import InstantAbilities
from components.lobbed import Lobbed
from components.projectile import Projectile
from events import (
    LOBBED_ARRIVED, AbilityActivatedEvent, ABILITY_ACTIVATED,
    AuraHitEvent, AURA_HIT, LobbedArrivedEvent,
    ProjectileHitEvent, PROJECTILE_HIT,
    InstantAbilityTriggeredEvent, INSTANT_ABILITY_TRIGGERED, VisualAoEHitEvent, CircleAoEHitEvent, VISUAL_AOE_HIT, CIRCLE_AOE_HIT
)
from pydispatch import dispatcher

class CombatHandler:
    """Handler responsible for handling attack logic and applying damage."""

    def __init__(self):
        dispatcher.connect(self.handle_ability_activated, signal=ABILITY_ACTIVATED)
        dispatcher.connect(self.handle_instant_ability_triggered, signal=INSTANT_ABILITY_TRIGGERED)
        dispatcher.connect(self.handle_projectile_hit, signal=PROJECTILE_HIT)
        dispatcher.connect(self.handle_visual_aoe_hit, signal=VISUAL_AOE_HIT)
        dispatcher.connect(self.handle_circle_aoe_hit, signal=CIRCLE_AOE_HIT)
        dispatcher.connect(self.handle_aura_hit, signal=AURA_HIT)
        dispatcher.connect(self.handle_lobbed_arrived, signal=LOBBED_ARRIVED)

    def handle_ability_activated(self, event: AbilityActivatedEvent):
        owner = event.entity
        abilities = esper.component_for_entity(owner, Abilities)
        ability = abilities.abilities[event.index]
        for effect in ability.effects[event.frame]:
            effect.apply(
                owner=owner,
                parent=owner,
                target=ability.target
            )
    def handle_instant_ability_triggered(self, event: InstantAbilityTriggeredEvent):
        owner = event.entity
        instant_abilities = esper.component_for_entity(owner, InstantAbilities)
        ability = instant_abilities.abilities[event.index]
        for effect in ability.effects:
            effect.apply(
                owner=owner,
                parent=owner,
                target=ability.target_strategy.target
            )

    def handle_projectile_hit(self, event: ProjectileHitEvent):
        projectile_ent = event.entity
        target_ent = event.target
        projectile = esper.component_for_entity(projectile_ent, Projectile)
        for effect in projectile.effects:
            effect.apply(
                owner=projectile.owner,
                parent=projectile_ent,
                target=target_ent
            )

    def handle_visual_aoe_hit(self, event: VisualAoEHitEvent):
        aoe_ent = event.entity
        target_ent = event.target
        aoe = esper.component_for_entity(aoe_ent, VisualAoE)
        for effect in aoe.effects:
            effect.apply(
                owner=aoe.owner,
                parent=aoe_ent,
                target=target_ent
            )
    
    def handle_circle_aoe_hit(self, event: CircleAoEHitEvent):
        aoe_ent = event.entity
        target_ent = event.target
        aoe = esper.component_for_entity(aoe_ent, CircleAoE)
        for effect in aoe.effects:
            effect.apply(
                owner=aoe.owner,
                parent=aoe_ent,
                target=target_ent
            )

    def handle_aura_hit(self, event: AuraHitEvent):
        aura_ent = event.entity
        target_ent = event.target
        aura = esper.component_for_entity(aura_ent, Aura)
        if aura.unit_condition.check(target_ent):
            for effect in aura.effects:
                effect.apply(
                    owner=aura.owner,
                    parent=aura_ent,
                    target=target_ent
                )

    def handle_lobbed_arrived(self, event: LobbedArrivedEvent):
        lobbed_ent = event.entity
        lobbed = esper.component_for_entity(lobbed_ent, Lobbed)
        for effect in lobbed.effects:
            effect.apply(
                owner=lobbed.owner,
                parent=lobbed_ent,
                target=None,
            )
