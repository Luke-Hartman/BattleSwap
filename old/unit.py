from enum import Enum
import pygame
from abc import ABC, abstractmethod
import math
import os

from game import Game


class UnitState(Enum):
    """Names of the different states a unit can be in."""
    IDLE = "idle"
    WALKING = "walking"
    ATTACKING = "attacking"
    DYING = "dying"
    DEAD = "dead"


class AnimationType(Enum):
    """Names of the different animations that can be played."""

    IDLE = "idle"
    WALKING = "walking"
    ATTACKING = "attacking"
    DYING = "dying"
    HIDDEN = "hidden"


class Entity(ABC):
    def __init__(
            self,
            x: int,
            y: int,
            is_enemy: bool,
        ):
        """Constructor.

        Args:
            x: Initial x position.
            y: Initial y position.
            is_enemy: Whether the entity is an enemy.
        """
        self.x = x
        self.y = y
        self.is_enemy = is_enemy
        self._current_frame = 0
        """Which frame is currently being displayed."""
        self._current_animation = AnimationType.IDLE
        """The current animation being played."""
        self._animation_counter = 0
        """How many frames into the current animation we are."""

        if not hasattr(self.__class__, "animation_frames"):
            self.__class__.animation_frames = self.__class__.load_animation_frames()

    def update(self):
        """Update the entity's state."""
        self._animation_counter += 1
        if self._animation_counter == self.frame_durations()[self._current_animation]:
            self.frame_finished()
            self._current_frame = (self._current_frame + 1) % self.frame_counts()[self._current_animation]
            self._animation_counter = 0

    @property
    def current_frame(self) -> int:
        return self._current_frame

    @property
    def current_animation(self) -> AnimationType:
        """The current animation being played."""
        return self._current_animation
    
    @current_animation.setter
    def current_animation(self, animation_type: AnimationType):
        """Change the animation to play."""
        self._current_animation = animation_type
        self._current_frame = 0
        self._animation_counter = 0

    def frame_finished(self) -> None:
        """Handle actions when a frame finishes."""
        pass

    @abstractmethod
    def draw(self, screen: pygame.Surface, game: Game):
        """Draw the entity to the screen."""
        if self._current_animation == AnimationType.HIDDEN:
            return
        frame = self.animation_frames()[self._current_animation][self._current_frame]
        if self.is_enemy:
            frame = pygame.transform.flip(frame, True, False)
        rect = frame.get_rect(center=(self.x, self.y))
        screen.blit(frame, rect)
        if game.debug:
            pygame.draw.rect(screen, (255, 0, 0), rect, 2)
            pygame.draw.circle(screen, (0, 255, 0), (self.x, self.y), 3)

    @abstractmethod
    @classmethod
    def hitbox_width(cls) -> int:
        """Width of the hitbox."""
        pass

    @abstractmethod
    @classmethod
    def hitbox_height(cls) -> int:
        """Height of the hitbox."""
        pass

    @abstractmethod
    @classmethod
    def frame_durations(cls) -> dict[AnimationType, int]:
        """How many frames to display each sprite in an animation for."""
        pass

    @abstractmethod
    @classmethod
    def frame_rows(cls) -> dict[AnimationType, int]:
        """Which row of the sprite sheet contains the animations for each animation type."""
        pass

    @abstractmethod
    @classmethod
    def frame_counts(cls) -> dict[AnimationType, int]:
        """How many frames are in each animation."""
        pass

    @abstractmethod
    @classmethod
    def scale(cls) -> int:
        """How much to scale the sprite by."""
        pass

    @classmethod
    def load_animation_frames(cls) -> dict[AnimationType, list[pygame.Surface]]:
        """Load the animation frames for the entity."""
        frames = {}
        for anim in AnimationType:
            frames[anim] = []
        for anim, count in cls.frame_counts().items():
            row = cls.frame_rows()[anim]
            for col in range(count):
                frame = cls.sprite_sheet().subsurface((col * cls.frame_width(), row * cls.frame_height(), cls.frame_width(), cls.frame_height()))
                frame = pygame.transform.scale(frame, (cls.frame_width() * cls.scale(), cls.frame_height() * cls.scale()))
                frames[anim].append(frame)
        return frames


class Unit(Entity):
    def __init__(
        self,
        x: int,
        y: int,
        is_enemy: bool,
    ):
        """Constructor.

        Args:
            x: initial x position.
            y: initial y position.
            is_enemy: Which team the unit is on.
        """
        self.is_enemy = is_enemy
        self.health = self.max_health()
        self.target = None
        self._state = UnitState.IDLE
        super().__init__(x, y)

    @abstractmethod
    @classmethod
    def max_health(cls) -> int:
        """Maximum health of the unit."""
        pass

    @abstractmethod
    @classmethod
    def speed(cls) -> int:
        """Speed of the unit."""
        pass

    @abstractmethod
    @classmethod
    def payload_frame(cls) -> int:
        """The payload frame of the attack animation."""
        pass

    @abstractmethod
    @classmethod
    def attack_distance(cls) -> int:
        """How far away from the target the unit can attack from."""
        pass

    @abstractmethod
    def attack(self):
        """Triggered on the payload frame of the attack animation."""
        pass

    @abstractmethod
    def damage(cls) -> int:
        """The amount of damage the unit will deal to another unit when attacking."""
        pass

    @property
    def state(self) -> UnitState:
        return self._state
    
    def alive(self) -> bool:
        return self._state not in [UnitState.DEAD, UnitState.DYING]

    @state.setter
    def state(self, value: UnitState):
        if self._state == value:
            return
        if self._state == UnitState.DEAD:
            raise ValueError("Cannot change the state of a dead unit.")
        if value == UnitState.IDLE:
            self.current_animation = AnimationType.IDLE if not self.is_enemy else AnimationType.ENEMY_IDLE
        elif value == UnitState.WALK:
            self.current_animation = AnimationType.WALKING if not self.is_enemy else AnimationType.ENEMY_WALKING
        elif value == UnitState.ATTACK:
            self.current_animation = AnimationType.ATTACKING if not self.is_enemy else AnimationType.ENEMY_ATTACKING
        elif value == UnitState.DYING:
            self.current_animation = AnimationType.DYING if not self.is_enemy else AnimationType.ENEMY_DYING
        elif value == UnitState.DEAD:
            self.current_animation = AnimationType.HIDDEN
        self._state = value
    
    def frame_finished(self):
        if self._state == UnitState.DYING and self.current_frame == self.frame_counts()[AnimationType.DYING] - 1:
            self.state = UnitState.DEAD
        assert self.payload_frame != 0
        if self._state == UnitState.ATTACKING and self.current_frame == self.payload_frame - 1:
            self.attack()

    def take_damage(self, damage: int):
        """Update the unit's health and check if it is dead."""
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.state = UnitState.DIE

    def move_towards_location(self, x: int, y: int):
        """Move the unit towards its target if it has one."""
        dx = x - self.x
        dy = y - self.y
        angle = math.atan2(dy, dx)
        self.x += self.speed * math.cos(angle)
        self.y += self.speed * math.sin(angle)
    
    def target_in_range(self) -> bool:
        dx = self.target.x - self.x
        dy = self.target.y - self.y
        distance = math.sqrt(dx**2 + dy**2)
        return distance <= self.attack_distance

    def draw(self, screen: pygame.Surface, game: Game):
        if self.alive():
            self.draw_health_bar(screen)
        super().draw(screen, game)

    def draw_health_bar(self, screen: pygame.Surface):
        bar_width = self.hitbox_width
        bar_height = 3 * self.scale
        bar_offset = 5 * self.scale
        fill = (self.health / self.max_health) * bar_width
        
        # Position the health bar above the unit
        bar_x = self.x - bar_width // 2
        bar_y = self.y - self.hitbox_height // 2 - bar_offset
        
        outline_rect = pygame.Rect(bar_x, bar_y, bar_width, bar_height)
        fill_rect = pygame.Rect(bar_x, bar_y, fill, bar_height)
        
        color = (0, 255, 0) if not self.is_enemy else (255, 0, 0)
        pygame.draw.rect(screen, color, fill_rect)
        pygame.draw.rect(screen, (255, 255, 255), outline_rect, 2)

    def target_nearest_enemy(self, game: Game) -> "Unit":
        nearest_enemy = None
        min_distance = float('inf')
        for unit in game.units:
            if unit.is_enemy != self.is_enemy and unit.alive:
                distance = math.sqrt((self.x - unit.x)**2 + (self.y - unit.y)**2)
                if distance < min_distance:
                    min_distance = distance
                    nearest_enemy = unit
        self.target = nearest_enemy
        return nearest_enemy

class MiniFolkUnit(Unit):

    @classmethod
    def scale(cls) -> int:
        return 4
    
    @abstractmethod
    @classmethod
    def minifolks_large(cls) -> bool:
        pass

    @classmethod
    def hitbox_width(cls) -> int:
        return 16 if cls.minifolks_large() else 8
    
    @classmethod
    def hitbox_height(cls) -> int:
        return 12 if cls.minifolks_large() else 16


class MiniSwordMan(MiniFolkUnit):

    @classmethod
    def minifolks_large(cls) -> bool:
        return False
    
    @classmethod
    def frame_rows(cls) -> dict[AnimationType, int]:
        return {
            AnimationType.IDLE: 0,
            AnimationType.WALKING: 1,
            AnimationType.ATTACKING: 3,
            AnimationType.DYING: 5,
        }
    
    @classmethod
    def frame_counts(cls) -> dict[AnimationType, int]:
        return {
            AnimationType.IDLE: 4,
            AnimationType.WALKING: 6,
            AnimationType.ATTACKING: 6,
            AnimationType.DYING: 4,
        }
    
    @classmethod
    def frame_durations(cls) -> dict[AnimationType, int]:
        return {
            AnimationType.IDLE: 6,
            AnimationType.WALKING: 6,
            AnimationType.ATTACKING: 6,
            AnimationType.DYING: 6,
        }
    
    @classmethod
    def payload_frame(cls) -> int:
        return 2
    
    @classmethod
    def attack_distance(cls) -> int:
        return 15 * cls.scale()
    
    @classmethod
    def damage(cls) -> int:
        return 20
    
    def attack(self):
        self.target.take_damage(self.damage)

    def update(self, game: Game):
        if not self.alive():
            return
        if not self.target or not self.target.alive():
            self.target = self.target_nearest_enemy(game)
        if self.state == UnitState.IDLE:
            if target:
                self.state = UnitState.WALKING
        if self.state == UnitState.WALKING:
            self.move_towards_location(self.target.x, self.target.y)
        if self.target_in_range():
            self.state = UnitState.ATTACKING
        if self.state == UnitState.ATTACKING:
            pass # Attack handled in frame_finished

    

class Archer(Unit):

    @classmethod
    def minifolks_large(cls) -> bool:
        return False
    
    @classmethod
    def frame_rows(cls) -> dict[AnimationType, int]:
        return {
            AnimationType.IDLE: 0,
            AnimationType.WALKING: 1,
            AnimationType.ATTACKING: 3,
            AnimationType.DYING: 6,
        }
    
    @classmethod
    def frame_counts(cls) -> dict[AnimationType, int]:
        return {
            AnimationType.IDLE: 4,
            AnimationType.WALKING: 6,
            AnimationType.ATTACKING: 11,
            AnimationType.DYING: 4,
        }
    
    @classmethod
    def payload_frame(cls) -> int:
        return 7
    
    @classmethod
    def attack_distance(cls) -> int:
        return 300
    
    @classmethod
    def damage(cls) -> int:
        return 15

    def attack(self):
        Arrow(
            x=self.x,
            y=self.y,
            target=self.target,
            damage=self.damage,
            speed=3,
            is_enemy=self.is_enemy,
        )

    def update(self, game):
        if self.is_dead:
            self.animate('die')
            return

        if self.state == 'attack':
            self.animate('attack')
            if self.current_frame == self.payload_frame and self.animation_counter == 0:
                self.create_arrow()
            if self.current_frame == 0 and self.animation_counter == 0:
                self.state = 'idle'
        elif self.attack_cooldown > 0:
            self.attack_cooldown -= 1
            self.animate('idle')
        else:
            self.find_nearest_enemy(game)
            if self.target:
                distance = math.sqrt((self.x - self.target.x)**2 + (self.y - self.target.y)**2)
                if distance <= self.min_distance:
                    self.state = 'attack'
                    self.attack_cooldown = self.attack_cooldown_max
                else:
                    self.move_towards_target()
                    self.animate('walk')
            else:
                self.animate('idle')

        for arrow in self.arrows:
            arrow.update()
        self.arrows = [arrow for arrow in self.arrows if not arrow.reached_target]

    def create_arrow(self):
        if self.target and not self.target.is_dead:
            # Calculate the position for the arrow to start from
            arrow_start_x = self.x
            arrow_start_y = self.y
            new_arrow = Arrow(arrow_start_x, arrow_start_y, self.target, self.damage, self.is_enemy)
            self.arrows.append(new_arrow)

    def draw(self, screen):
        super().draw(screen)
        for arrow in self.arrows:
            arrow.draw(screen)

class Arrow:
    def __init__(self, x, y, target, damage, is_enemy):
        self.x = x
        self.y = y
        self.target = target
        self.damage = damage
        self.is_enemy = is_enemy
        self.speed = 3
        self.reached_target = False

        # Load arrow sprite
        arrow_path = os.path.join("assets", "MinifolksHumans", "HumansProjectiles.png")
        arrow_sheet = pygame.image.load(arrow_path).convert_alpha()
        self.image = arrow_sheet.subsurface((0, 0, 16, 16))  # Top-left sprite
        self.image = pygame.transform.scale(self.image, (16 * 2, 16 * 2))  # Scale up by 2
        if self.is_enemy:
            self.image = pygame.transform.flip(self.image, True, False)

        # Calculate initial angle
        dx = self.target.x - self.x
        dy = self.target.y - self.y
        self.angle = math.atan2(dy, dx)
        self.image = pygame.transform.rotate(self.image, -math.degrees(self.angle))

    def update(self):
        if self.target and not self.reached_target:
            dx = self.target.x - self.x
            dy = self.target.y - self.y
            distance = math.sqrt(dx**2 + dy**2)
            
            if distance > self.speed:
                self.x += self.speed * math.cos(self.angle)
                self.y += self.speed * math.sin(self.angle)
            else:
                self.x = self.target.x
                self.y = self.target.y
                self.reached_target = True
                if not self.target.is_dead:
                    self.target.take_damage(self.damage)

    def draw(self, screen):
        if not self.reached_target:
            rect = self.image.get_rect(center=(self.x, self.y))
            screen.blit(self.image, rect)