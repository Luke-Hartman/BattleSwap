from typing import Tuple, List
import pygame

class Camera:
    def __init__(self, width: int, height: int):
        """
        Initialize the Camera object.

        Args:
            width: The width of the camera view.
            height: The height of the camera view.
        """
        self._rect = pygame.Rect(0, 0, width, height)
        self.speed = 10

    @property
    def x(self) -> int:
        """The x-coordinate of the camera's top-left corner."""
        return self._rect.x

    @x.setter
    def x(self, value: int) -> None:
        self._rect.x = value

    @property
    def y(self) -> int:
        """The y-coordinate of the camera's top-left corner."""
        return self._rect.y

    @y.setter
    def y(self, value: int) -> None:
        self._rect.y = value

    @property
    def width(self) -> int:
        """The width of the camera view."""
        return self._rect.width

    @width.setter
    def width(self, value: int) -> None:
        self._rect.width = value

    @property
    def height(self) -> int:
        """The height of the camera view."""
        return self._rect.height

    @height.setter
    def height(self, value: int) -> None:
        self._rect.height = value

    def process_event(self, event: pygame.event.Event) -> bool:
        """
        Process a single event and return whether it was consumed.

        Args:
            event: The pygame event to process.

        Returns:
            bool: True if the event was consumed, False otherwise.
        """
        if event.type in [pygame.KEYDOWN, pygame.KEYUP] and event.key in [
                pygame.K_LEFT, pygame.K_a,
                pygame.K_RIGHT, pygame.K_d,
                pygame.K_UP, pygame.K_w,
                pygame.K_DOWN, pygame.K_s
            ]:
            return True
        return False
    
    def update(self, time_delta: float) -> None:
        """Update the camera position based on the pressed keys."""
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.y += self.speed
        return False
