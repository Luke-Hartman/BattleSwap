"""Processor for status effects."""

from components.dying import Dying
from components.on_kill_effects import OnKillEffects
from components.health import Health
from components.status_effect import InfantryBannerBearerEmpowered, InfantryBannerBearerMovementSpeedBuff, InfantryBannerBearerAbilitySpeedBuff, Fleeing, Healing, DamageOverTime, Slowed, StatusEffects, WontPursue, ZombieInfection, Invisible, Immobilized, ReviveProgress
from components.unit_type import UnitTypeComponent
from effects import Revive
from game_constants import gc
from effects import PlaySound, SoundEffect
from point_values import unit_values
import esper

from components.unit_state import State, UnitState

class StatusEffectProcessor(esper.Processor):
    """Processor for status effects."""

    def process(self, dt: float):
        for ent, (status_effects,) in esper.get_components(StatusEffects):
            status_effects.update(dt)
            for status_effect in status_effects.active_effects():
                if isinstance(status_effect, DamageOverTime):
                    if esper.component_for_entity(ent, UnitState).state != State.DEAD:
                        damage = status_effect.dps * dt
                        health = esper.component_for_entity(ent, Health)
                        previous_health = health.current
                        health.current = max(health.current - damage, 0)
                        if health.current == 0 and previous_health > 0:
                            esper.add_component(ent, Dying())
                            # Check for OnKillEffects component on the owner (but not if killing self)
                            if status_effect.owner and status_effect.owner != ent and esper.has_component(status_effect.owner, OnKillEffects):
                                on_kill_effects = esper.component_for_entity(status_effect.owner, OnKillEffects)
                                for effect in on_kill_effects.effects:
                                    effect.apply(status_effect.owner, ent, ent)
                elif isinstance(status_effect, InfantryBannerBearerEmpowered):
                    # Handled in the damage effect
                    pass
                elif isinstance(status_effect, InfantryBannerBearerMovementSpeedBuff):
                    # Handled in the pursuing processor
                    pass
                elif isinstance(status_effect, InfantryBannerBearerAbilitySpeedBuff):
                    # Handled in the animation processor
                    pass
                elif isinstance(status_effect, Fleeing):
                    # Handled in the fleeing processor
                    pass
                elif isinstance(status_effect, Healing):
                    heal = status_effect.dps * dt
                    health = esper.component_for_entity(ent, Health)
                    health.current = min(health.current + heal, health.maximum)
                elif isinstance(status_effect, ZombieInfection):
                    # Handled in the dying processor
                    pass
                elif isinstance(status_effect, Invisible):
                    pass # Handled in the transparency processor
                elif isinstance(status_effect, Immobilized):
                    pass # Handled in the movement processor
                elif isinstance(status_effect, WontPursue):
                    pass # Handled in the targeting processor
                elif isinstance(status_effect, ReviveProgress):
                    # Handled in the revive processing logic below
                    pass
                elif isinstance(status_effect, Slowed):
                    pass # Handled in the pursuing processor
                else:
                    raise ValueError(f"Unknown status effect: {status_effect}")
        
        # Process ReviveProgress effects for dead units
        for ent, (unit_state, status_effects) in esper.get_components(UnitState, StatusEffects):
            if unit_state.state != State.DEAD:
                continue
                
            # Get all ReviveProgress effects for this unit
            revive_progress_effects = status_effects._status_by_type.get(ReviveProgress, [])
            if not revive_progress_effects:
                continue
                
            # Calculate net stacks by team
            team_stacks = {}
            for effect in revive_progress_effects:
                team = effect.team
                if team not in team_stacks:
                    team_stacks[team] = 0
                team_stacks[team] += effect.stacks
                
            winning_team = max(team_stacks.keys(), key=lambda t: team_stacks[t])
            total_stacks = team_stacks[winning_team]
            
            # Get the unit's point value to determine if we have enough stacks
            unit_type = esper.component_for_entity(ent, UnitTypeComponent).type
            point_value = unit_values[unit_type]

            # Check if we have enough stacks to revive
            if total_stacks >= point_value:
                # Get all ReviveProgress effects from the winning team
                winning_team_effects = [effect for effect in revive_progress_effects if effect.team == winning_team]
                
                if not winning_team_effects:
                    continue
                
                # Find the highest tier among all effects from the winning team
                highest_tier = max(winning_team_effects, key=lambda e: e.tier.value).tier
                
                # Assert that all corruption powers match (or are all None)
                corruption_powers = winning_team_effects[0].corruption_powers
                for effect in winning_team_effects[1:]:
                    if effect.corruption_powers != corruption_powers:
                        raise AssertionError("Corruption powers do not match")
                
                # Revive the unit on the winning team with the highest tier and matching corruption powers
                Revive(team=winning_team, tier=highest_tier, corruption_powers=corruption_powers).apply(owner=None, parent=None, target=ent)
                # TODO: better way to handle this?
                PlaySound(SoundEffect(filename="skeleton_lich_ability.wav", volume=0.2)).apply(owner=None, parent=None, target=None)
                PlaySound(SoundEffect(filename="revive.wav", volume=0.2)).apply(owner=None, parent=None, target=None)
                # Remove all ReviveProgress effects from this unit
                status_effects._status_by_type[ReviveProgress] = []

