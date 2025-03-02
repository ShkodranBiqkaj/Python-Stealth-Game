import pygame
from abc import ABC, abstractmethod

class Entity(ABC): 
    def __init__(self):
        self.pos_X = 50
        self.pos_Y = 50
        self.speed = 2.5

    @abstractmethod
    def move(self, pos):
        """Subclasses must implement this method."""
        pass

    @abstractmethod
    def find_collision(self, pos, char):
        """Subclasses must implement this method."""
        pass
