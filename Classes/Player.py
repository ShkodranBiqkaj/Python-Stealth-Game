import pygame
import math
from constants.matrix_sizes import SIZE_X, SIZE_Y, PIXEL_ONE_X, PIXEL_ONE_Y, matrix

class Player:
    def __init__(self):
        self.pos_X = 100
        self.pos_Y = 100
        self.speed = 4  # Increase player speed if desired

    def move(self):
        """
        Poll keyboard inputs and move the player if there's no collision.
        """
        pygame.event.pump()
        keys = pygame.key.get_pressed()

        new_x = self.pos_X
        new_y = self.pos_Y

        if keys[pygame.K_w]:
            if not self.check_collision((self.pos_X, self.pos_Y - self.speed)):
                new_y -= self.speed
        if keys[pygame.K_s]:
            if not self.check_collision((self.pos_X, self.pos_Y + self.speed)):
                new_y += self.speed
        if keys[pygame.K_a]:
            if not self.check_collision((self.pos_X - self.speed, self.pos_Y)):
                new_x -= self.speed
        if keys[pygame.K_d]:
            if not self.check_collision((self.pos_X + self.speed, self.pos_Y)):
                new_x += self.speed

        # Update matrix to reflect player's new position (mark old cell as 1, new as 2)
        old_col, old_row = self.pixel_to_grid((self.pos_X, self.pos_Y))
        new_col, new_row = self.pixel_to_grid((new_x, new_y))
        
        # Mark the old position as walkable again
        matrix[old_row][old_col] = 1
        # Mark the new position as "2" (player)
        matrix[new_row][new_col] = 2

        self.pos_X, self.pos_Y = new_x, new_y

    def check_collision(self, pixel_pos):
        """
        Convert the pixel position to grid coordinates and check if the tile is 0 (blocked).
        """
        col, row = self.pixel_to_grid(pixel_pos)
        # Check bounds
        if not (0 <= col < len(matrix[0]) and 0 <= row < len(matrix)):
            return True  # Out of bounds => collision

        return (matrix[row][col] == 0)

    def pixel_to_grid(self, pixel_pos):
        x, y = pixel_pos
        col = int(x // PIXEL_ONE_X)
        row = int(y // PIXEL_ONE_Y)
        return (col, row)

    def get_position(self):
        return (self.pos_X, self.pos_Y)
