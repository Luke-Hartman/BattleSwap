"""Animation processor for the Battle Swap game."""

import esper
from components.renderable import Renderable
from components.animation import Animation
from components.health import Health
from components.combat import Combat

class AnimationProcessor(esper.Processor):
    """Processor responsible for updating entity animations."""

    def __init__(self):
        self.battle_ended = False

    def process(self):
        """Update the animation state for all entities with Renderable and Animation components."""
        for ent, (rend, anim, health, combat) in esper.get_components(Renderable, Animation, Health, Combat):
            if health.current_health <= 0:
                self.handle_death_animation(anim, rend)
            elif self.battle_ended:
                self.handle_idle_animation(anim, rend)
            elif anim.row == 3 and anim.current_frame == anim.frame_count - 1:
                self.return_to_idle(anim)
            else:
                self.update_animation(anim, rend)

    def handle_death_animation(self, anim, rend):
        if anim.row != 5:
            anim.row = 5
            anim.current_frame = 0
            anim.frame_timer = 0
        elif anim.current_frame < anim.frame_count - 1:
            self.update_animation(anim, rend)

    def handle_idle_animation(self, anim, rend):
        if anim.row != 0:
            anim.row = 0
            anim.current_frame = 0
            anim.frame_timer = 0
        self.update_animation(anim, rend)

    def return_to_idle(self, anim):
        anim.row = 0
        anim.current_frame = 0
        anim.frame_timer = 0

    def update_animation(self, anim, rend):
        """Update the animation frame."""
        anim.frame_timer += 1
        if anim.frame_timer >= anim.frame_duration:
            anim.frame_timer = 0
            anim.current_frame = (anim.current_frame + 1) % anim.frame_count
            rend.current_frame = anim.current_frame

    def set_battle_ended(self, ended: bool):
        """Set the battle ended state."""
        self.battle_ended = ended
