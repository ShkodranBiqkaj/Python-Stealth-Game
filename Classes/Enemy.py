import math
import time
from collections import deque
import pygame

from constants.matrix_sizes import PIXEL_ONE_X, PIXEL_ONE_Y, matrix, GRID_ROWS, GRID_COLS

class Enemy:
    def __init__(self, position, move_speed=3, update_interval=1):
        """
        :param position: (x, y) pixel coordinates for the enemy's start
        :param move_speed: pixels the enemy moves each update
        :param update_interval: seconds between path recalculations
        """
        self.images = {
            'down': [
                pygame.transform.scale(
                    pygame.image.load("../assets/boy_down_1.png").convert_alpha(), (40, 40)
                ),
                pygame.transform.scale(
                    pygame.image.load("../assets/boy_down_2.png").convert_alpha(), (40, 40)
                )
            ],
            'up': [
                pygame.transform.scale(
                    pygame.image.load("../assets/enemy_up_1.png").convert_alpha(), (40, 40)
                ),
                pygame.transform.scale(
                    pygame.image.load("../assets/enemy_up_2.png").convert_alpha(), (40, 40)
                )
            ],
            'left': [
                pygame.transform.scale(
                    pygame.image.load("../assets/enemy_left_1.png").convert_alpha(), (40, 40)
                ),
                pygame.transform.scale(
                    pygame.image.load("../assets/enemy_left_2.png").convert_alpha(), (40, 40)
                )
            ],
            'right': [
                pygame.transform.scale(
                    pygame.image.load("../assets/enemy_right_1.png").convert_alpha(), (40, 40)
                ),
                pygame.transform.scale(
                    pygame.image.load("../assets/enemy_right_2.png").convert_alpha(), (40, 40)
                )
            ]
        }

        self.direction = 'down'
        self.position = position
        self.move_speed = move_speed
        self.update_interval = update_interval

        # Timing for path recalculation
        self.last_update_time = time.time()

        # Path of grid cells (col, row) to follow
        self.path = []

        # Animation counters
        self.frames_per_step = 10  # how many updates before toggling footstep frame
        self.frame_timer = 0
        self.current_frame = 0
        self.current_image = self.images[self.direction][self.current_frame]

    def move(self, player_pos):
        """
        Updates the enemy's position by following a BFS path toward the player.
        Recalculates the path every self.update_interval seconds.
        """
        current_time = time.time()
        if current_time - self.last_update_time >= self.update_interval:
            self.find_path(player_pos)
            self.last_update_time = current_time

        if not self.path:
            # No path available or not found
            return

        # Get next grid cell from path
        next_cell = self.path[0]
        target_pixel = self.grid_to_pixel(next_cell)

        # Calculate direction vector (dx, dy)
        dx = target_pixel[0] - self.position[0]
        dy = target_pixel[1] - self.position[1]
        dist = math.sqrt(dx*dx + dy*dy)

        if dist > 0:
            dx /= dist
            dy /= dist

        # Decide facing direction based on dx, dy
        # Whichever axis has the larger magnitude decides the direction
        if abs(dx) > abs(dy):
            if dx > 0:
                self.direction = 'right'
            else:
                self.direction = 'left'
        else:
            if dy > 0:
                self.direction = 'down'
            else:
                self.direction = 'up'

        # Attempt movement
        new_x = self.position[0] + dx * self.move_speed
        new_y = self.position[1] + dy * self.move_speed

        # Check collision with the matrix
        if not self.check_collision((new_x, new_y)):
            self.position = (new_x, new_y)

            # Update the animation frame (toggle foot)
            self.frame_timer += 1
            if self.frame_timer >= self.frames_per_step:
                self.frame_timer = 0
                self.current_frame = (self.current_frame + 1) % 2

            # Update the current image based on direction & current frame
            self.current_image = self.images[self.direction][self.current_frame]

            # If we're close enough to the target cell, pop it from the path
            new_dist = math.sqrt((target_pixel[0] - new_x)**2 + (target_pixel[1] - new_y)**2)
            if new_dist < self.move_speed:
                self.path.pop(0)
        else:
            # Collision encountered; remove the problematic cell and try again
            self.path.pop(0)
            self.find_path(player_pos)

    def find_path(self, player_pos):
        """Use BFS to find a path from the enemy's grid cell to the player's grid cell."""
        start = self.pixel_to_grid(self.position)
        goal = self.pixel_to_grid(player_pos)

        if not self.is_walkable(start) or not self.is_walkable(goal):
            self.path = []
            return

        queue = deque([start])
        came_from = {start: None}
        visited = {start}

        found = False
        while queue and not found:
            current = queue.popleft()
            if current == goal:
                found = True
                break

            for neighbor in self.get_neighbors(current):
                if neighbor not in visited and self.is_walkable(neighbor):
                    visited.add(neighbor)
                    came_from[neighbor] = current
                    queue.append(neighbor)

        if found:
            # Reconstruct path
            path = []
            node = goal
            while node != start:
                path.append(node)
                node = came_from[node]
            path.reverse()
            self.path = path
        else:
            self.path = []

    def get_neighbors(self, cell):
        """Return valid up/down/left/right neighbors for BFS."""
        col, row = cell
        neighbors = [
            (col, row - 1),
            (col, row + 1),
            (col - 1, row),
            (col + 1, row)
        ]
        # Filter out-of-bounds
        valid = [(c, r) for (c, r) in neighbors if 0 <= c < GRID_COLS and 0 <= r < GRID_ROWS]
        return valid

    def check_collision(self, pixel_pos):
        """
        Convert the pixel position to a grid cell and check if it's walkable (1) or not (0).
        If it's 0 (obstacle), we have a collision.
        """
        grid_cell = self.pixel_to_grid(pixel_pos)
        if not self.in_bounds(grid_cell):
            return True  # out of bounds => collision
        col, row = grid_cell
        return (matrix[row][col] == 0)

    def is_walkable(self, cell):
        """Check if the cell in the matrix is walkable."""
        col, row = cell
        if not self.in_bounds(cell):
            return False
        # Adjust if you have special tiles (e.g., 2) that are also walkable
        return (matrix[row][col] == 1 or matrix[row][col] == 2)

    def pixel_to_grid(self, pixel_pos):
        """Convert pixel coordinates to (col, row) in the grid."""
        x, y = pixel_pos
        col = int(x // PIXEL_ONE_X)
        row = int(y // PIXEL_ONE_Y)
        return (col, row)

    def grid_to_pixel(self, cell):
        """Convert (col, row) to pixel coordinates (x, y)."""
        col, row = cell
        px = col * PIXEL_ONE_X + PIXEL_ONE_X / 2
        py = row * PIXEL_ONE_Y + PIXEL_ONE_Y / 2
        return (px, py)

    def in_bounds(self, cell):
        """Check if a cell (col, row) is within the grid."""
        c, r = cell
        return (0 <= c < GRID_COLS and 0 <= r < GRID_ROWS)

    def get_position(self):
        """Return the current pixel (x, y) of the enemy."""
        return self.position

    def draw(self, screen):
        """
        Draw the enemy sprite at its current position.
        The sprite is 40x40, so you might want to offset it
        to center the position if needed.
        """
        x_offset = 20
        y_offset = 20
        screen.blit(self.current_image, (self.position[0] - x_offset, self.position[1] - y_offset))
