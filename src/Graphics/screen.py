# screen.py
import pygame
from abc import ABC, abstractmethod
SIZE_X, SIZE_Y = 1000, 750

class Screen(ABC):
    """
    Base class for any game‐state screen (menus, game, etc.).
    """

    def __init__(self, surface: pygame.Surface, clock: pygame.time.Clock):
        self.surface = surface
        self.clock   = clock

    def on_enter(self):
        """Called once when this screen is pushed."""
        pass

    def on_exit(self):
        """Called once when this screen is popped."""
        pass

    @abstractmethod
    def handle_event(self, event: pygame.event.EventType):
        """React to a single Pygame event."""
        ...

    @abstractmethod
    def update(self, dt: float):
        """Update logic (called every frame)."""
        ...

    @abstractmethod
    def render(self):
        """Draw everything to self.surface."""
        ...
