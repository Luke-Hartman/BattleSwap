from abc import ABC, abstractmethod

import pygame

class Scene(ABC):
    """Abstract base class for all scenes."""

    @abstractmethod
    def update(self, screen: pygame.Surface, time_delta: float, events: list[pygame.event.Event]) -> bool:
        """Update the scene, including rendering and processing events.
        Args:
            screen: The pygame surface to draw on.
            time_delta: The time delta since the last update.
            events: The events from pygame.event.get().

        Returns:
            True if the game should continue, False if it should quit.
        """
