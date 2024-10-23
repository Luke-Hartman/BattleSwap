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

    def handle_event(self, events: List[pygame.event.Event]) -> None:
        """
        Handle camera movement based on input events.

        Args:
            events: List of pygame events to process.
        """
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.y += self.speed
