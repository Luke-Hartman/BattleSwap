"""
Animation processor module for Battle Swap.

This module contains the AnimationProcessor class, which is responsible for
updating the current frame of entities with AnimationState components.
"""

import esper
from components.animation import AnimationState
from components.sprite_sheet import SpriteSheet

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
        for ent, (anim_state, sprite_sheet) in esper.get_components(AnimationState, SpriteSheet):
            anim_state.current_time += dt
            total_duration = sprite_sheet.animation_durations[anim_state.type]
            frame_count = sprite_sheet.frames[anim_state.type]
            frame_duration = total_duration / frame_count

            if anim_state.current_time >= frame_duration:
                anim_state.current_time -= frame_duration
                anim_state.current_frame = (anim_state.current_frame + 1) % frame_count
