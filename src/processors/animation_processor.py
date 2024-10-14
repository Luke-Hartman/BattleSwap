"""
Animation processor module for Battle Swap.

This module contains the AnimationProcessor class, which is responsible for
updating the current frame of entities with AnimationState components.
"""

import esper
from components.animation import AnimationState, AnimationType
from components.sprite_sheet import SpriteSheet
from components.unit_state import UnitState, State
from events import AttackCompletedEvent, AttackActivatedEvent, ATTACK_COMPLETED, ATTACK_ACTIVATED, emit_event

class AnimationProcessor(esper.Processor):
    """
    Processor responsible for updating animation frames of entities.
    """

    def process(self, dt: float):
        """
        Process all entities with AnimationState components and update their current frame.

        Args:
            dt (float): Delta time since last frame, in seconds.
        """
        for ent, (anim_state, sprite_sheet, unit_state) in esper.get_components(AnimationState, SpriteSheet, UnitState):
            # Update the animation type based on the unit state
            new_anim_type = {
                State.IDLE: AnimationType.IDLE,
                State.PURSUING: AnimationType.WALKING,
                State.ATTACKING: AnimationType.ATTACKING,
                State.DEAD: AnimationType.DYING
            }.get(unit_state.state, AnimationType.IDLE)

            if anim_state.type != new_anim_type:
                anim_state.type = new_anim_type
                anim_state.current_frame = 0
                anim_state.current_time = 0

            # Update the animation frame based on the current time
            anim_state.current_time += dt
            total_duration = sprite_sheet.animation_durations[anim_state.type]
            frame_count = sprite_sheet.frames[anim_state.type]
            frame_duration = total_duration / frame_count

            if anim_state.current_time >= frame_duration:
                anim_state.current_time -= frame_duration
                if anim_state.type == AnimationType.DYING and anim_state.current_frame == frame_count - 1:
                    # Stop the animation at the last frame for death animation
                    anim_state.current_frame = frame_count - 1
                else:
                    anim_state.current_frame = (anim_state.current_frame + 1) % frame_count

                # Check if attack is activated
                if unit_state.state == State.ATTACKING and anim_state.type == AnimationType.ATTACKING:
                    if anim_state.current_frame == sprite_sheet.attack_activation_frame:
                        emit_event(ATTACK_ACTIVATED, event=AttackActivatedEvent(ent))
                    elif anim_state.current_frame == frame_count - 1:
                        emit_event(ATTACK_COMPLETED, event=AttackCompletedEvent(ent))
