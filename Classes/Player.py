import pygame
from constants.matrix_sizes import *

class Player:
    def __init__(self):
        self.pos_X = 0
        self.pos_Y = 0
        self.speed = 10

    def move(self, pos):
        pygame.event.pump()
        keys = pygame.key.get_pressed()

        if keys[pygame.K_w]:
            if not self.find_collision(pos, pos, "W"):
                if self.pos_Y - self.speed >= 0:
                    self.pos_Y -= self.speed
        if keys[pygame.K_s]:
            if not self.find_collision(pos, pos, "S"):
                if self.pos_Y + self.speed <= SIZE_Y:
                    self.pos_Y += self.speed
        if keys[pygame.K_a]:
            if not self.find_collision(pos, pos, "A"):
                if self.pos_X - self.speed >= 0 :
                    self.pos_X -= self.speed
        if keys[pygame.K_d]:
            if not self.find_collision(pos, pos, "D"):
                if self.pos_X + self.speed <= SIZE_X:
                    self.pos_X += self.speed

    def get_position(self):
        return (self.pos_X, self.pos_Y)
    
    def find_collision(self, pos, char):
        if char == "W":
            for start_X, start_Y in border_tuples:
                if self.pos_Y - self.speed >= 0:

        if char == "S":
            
        if char == "A":

        if char == "D":

