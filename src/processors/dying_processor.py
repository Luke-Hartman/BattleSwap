"""Processor for units that are dying."""

import esper
from components.corpse_timer import CorpseTimer
from components.dying import Dying
from components.on_death_effects import OnDeathEffect
from components.forced_movement import ForcedMovement
from components.position import Position
from components.sprite_sheet import SpriteSheet
from components.team import Team, TeamType
from components.unit_tier import UnitTier
from components.unit_type import UnitType, UnitTypeComponent
from components.transparent import Transparency
from components.unusable_corpse import UnusableCorpse
from effects import PlaySound, SoundEffect
from entities.units import create_unit
from events import DEATH, PLAY_SOUND, DeathEvent, emit_event
from progress_manager import progress_manager
from unit_condition import Infected
from voice import play_death
from components.summoned import SummonedBy
from components.status_effect import StatusEffects, ExplodeOnDeath as ExplodeOnDeathEffect

class DyingProcessor(esper.Processor):
    """Processor for units that are dying."""

    def process(self, dt: float):
        for ent, (_, unit_type) in esper.get_components(Dying, UnitTypeComponent):
            if esper.has_component(ent, ForcedMovement):
                continue
            esper.add_component(ent, CorpseTimer())
            emit_event(DEATH, event=DeathEvent(ent))
            play_death(unit_type.type)
            
            # Handle on death effects
            if esper.has_component(ent, OnDeathEffect):
                on_death = esper.component_for_entity(ent, OnDeathEffect)
                if on_death.condition is None or on_death.condition.check(ent):
                    for effect in on_death.effects:
                        effect.apply(owner=ent, parent=ent, target=None)

            # If a necromancer dies, kill only their summons
            if unit_type.type in (
                UnitType.SKELETON_ARCHER_NECROMANCER,
                UnitType.SKELETON_HORSEMAN_NECROMANCER,
                UnitType.SKELETON_MAGE_NECROMANCER,
                UnitType.SKELETON_SWORDSMAN_NECROMANCER,
            ):
                for summoned_ent, summoned in esper.get_component(SummonedBy):
                    if summoned.summoner == ent and not esper.has_component(summoned_ent, Dying):
                        esper.add_component(summoned_ent, Dying())

            # Handle zombie infection
            zombie_infection = Infected().get_active_zombie_infection(ent)
            if zombie_infection and not esper.has_component(ent, UnusableCorpse):
                position = esper.component_for_entity(ent, Position)
                team = esper.component_for_entity(ent, Team)
                
                # Determine the appropriate tier for the zombie
                if team.type == TeamType.TEAM1 and progress_manager:
                    # Player units should create zombies of the player's zombie tier
                    tier = progress_manager.get_unit_tier(UnitType.ZOMBIE_BASIC_ZOMBIE)
                else:
                    if zombie_infection.corruption_powers is not None:
                        tier = UnitTier.ELITE
                    else:
                        tier = UnitTier.BASIC
                
                create_unit(
                    x=position.x,
                    y=position.y,
                    team=zombie_infection.team,
                    unit_type=UnitType.ZOMBIE_BASIC_ZOMBIE,
                    corruption_powers=zombie_infection.corruption_powers,
                    tier=tier,
                    play_spawning=False # Changed my mind about this, not using the play_spawning flag for anything right now.
                )
                # This is a hack to hide the corpse of the unit
                if esper.has_component(ent, SpriteSheet):
                    esper.remove_component(ent, SpriteSheet)
                PlaySound([
                    (SoundEffect(filename=f"zombie_grunt_{i+1}.wav", volume=0.5), 1.0) for i in range(3)
                ]).apply(owner=None, parent=None, target=None)
            
            # Handle explode on death status effect
            if esper.has_component(ent, StatusEffects):
                status_effects = esper.component_for_entity(ent, StatusEffects)
                active_effects = status_effects.active_effects()
                explode_effect = next((e for e in active_effects if isinstance(e, ExplodeOnDeathEffect)), None)
                
                if explode_effect:
                    from effects import CreatesCircleAoE, Damages, CreatesVisual, Recipient
                    from unit_condition import All, Alive, Grounded
                    from visuals import Visual
                    from game_constants import gc
                    
                    # Create explosion effects
                    CreatesCircleAoE(
                        effects=[
                            Damages(damage=explode_effect.damage, recipient=Recipient.TARGET, is_melee=False),
                        ],
                        radius=explode_effect.radius,
                        unit_condition=All([Alive(), Grounded()]),
                        location=Recipient.OWNER,
                    ).apply(owner=ent, parent=ent, target=None)
                    
                    CreatesVisual(
                        recipient=Recipient.OWNER,
                        visual=Visual.Explosion,
                        animation_duration=gc.CORE_WIZARD_FIREBALL_AOE_DURATION,
                        scale=explode_effect.radius * gc.EXPLOSION_VISUAL_SCALE_RATIO,
                        duration=gc.CORE_WIZARD_FIREBALL_AOE_DURATION,
                        layer=2,
                    ).apply(owner=ent, parent=ent, target=None)
                    
                    PlaySound(SoundEffect(filename="fireball_impact.wav", volume=0.50)).apply(owner=None, parent=None, target=None)
            
            esper.remove_component(ent, Dying)
