"""
Animation processor module for Battle Swap.

This module contains the AnimationProcessor class, which is responsible for
updating the current frame of entities with AnimationState components.

Also triggers events based on frame changes.
"""

import esper
from components.ability import Abilities
from components.animation import AnimationState, AnimationType
from components.sprite_sheet import SpriteSheet
from components.unit_state import UnitState, State
from components.velocity import Velocity
from components.walk_effects import WalkEffects
from events import ABILITY_ACTIVATED, ABILITY_COMPLETED, AbilityActivatedEvent, AbilityCompletedEvent, emit_event

class AnimationProcessor(esper.Processor):
    """
    Processor responsible for updating animation frames.
    """

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

            new_anim_type = {
                State.IDLE: AnimationType.IDLE,
                State.PURSUING: AnimationType.WALKING,
                State.FLEEING: AnimationType.WALKING,
                State.ABILITY1: AnimationType.ABILITY1,
                State.ABILITY2: AnimationType.ABILITY2,
                State.ABILITY3: AnimationType.ABILITY3,
                State.ABILITY4: AnimationType.ABILITY4,
                State.ABILITY5: AnimationType.ABILITY5,
                State.DEAD: AnimationType.DYING
            }[unit_state.state]

            if unit_state.state == State.PURSUING:
                velocity = esper.component_for_entity(ent, Velocity)
                if velocity.x == 0 and velocity.y == 0:
                    new_anim_type = AnimationType.IDLE

            if anim_state.type != new_anim_type:
                anim_state.type = new_anim_type
                anim_state.current_frame = 0
                anim_state.time_elapsed = 0
            else:
                anim_state.time_elapsed += dt

            # Update the animation frame based on the current time
            total_duration = sprite_sheet.animation_durations[anim_state.type]
            frame_count = sprite_sheet.frames[anim_state.type]
            frame_duration = total_duration / frame_count

            new_frame = int(anim_state.time_elapsed // frame_duration)
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
                elif anim_state.type == AnimationType.WALKING and esper.has_component(ent, WalkEffects):
                    walk_effects = esper.component_for_entity(ent, WalkEffects)
                    effects = walk_effects.effects.get(anim_state.current_frame, None)
                    if effects:
                        for effect in effects:
                            effect.apply(ent, ent, ent)
                
                if new_frame == frame_count:
                    if index is not None:
                        emit_event(ABILITY_COMPLETED, event=AbilityCompletedEvent(ent, index))
                    # Stay on the last frame of the animation for one more tick.
                    anim_state.current_frame = frame_count - 1
                    # Reset the time so if the animation is supposed to loop it will start over.
                    anim_state.time_elapsed = 0
            sprite_sheet.update_frame(anim_state.type, anim_state.current_frame)
