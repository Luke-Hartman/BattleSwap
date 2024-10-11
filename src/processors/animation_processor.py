"""Animation processor for the Battle Swap game."""

import esper
from components.renderable import Renderable
from components.animation import Animation

class AnimationProcessor(esper.Processor):
    """Processor responsible for updating entity animations."""

    def process(self):
        """Update the animation state for all entities with Renderable and Animation components."""
        for ent, (rend, anim) in esper.get_components(Renderable, Animation):
            anim.frame_timer += 1
            if anim.frame_timer >= anim.frame_duration:
                anim.frame_timer = 0
                anim.current_frame = (anim.current_frame + 1) % anim.frame_count
                rend.current_frame = anim.current_frame