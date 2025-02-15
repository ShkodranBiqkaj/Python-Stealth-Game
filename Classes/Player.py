import pygame
from constants.matrix_sizes import *

class Player:
    def __init__(self):
        self.pos_X = 25
        self.pos_Y = 25
        self.speed = 10

    def move(self, pos):
        pygame.event.pump()
        keys = pygame.key.get_pressed()

        new_x = self.pos_X
        new_y = self.pos_Y

        if keys[pygame.K_w] and not self.find_collision((self.pos_X, self.pos_Y - self.speed), "W"):
            if self.pos_Y - self.speed >= 0:  # Boundary check
                new_y -= self.speed
        if keys[pygame.K_s] and not self.find_collision((self.pos_X, self.pos_Y + self.speed), "S"):
            if self.pos_Y + self.speed <= SIZE_Y:  # Boundary check
                new_y += self.speed
        if keys[pygame.K_a] and not self.find_collision((self.pos_X - self.speed, self.pos_Y), "A"):
            if self.pos_X - self.speed >= 0:  # Boundary check
                new_x -= self.speed
        if keys[pygame.K_d] and not self.find_collision((self.pos_X + self.speed, self.pos_Y), "D"):
            if self.pos_X + self.speed <= SIZE_X:  # Boundary check
                new_x += self.speed

        self.pos_X = new_x
        self.pos_Y = new_y

    def get_position(self):
        return (self.pos_X, self.pos_Y)
    
    def find_collision(self, pos, char):
        player_size = 0  # Assuming player is 10x10 pixels

        for (x_start, x_end), (y_start, y_end) in border_tuples:
            # Check movement in all directions
            if char == "W" and (pos[1] - self.speed < y_end and pos[1] - self.speed + player_size > y_start) and (pos[0] + player_size > x_start and pos[0] < x_end):
                return True
            if char == "S" and (pos[1] + self.speed + player_size > y_start and pos[1] + self.speed < y_end) and (pos[0] + player_size > x_start and pos[0] < x_end):
                return True
            if char == "A" and (pos[0] - self.speed < x_end and pos[0] - self.speed + player_size > x_start) and (pos[1] + player_size > y_start and pos[1] < y_end):
                return True
            if char == "D" and (pos[0] + self.speed + player_size > x_start and pos[0] + self.speed < x_end) and (pos[1] + player_size > y_start and pos[1] < y_end):
                return True

        return False
