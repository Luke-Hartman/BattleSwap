"""
Animation processor module for Battle Swap.

This module contains the AnimationProcessor class, which is responsible for
updating the current frame of entities with AnimationState components.

Also triggers events based on frame changes.
"""

import esper
from components.ability import Abilities
from components.animation import AnimationState, AnimationType
from components.corruption import IncreasedAbilitySpeedComponent
from components.status_effect import StatusEffects, CrusaderBannerBearerAbilitySpeedBuff
from components.destination import Destination
from components.forced_movement import ForcedMovement
from components.movement import Movement
from components.smooth_movement import SmoothMovement
from components.sprite_sheet import SpriteSheet
from components.unit_state import UnitState, State
from components.velocity import Velocity
from components.animation_effects import AnimationEffects
from components.airborne import Airborne
from events import ABILITY_ACTIVATED, ABILITY_COMPLETED, SPAWNING_COMPLETED, AbilityActivatedEvent, AbilityCompletedEvent, SpawningCompletedEvent, emit_event
import timing

class AnimationProcessor(esper.Processor):
    """
    Processor responsible for updating animation frames.
    """

    def __init__(self) -> None:
        """
        Initialize the AnimationProcessor.
        """
        super().__init__()
    
    def _get_start_time(self, sprite_sheet: SpriteSheet, animation_type: AnimationType) -> float:
        if sprite_sheet.synchronized_animations.get(animation_type, False):
            return timing.get_global_clock() % sprite_sheet.animation_durations[animation_type]
        else:
            return 0

    def process(self, dt: float):
        """
        Process all entities with AnimationState components and update their current frame.

        Args:
            dt (float): Delta time since last frame, in seconds.
        """
        for ent, (anim_state, sprite_sheet) in esper.get_components(AnimationState, SpriteSheet):
            if esper.has_component(ent, UnitState):
                unit_state = esper.component_for_entity(ent, UnitState)
            else:
                unit_state = UnitState(state=State.IDLE)

            # First determine base animation from state
            new_anim_type = {
                State.IDLE: AnimationType.IDLE,
                State.PURSUING: AnimationType.WALKING,
                State.FLEEING: AnimationType.WALKING,
                State.ABILITY1: AnimationType.ABILITY1,
                State.ABILITY2: AnimationType.ABILITY2,
                State.ABILITY3: AnimationType.ABILITY3,
                State.ABILITY4: AnimationType.ABILITY4,
                State.ABILITY5: AnimationType.ABILITY5,
                State.DEAD: AnimationType.DYING,
                State.SPAWNING: AnimationType.SPAWNING
            }[unit_state.state]

            # Override with airborne animation if airborne
            if esper.has_component(ent, Airborne) and new_anim_type != AnimationType.DYING:
                new_anim_type = AnimationType.AIRBORNE

            # Override with first frame of IDLE animation if forced movement
            if esper.has_component(ent, ForcedMovement):
                new_anim_type = AnimationType.IDLE
                anim_state.current_frame = 0
                anim_state.time_elapsed = self._get_start_time(sprite_sheet, new_anim_type)

            if unit_state.state == State.PURSUING:
                if esper.has_component(ent, Destination):
                    destination = esper.component_for_entity(ent, Destination)
                    if destination.target_strategy.target is not None:
                        velocity = esper.component_for_entity(ent, Velocity)
                        target_velocity = esper.component_for_entity(destination.target_strategy.target, Velocity)
                        if velocity.x == velocity.y == target_velocity.x == target_velocity.y == 0:
                            new_anim_type = AnimationType.IDLE
            
            if anim_state.time_elapsed is None:
                anim_state.time_elapsed = self._get_start_time(sprite_sheet, new_anim_type)

            if anim_state.type != new_anim_type:
                anim_state.type = new_anim_type
                anim_state.current_frame = 0
                anim_state.time_elapsed = self._get_start_time(sprite_sheet, new_anim_type)
            else:
                if anim_state.type == AnimationType.WALKING and not esper.has_component(ent, SmoothMovement):
                    # If the unit is moving faster/slower than it's normal movement speed, scale the animation speed
                    velocity = esper.component_for_entity(ent, Velocity)
                    movement = esper.component_for_entity(ent, Movement)
                    if movement.speed != 0:
                        scale = (velocity.x**2 + velocity.y**2)**0.5 / movement.speed
                    else:
                        scale = 1
                    anim_state.time_elapsed += dt * scale
                else:
                    # Check for ability speed increases from corruption powers or status effects
                    speed_multiplier = 1.0
                    
                    if esper.has_component(ent, IncreasedAbilitySpeedComponent):
                        speed_multiplier *= (1 + esper.component_for_entity(ent, IncreasedAbilitySpeedComponent).increase_percent / 100)
                    
                    if esper.has_component(ent, StatusEffects):
                        status_effects = esper.component_for_entity(ent, StatusEffects)
                        for status_effect in status_effects.active_effects():
                            if isinstance(status_effect, CrusaderBannerBearerAbilitySpeedBuff):
                                speed_multiplier *= (1 + status_effect.ability_speed_increase_percent / 100)
                    
                    anim_state.time_elapsed += dt * speed_multiplier

            # Update the animation frame based on the current time
            total_duration = sprite_sheet.animation_durations[anim_state.type]
            frame_count = sprite_sheet.frames[anim_state.type]
            frame_duration = total_duration / frame_count

            new_frame = min(frame_count, int(anim_state.time_elapsed // frame_duration))
            if new_frame != anim_state.current_frame or anim_state.time_elapsed == 0:
                if anim_state.type == AnimationType.DYING and anim_state.current_frame == frame_count - 1:
                    # Stop the animation at the last frame for death animation
                    pass
                else:
                    anim_state.current_frame = new_frame

                # Check if ability is activated
                index = None
                if unit_state.state == State.ABILITY1 and anim_state.type == AnimationType.ABILITY1:
                    index = 0
                elif unit_state.state == State.ABILITY2 and anim_state.type == AnimationType.ABILITY2:
                    index = 1
                elif unit_state.state == State.ABILITY3 and anim_state.type == AnimationType.ABILITY3:
                    index = 2
                elif unit_state.state == State.ABILITY4 and anim_state.type == AnimationType.ABILITY4:
                    index = 3
                elif unit_state.state == State.ABILITY5 and anim_state.type == AnimationType.ABILITY5:
                    index = 4

                if index is not None:
                    ability = esper.component_for_entity(ent, Abilities).abilities[index]
                    if ability.effects.get(anim_state.current_frame, None):
                        emit_event(ABILITY_ACTIVATED, event=AbilityActivatedEvent(ent, index, anim_state.current_frame))
                elif esper.has_component(ent, AnimationEffects):
                    anim_effects = esper.component_for_entity(ent, AnimationEffects)
                    effects = anim_effects.effects.get(anim_state.type, {}).get(anim_state.current_frame, [])
                    for effect in effects:
                        effect.apply(ent, ent, ent)
                
                if new_frame == frame_count:
                    if index is not None:
                        emit_event(ABILITY_COMPLETED, event=AbilityCompletedEvent(ent, index))
                    elif anim_state.type == AnimationType.SPAWNING:
                        emit_event(SPAWNING_COMPLETED, event=SpawningCompletedEvent(ent))
                    # Stay on the last frame of the animation for one more tick.
                    anim_state.current_frame = frame_count - 1
                    # Reset the time so if the animation is supposed to loop it will start over.
                    anim_state.time_elapsed = 0
            sprite_sheet.update_frame(anim_state.type, anim_state.current_frame)
