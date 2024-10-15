"""Collision processor module for Battle Swap.

This module contains the CollisionProcessor class, which is responsible for
detecting collisions between projectiles and units and removing off-screen projectiles.
"""

import esper
import pygame
from components.position import Position
from components.sprite_sheet import SpriteSheet
from components.team import Team, TeamType
from components.unit_state import UnitState, State
from components.projectile_damage import ProjectileDamage
from events import ProjectileHitEvent, PROJECTILE_HIT, emit_event

class CollisionProcessor(esper.Processor):
    """Processor responsible for detecting collisions between projectiles and units."""

    def __init__(self, screen):
        self.screen = screen
        self.screen_rect = screen.get_rect()

    def process(self, dt: float):
        projectiles = [(ent, pos, sprite, team, damage) 
                       for ent, (pos, sprite, team, damage) in esper.get_components(Position, SpriteSheet, Team, ProjectileDamage)]

        units = [(ent, pos, sprite, team) 
                 for ent, (pos, sprite, team, state) in esper.get_components(Position, SpriteSheet, Team, UnitState)
                 if state.state != State.DEAD]

        for p_ent, p_pos, p_sprite, p_team, p_damage in projectiles:
            p_sprite.rect.center = (p_pos.x, p_pos.y)
            
            # Check if projectile is off-screen
            if not self.screen_rect.colliderect(p_sprite.rect):
                esper.delete_entity(p_ent)
                continue

            for u_ent, u_pos, u_sprite, u_team in units:
                if p_team.type != u_team.type:
                    u_sprite.rect.center = (u_pos.x, u_pos.y)

                    if pygame.sprite.collide_mask(p_sprite, u_sprite):
                        emit_event(PROJECTILE_HIT, event=ProjectileHitEvent(u_ent, p_damage.damage))
                        esper.delete_entity(p_ent)
                        break  # Only one unit can be hit by each projectile
