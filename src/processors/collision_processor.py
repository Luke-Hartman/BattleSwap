"""Collision processor module for Battle Swap.

This module contains the CollisionProcessor class, which is responsible for
detecting collisions between projectiles and units of opposing teams.
"""

import esper
import pygame
import numpy as np
from scipy.spatial import KDTree
from components.position import Position
from game_constants import gc
from components.aoe import AoE
from components.projectile import Projectile
from components.sprite_sheet import SpriteSheet
from components.team import Team, TeamType
from components.unit_state import UnitState, State
from components.hitbox import Hitbox
from events import AOE_HIT, AoEHitEvent, ProjectileHitEvent, PROJECTILE_HIT, emit_event

class CollisionProcessor(esper.Processor):
    """Processor responsible for detecting collisions between projectiles and units of opposing teams."""

    def __init__(self):
        self.battlefield_rect = pygame.Rect(0, 0, gc.BATTLEFIELD_WIDTH, gc.BATTLEFIELD_HEIGHT)

    def process(self, dt: float):
        team1_projectiles = pygame.sprite.Group()
        team2_projectiles = pygame.sprite.Group()
        team1_units = pygame.sprite.Group()
        team2_units = pygame.sprite.Group()
        aoe_sprites = pygame.sprite.Group()
        sprite_to_ent = {}

        # Separate entities by team and type (projectiles, AoEs, or units)
        for ent, (sprite, team) in esper.get_components(SpriteSheet, Team):
            sprite_to_ent[sprite] = ent
            if esper.has_component(ent, Projectile):
                if team.type == TeamType.TEAM1:
                    team1_projectiles.add(sprite)
                else:
                    team2_projectiles.add(sprite)
            elif esper.has_component(ent, AoE):
                aoe_sprites.add(sprite)
            elif esper.has_component(ent, UnitState):
                unit_state = esper.component_for_entity(ent, UnitState)
                if unit_state.state != State.DEAD:
                    if team.type == TeamType.TEAM1:
                        team1_units.add(sprite)
                    else:
                        team2_units.add(sprite)
        
        # For all sprites, update their collision masks
        for sprite in [*team1_projectiles, *team2_projectiles, *team1_units, *team2_units, *aoe_sprites]:
            sprite.mask = pygame.mask.from_surface(sprite.image)

        # Handle collisions between team1 projectiles and team2 units
        self.process_unit_projectile_collisions(team1_projectiles, team2_units, sprite_to_ent)

        # Handle collisions between team2 projectiles and team1 units
        self.process_unit_projectile_collisions(team2_projectiles, team1_units, sprite_to_ent)

        # Handle collisions between AoEs and units
        self.process_aoe_unit_collisions(aoe_sprites, team1_units, sprite_to_ent)
        self.process_aoe_unit_collisions(aoe_sprites, team2_units, sprite_to_ent)

        # Remove off-battlefield projectiles
        for projectile in [*team1_projectiles, *team2_projectiles]:
            if not self.battlefield_rect.colliderect(projectile.rect):
                esper.delete_entity(sprite_to_ent[projectile])

    def check_sprite_group_collisions(self, group1: pygame.sprite.Group, group2: pygame.sprite.Group) -> list[tuple[pygame.sprite.Sprite, pygame.sprite.Sprite]]:
        """Check collisions between two sprite groups using KDTree."""
        if not group1 or not group2:
            return []

        # Create KDTree for group1
        g1_positions = np.array([(s.rect.centerx, s.rect.centery) for s in group1])
        g1_tree = KDTree(g1_positions)

        # Create list of group2 positions and max dimensions
        g2_positions = np.array([(s.rect.centerx, s.rect.centery) for s in group2])
        g2_max_dims = np.array([((s.rect.width/2)**2 + (s.rect.height/2)**2)**0.5 for s in group2])

        # Query KDTree for potential collisions
        potential_collisions = g1_tree.query_ball_point(g2_positions, g2_max_dims)

        collisions = []
        for s2, s1_indices in zip(group2, potential_collisions):
            for s1_index in s1_indices:
                s1 = list(group1)[s1_index]
                if pygame.sprite.collide_mask(s1, s2):
                    collisions.append((s1, s2))

        return collisions

    def check_hitbox_collision(self, attacker_sprite: pygame.sprite.Sprite, unit_sprite: pygame.sprite.Sprite, sprite_to_ent: dict) -> bool:
        """Check if any pixel of the attacker sprite overlaps with the unit's hitbox.
        
        Args:
            attacker_sprite: The sprite doing the attacking (projectile or AoE)
            unit_sprite: The unit's sprite
            hitbox: The unit's hitbox component
            sprite_to_ent: Dictionary mapping sprites to their entities
        """
        # Get the unit's sprite sheet component to access the center offset
        unit_ent = sprite_to_ent[unit_sprite]
        hitbox = esper.component_for_entity(unit_ent, Hitbox)
        unit_position = esper.component_for_entity(unit_ent, Position)

        # Create hitbox rect centered on unit's actual center (accounting for offset)
        hitbox_rect = pygame.Rect(
            unit_position.x - hitbox.width / 2,
            unit_position.y - hitbox.height / 2,
            hitbox.width,
            hitbox.height
        )

        # Get all non-transparent pixels in the attacker's sprite
        mask = attacker_sprite.mask
        sprite_rect = attacker_sprite.rect
        
        # For each non-transparent pixel in the sprite, check if it's in the hitbox
        offset_x = sprite_rect.x - hitbox_rect.x
        offset_y = sprite_rect.y - hitbox_rect.y
        for x in range(sprite_rect.width):
            if not 0 <= offset_x + x <= hitbox_rect.width:
                continue
            for y in range(sprite_rect.height):
                if not 0 <= offset_y + y <= hitbox_rect.height:
                    continue
                if mask.get_at((x, y)):
                    return True
        
        return False

    def process_unit_projectile_collisions(
        self,
        p_sprites: pygame.sprite.Group,
        u_sprites: pygame.sprite.Group,
        sprite_to_ent: dict,
    ):
        """Handle collisions between projectiles and units of opposing teams."""
        collisions = self.check_sprite_group_collisions(p_sprites, u_sprites)

        # This is to skip checking collisions for a projectile that has already hit a unit
        collided_projectiles = set()
        for p_sprite, u_sprite in collisions:
            if p_sprite in collided_projectiles:
                continue
            
            if not self.check_hitbox_collision(p_sprite, u_sprite, sprite_to_ent):
                continue

            p_ent = sprite_to_ent[p_sprite]
            u_ent = sprite_to_ent[u_sprite]
            emit_event(PROJECTILE_HIT, event=ProjectileHitEvent(entity=p_ent, target=u_ent))
            collided_projectiles.add(p_sprite)
            esper.delete_entity(p_ent)

    def process_aoe_unit_collisions(
        self,
        aoe_sprites: pygame.sprite.Group,
        u_sprites: pygame.sprite.Group,
        sprite_to_ent: dict
    ):
        """Handle collisions between AoEs and units."""
        collisions = self.check_sprite_group_collisions(aoe_sprites, u_sprites)
        for aoe_sprite, u_sprite in collisions:

            if not self.check_hitbox_collision(aoe_sprite, u_sprite, sprite_to_ent):
                continue

            aoe_ent = sprite_to_ent[aoe_sprite]
            u_ent = sprite_to_ent[u_sprite]
            emit_event(AOE_HIT, event=AoEHitEvent(entity=aoe_ent, target=u_ent))