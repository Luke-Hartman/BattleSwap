"""Collision processor module for Battle Swap.

This module contains the CollisionProcessor class, which is responsible for
detecting collisions between projectiles and units of opposing teams.
"""

from typing import Tuple
import esper
import pygame
from components.position import Position
from components.aoe import VisualAoE, CircleAoE
from components.projectile import Projectile
from components.sprite_sheet import SpriteSheet
from components.team import Team, TeamType
from components.unit_state import UnitState, State
from components.hitbox import Hitbox
from events import CIRCLE_AOE_HIT, VISUAL_AOE_HIT, CircleAoEHitEvent, ProjectileHitEvent, PROJECTILE_HIT, VisualAoEHitEvent, emit_event
from hex_grid import get_hex_bounds
from unit_condition import MaximumDistanceFromEntity

class CollisionProcessor(esper.Processor):
    """Processor responsible for detecting collisions between projectiles and units of opposing teams."""

    def __init__(self, hex_coords: Tuple[int, int]):
        self.battlefield_rect = pygame.Rect(*get_hex_bounds(*hex_coords))

    def process(self, dt: float):
        team1_projectiles = pygame.sprite.Group()
        team2_projectiles = pygame.sprite.Group()
        team1_units = pygame.sprite.Group()
        team2_units = pygame.sprite.Group()
        visual_aoe_sprites = pygame.sprite.Group()
        circle_aoe_ents = []
        sprite_to_ent = {}

        for ent, (sprite, team) in esper.get_components(SpriteSheet, Team):
            sprite_to_ent[sprite] = ent
            if esper.has_component(ent, Projectile):
                if team.type == TeamType.TEAM1:
                    team1_projectiles.add(sprite)
                else:
                    team2_projectiles.add(sprite)
            elif esper.has_component(ent, VisualAoE):
                visual_aoe_sprites.add(sprite)
            elif esper.has_component(ent, UnitState):
                unit_state = esper.component_for_entity(ent, UnitState)
                if unit_state.state != State.DEAD:
                    if team.type == TeamType.TEAM1:
                        team1_units.add(sprite)
                    else:
                        team2_units.add(sprite)
        
        for ent, (_) in esper.get_components(CircleAoE):
            circle_aoe_ents.append(ent)
        
        # For all sprites, update their collision masks
        for sprite in [*team1_projectiles, *team2_projectiles, *team1_units, *team2_units, *visual_aoe_sprites]:
            sprite.mask = pygame.mask.from_surface(sprite.image, threshold=10)

        # Handle collisions between team1 projectiles and team2 units
        self.process_unit_projectile_collisions(team1_projectiles, team2_units, sprite_to_ent)

        # Handle collisions between team2 projectiles and team1 units
        self.process_unit_projectile_collisions(team2_projectiles, team1_units, sprite_to_ent)

        # Handle collisions between Visual AOEs and units
        self.process_visual_aoe_unit_collisions(visual_aoe_sprites, team1_units, sprite_to_ent)
        self.process_visual_aoe_unit_collisions(visual_aoe_sprites, team2_units, sprite_to_ent)
        
        # Handle collisions between Circle AOEs and units
        self.process_circle_aoe_unit_collisions(circle_aoe_ents, team1_units, sprite_to_ent)
        self.process_circle_aoe_unit_collisions(circle_aoe_ents, team2_units, sprite_to_ent)

        # Remove off-battlefield projectiles
        for projectile in [*team1_projectiles, *team2_projectiles]:
            if not self.battlefield_rect.colliderect(projectile.rect):
                esper.delete_entity(sprite_to_ent[projectile])

        # Remove all circle aoes
        for aoe_ent in circle_aoe_ents:
            esper.delete_entity(aoe_ent)

    def check_sprite_group_collisions(self, group1: pygame.sprite.Group, group2: pygame.sprite.Group) -> list[tuple[pygame.sprite.Sprite, pygame.sprite.Sprite]]:
        """Check collisions between two sprite groups."""
        if not group1 or not group2:
            return []
        collisions = pygame.sprite.groupcollide(groupa=group1, groupb=group2, dokilla=False, dokillb=False, collided=pygame.sprite.collide_mask)
        collisions_list = []
        for sprite, collided_sprites in collisions.items():
            for collided_sprite in collided_sprites:
                collisions_list.append((sprite, collided_sprite))
        return collisions_list

    def check_hitbox_collision(self, attacker_sprite: pygame.sprite.Sprite, unit_sprite: pygame.sprite.Sprite, sprite_to_ent: dict) -> bool:
        """Check if any pixel of the attacker sprite overlaps with the unit's hitbox.

        Args:
            attacker_sprite: The sprite doing the attacking (projectile or AoE)
            unit_sprite: The unit's sprite
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
            
            # Check if the unit satisfies the projectile's unit condition
            projectile = esper.component_for_entity(p_ent, Projectile)
            if not projectile.unit_condition.check(u_ent):
                continue

            emit_event(PROJECTILE_HIT, event=ProjectileHitEvent(entity=p_ent, target=u_ent))
            collided_projectiles.add(p_sprite)
            esper.delete_entity(p_ent)

    def process_visual_aoe_unit_collisions(
        self,
        aoe_sprites: pygame.sprite.Group,
        u_sprites: pygame.sprite.Group,
        sprite_to_ent: dict
    ):
        """Handle collisions between visual AOEs and units."""
        collisions = self.check_sprite_group_collisions(aoe_sprites, u_sprites)

        for aoe_sprite, u_sprite in collisions:
            aoe_ent = sprite_to_ent[aoe_sprite]
            u_ent = sprite_to_ent[u_sprite]
            aoe = esper.component_for_entity(aoe_ent, VisualAoE)

            if u_ent in aoe.hit_entities:
                continue
            if not aoe.unit_condition.check(u_ent):
                continue
            if not self.check_hitbox_collision(aoe_sprite, u_sprite, sprite_to_ent):
                continue
            aoe.hit_entities.append(u_ent)
            emit_event(VISUAL_AOE_HIT, event=VisualAoEHitEvent(entity=aoe_ent, target=u_ent))

    def process_circle_aoe_unit_collisions(
        self,
        circle_aoe_ents: list[int],
        u_sprites: pygame.sprite.Group,
        sprite_to_ent: dict
    ):
        """Handle collisions between CircleAoEs and units."""
        # Process all CircleAoEs
        for aoe_ent in circle_aoe_ents:
            aoe = esper.component_for_entity(aoe_ent, CircleAoE)
            range_condition = MaximumDistanceFromEntity(aoe_ent, distance=aoe.radius, y_bias=None, use_hitbox=True)
            # Check all units
            for u_sprite in u_sprites:
                u_ent = sprite_to_ent[u_sprite]
                # Check unit condition
                if not aoe.unit_condition.check(u_ent):
                    continue
                if not range_condition.check(u_ent):
                    continue
                emit_event(CIRCLE_AOE_HIT, event=CircleAoEHitEvent(entity=aoe_ent, target=u_ent))