"""Collision processor module for Battle Swap.

This module contains the CollisionProcessor class, which is responsible for
detecting collisions between projectiles and units and removing off-screen projectiles.
"""

import esper
import pygame
import math
from components.position import Position
from components.sprite_sheet import SpriteSheet
from components.team import Team
from components.unit_state import UnitState, State
from components.projectile_damage import ProjectileDamage
from components.velocity import Velocity
from components.orientation import Orientation, FacingDirection
from events import ProjectileHitEvent, PROJECTILE_HIT, emit_event


def get_hitbox(sprite_sheet: SpriteSheet, pos: Position) -> pygame.Rect:
    """Returns the scaled hitbox as a pygame.Rect, centered on the sprite."""
    hitbox = pygame.Rect(
        sprite_sheet.sprite_offset[0] * sprite_sheet.scale,
        sprite_sheet.sprite_offset[1] * sprite_sheet.scale,
        sprite_sheet.sprite_size[0] * sprite_sheet.scale,
        sprite_sheet.sprite_size[1] * sprite_sheet.scale
    )
    hitbox.center = (pos.x, pos.y)
    return hitbox

class CollisionProcessor(esper.Processor):
    """Processor responsible for detecting collisions between projectiles and units."""

    def __init__(self, screen):
        self.screen = screen
        self.screen_rect = screen.get_rect()

    def process(self, dt: float):
        projectiles = [(ent, pos, sprite, team, velocity, damage) 
                       for ent, (pos, sprite, team, velocity, damage) in esper.get_components(Position, SpriteSheet, Team, Velocity, ProjectileDamage)]

        units = [(ent, pos, sprite, team, state) 
                 for ent, (pos, sprite, team, state) in esper.get_components(Position, SpriteSheet, Team, UnitState)
                 if state.state != State.DEAD]

        for p_ent, p_pos, p_sprite, p_team, p_velocity, p_damage in projectiles:
            p_hitbox = get_hitbox(p_sprite, p_pos)
            
            # Check if projectile is off-screen
            if not self.screen_rect.colliderect(p_hitbox):
                esper.delete_entity(p_ent)
                continue

            for u_ent, u_pos, u_sprite, u_team, u_state in units:
                if p_team.type != u_team.type and u_state.state != State.DEAD:
                    u_hitbox = get_hitbox(u_sprite, u_pos)

                    if p_hitbox.colliderect(u_hitbox):
                        emit_event(PROJECTILE_HIT, event=ProjectileHitEvent(u_ent, p_damage.damage))
                        esper.delete_entity(p_ent)
                        break  # Only one unit can be hit by each projectile
