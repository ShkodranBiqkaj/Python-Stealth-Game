import math
import time
from collections import deque
from constants.matrix_sizes import PIXEL_ONE_X, PIXEL_ONE_Y, matrix, GRID_ROWS, GRID_COLS

class Enemy:
    def __init__(self, position, move_speed=3, update_interval=1):
        """
        :param position: (x, y) pixel coordinates for the enemy's start
        :param move_speed: pixels the enemy moves each update
        :param update_interval: seconds between path recalculations
        """
        self.position = position
        self.move_speed = move_speed
        self.update_interval = update_interval

        self.last_update_time = time.time()
        self.path = []  # List of grid cells (col, row) to follow

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

        # Calculate direction
        dx = target_pixel[0] - self.position[0]
        dy = target_pixel[1] - self.position[1]
        dist = math.sqrt(dx*dx + dy*dy)

        if dist > 0:
            dx /= dist
            dy /= dist

        # Proposed new position
        new_x = self.position[0] + dx * self.move_speed
        new_y = self.position[1] + dy * self.move_speed

        # Check collision with the matrix
        if not self.check_collision((new_x, new_y)):
            self.position = (new_x, new_y)

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
            (col, row-1),
            (col, row+1),
            (col-1, row),
            (col+1, row)
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
            return True  # out of bounds = collision
        col, row = grid_cell
        return (matrix[row][col] == 0)

    def is_walkable(self, cell):
        """Check if the cell in the matrix is walkable."""
        col, row = cell
        if not self.in_bounds(cell):
            return False
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
        return self.position
