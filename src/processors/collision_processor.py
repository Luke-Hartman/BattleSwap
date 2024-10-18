"""Collision processor module for Battle Swap.

This module contains the CollisionProcessor class, which is responsible for
detecting collisions between projectiles and units of opposing teams.
"""

import esper
import pygame
import numpy as np
from scipy.spatial import KDTree
from CONSTANTS import SCREEN_HEIGHT, SCREEN_WIDTH
from components.sprite_sheet import SpriteSheet
from components.team import Team, TeamType
from components.unit_state import UnitState, State
from components.projectile_damage import ProjectileDamage
from events import ProjectileHitEvent, PROJECTILE_HIT, emit_event

class CollisionProcessor(esper.Processor):
    """Processor responsible for detecting collisions between projectiles and units of opposing teams."""

    def __init__(self, screen):
        self.screen = screen
        self.screen_rect = screen.get_rect()

    def process(self, dt: float):
        team1_projectiles = pygame.sprite.Group()
        team2_projectiles = pygame.sprite.Group()
        team1_units = pygame.sprite.Group()
        team2_units = pygame.sprite.Group()
        sprite_to_ent = {}

        # Separate entities by team and type (projectile or unit)
        for ent, (sprite, team) in esper.get_components(SpriteSheet, Team):
            sprite_to_ent[sprite] = ent
            if esper.has_component(ent, ProjectileDamage):
                if team.type == TeamType.TEAM1:
                    team1_projectiles.add(sprite)
                else:
                    team2_projectiles.add(sprite)
            elif esper.has_component(ent, UnitState):
                unit_state = esper.component_for_entity(ent, UnitState)
                if unit_state.state != State.DEAD:
                    if team.type == TeamType.TEAM1:
                        team1_units.add(sprite)
                    else:
                        team2_units.add(sprite)
        
        # For all sprites, update their collision masks
        for sprite in [*team1_projectiles, *team2_projectiles, *team1_units, *team2_units]:
            sprite.mask = pygame.mask.from_surface(sprite.image)

        # Handle collisions between team1 projectiles and team2 units
        self.process_unit_projectile_collisions(team1_projectiles, team2_units, sprite_to_ent)

        # Handle collisions between team2 projectiles and team1 units
        self.process_unit_projectile_collisions(team2_projectiles, team1_units, sprite_to_ent)

        # Remove off-screen projectiles
        for projectile in [*team1_projectiles, *team2_projectiles]:
            if not self.screen_rect.colliderect(projectile.rect):
                esper.delete_entity(sprite_to_ent[projectile])

    def process_unit_projectile_collisions(self, p_sprites: pygame.sprite.Group, u_sprites: pygame.sprite.Group, sprite_to_ent: dict):
        """Handle collisions between projectiles and units of opposing teams."""
        if not p_sprites or not u_sprites:
            return

        # Create KDTree for projectiles
        p_positions = np.array([(p.rect.centerx, p.rect.centery) for p in p_sprites])
        p_tree = KDTree(p_positions)

        # Create list of unit positions and max dimensions
        u_positions = np.array([(u.rect.centerx, u.rect.centery) for u in u_sprites])
        u_max_dims = np.array([((u.rect.width/2)**2 + (u.rect.height/2)**2)**0.5 for u in u_sprites])

        # Query KDTree for potential collisions
        potential_collisions = p_tree.query_ball_point(u_positions, u_max_dims)

        collisions = []
        for (u_sprite, p_indices) in zip(u_sprites, potential_collisions):
            for p_index in p_indices:
                p_sprite = list(p_sprites)[p_index]
                if pygame.sprite.collide_mask(p_sprite, u_sprite):
                    collisions.append((p_sprite, u_sprite))

        # Handle found collisions
        collided_projectiles = set()
        for p_sprite, u_sprite in collisions:
            if p_sprite in collided_projectiles:
                continue
            p_ent = sprite_to_ent[p_sprite]
            p_damage = esper.component_for_entity(p_ent, ProjectileDamage)

            u_ent = sprite_to_ent[u_sprite]
            emit_event(PROJECTILE_HIT, event=ProjectileHitEvent(u_ent, p_damage.damage))
            collided_projectiles.add(p_sprite)
            esper.delete_entity(p_ent)
