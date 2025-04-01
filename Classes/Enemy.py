import math
import random
import time
import pygame
from collections import deque

from constants.matrix_sizes import PIXEL_ONE_X, PIXEL_ONE_Y, matrix, GRID_ROWS, GRID_COLS

class Enemy:
    def __init__(self, position, patrolling_area, move_speed=3, update_interval=1):
        """
        Initialize the enemy with a starting pixel position, a designated patrolling area,
        a movement speed, and an update interval.
        """
        # Load enemy images for animations in each direction.
        self.images = {
            'down': [
                pygame.transform.scale(
                    pygame.image.load("../assets/enemy_down_1.png").convert_alpha(), (40, 40)
                ),
                pygame.transform.scale(
                    pygame.image.load("../assets/enemy_down_2.png").convert_alpha(), (40, 40)
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
        self.position = position  # Should be at a cell center
        self.move_speed = random.randint(0,1)
        self.update_interval = update_interval

        # Animation variables.
        self.frames_per_step = 10
        self.frame_timer = 0
        self.current_frame = 0
        self.current_image = self.images[self.direction][self.current_frame]

        self.patrolling_area = patrolling_area
        # Initialize the path cache (still used in other parts) before building the patrol route.
        self._path_cache = {}
        # Build the patrol route covering all walkable cells in the patrol area.
        self.complete_patrol_route = self.build_exhaustive_patrol_route()
        self.patrol_index = 0

    def build_exhaustive_patrol_route(self):
        """
        Generate a patrol route that visits every walkable cell (candidate) in the patrol area.
        First, perform DFS starting from the enemy's position. Then, if any candidate cells remain
        unvisited (i.e. the area is not fully connected from the start), use BFS to jump to an
        unvisited cell and continue the DFS from there.
        Finally, ensure the route ends at the starting cell.
        """
        # Define grid boundaries from the patrolling area.
        x_min, y_min, x_max, y_max = self.patrolling_area
        col_min = int(x_min // PIXEL_ONE_X)
        row_min = int(y_min // PIXEL_ONE_Y)
        col_max = int(x_max // PIXEL_ONE_X)
        row_max = int(y_max // PIXEL_ONE_Y)
        
        # Build the set of candidate (walkable) cells.
        candidates = set()
        for row in range(row_min, row_max + 1):
            for col in range(col_min, col_max + 1):
                if 0 <= col < GRID_COLS and 0 <= row < GRID_ROWS:
                    if matrix[row][col] == 1:
                        candidates.add((col, row))
        
        start = self.pixel_to_grid(self.position)
        visited = set()
        route = []
        
        def dfs(cell):
            """Standard DFS that visits every candidate reachable from cell."""
            visited.add(cell)
            route.append(cell)
            for neighbor in self.get_neighbors(cell):  # fixed order: right, down, left, up
                if neighbor in candidates and neighbor not in visited:
                    dfs(neighbor)
                    # Append the current cell as a backtracking step.
                    route.append(cell)
        
        # First, do DFS from the starting cell.
        dfs(start)
        
        # If some candidates remain unvisited (disconnected regions),
        # find a route from the current end of route to one unvisited cell and DFS from there.
        while candidates - visited:
            # Pick one unvisited candidate.
            next_cell = (candidates - visited).pop()
            # Compute a connecting path using BFS from the last cell in route to next_cell.
            current_end = route[-1]
            jump = self.find_path(next_cell, start_cell=current_end)
            if jump and len(jump) > 1:
                # Append the jump (skip the first cell because it is current_end).
                route.extend(jump[1:])
            else:
                # If no jump found, directly add the cell.
                route.append(next_cell)
            # Continue DFS from this new cell.
            dfs(next_cell)
        
        # Finally, append the start cell to close the loop if not already there.
        if route[-1] != start:
            route.append(start)
        return route
    
    def smooth_route(self, route):
        """
        Optimize the patrol route by removing unnecessary waypoints.
        If three consecutive waypoints lie on a straight line, remove the middle one.
        """
        if not route or len(route) < 3:
            return route
        smoothed = [route[0]]
        for i in range(1, len(route) - 1):
            prev = smoothed[-1]
            curr = route[i]
            nxt = route[i + 1]
            dx1, dy1 = curr[0] - prev[0], curr[1] - prev[1]
            dx2, dy2 = nxt[0] - curr[0], nxt[1] - curr[1]
            if dx1 == dx2 and dy1 == dy2:
                continue
            smoothed.append(curr)
        smoothed.append(route[-1])
        return smoothed

    def move_patrol_area(self):
        """
        Move the enemy toward the center of the next cell in its patrol route.
        If the direct step toward the next cell is blocked, compute a mini path via BFS and follow it.
        Once the mini path is finished, resume the normal patrol route.
        """
        # If currently following a mini path, follow it first.
        if hasattr(self, '_mini_path') and self._mini_path is not None and len(self._mini_path) > 0:
            target = self._mini_path[0]
            target_pixel = self.grid_to_pixel(target)
            dx = target_pixel[0] - self.position[0]
            dy = target_pixel[1] - self.position[1]
            dist = math.hypot(dx, dy)
            if dist < self.move_speed:
                self.position = target_pixel
                self._mini_path.pop(0)
            else:
                dx_norm = dx / dist
                dy_norm = dy / dist
                new_x = self.position[0] + dx_norm * self.move_speed
                new_y = self.position[1] + dy_norm * self.move_speed
                self.position = (new_x, new_y)
            # If mini path is finished, clear it and update patrol index.
            if not self._mini_path:
                self._mini_path = None
                self.patrol_index = (self.patrol_index + 1) % len(self.complete_patrol_route)
        else:
            # No mini path: attempt direct movement toward next patrol cell.
            target_cell = self.complete_patrol_route[self.patrol_index]
            target_pixel = self.grid_to_pixel(target_cell)
            dx = target_pixel[0] - self.position[0]
            dy = target_pixel[1] - self.position[1]
            dist = math.hypot(dx, dy)
            if dist < self.move_speed:
                self.position = target_pixel
                self.patrol_index = (self.patrol_index + 1) % len(self.complete_patrol_route)
            else:
                dx_norm = dx / dist
                dy_norm = dy / dist
                new_x = self.position[0] + dx_norm * self.move_speed
                new_y = self.position[1] + dy_norm * self.move_speed
                # Check if the step to (new_x, new_y) collides.
                if self.check_collision((new_x, new_y)):
                    # Compute BFS mini path from the current grid cell to the target patrol cell.
                    current_grid = self.pixel_to_grid(self.position)
                    mini_path = self.find_path(target_cell, start_cell=current_grid)
                    if mini_path and len(mini_path) > 1:
                        # Skip the first cell (current position) and store the mini path.
                        self._mini_path = mini_path[1:]
                        # Immediately follow the first step of the mini path.
                        target = self._mini_path[0]
                        target_pixel = self.grid_to_pixel(target)
                        dx = target_pixel[0] - self.position[0]
                        dy = target_pixel[1] - self.position[1]
                        dist = math.hypot(dx, dy)
                        if dist < self.move_speed:
                            self.position = target_pixel
                            self._mini_path.pop(0)
                        else:
                            dx_norm = dx / dist
                            dy_norm = dy / dist
                            new_x = self.position[0] + dx_norm * self.move_speed
                            new_y = self.position[1] + dy_norm * self.move_speed
                            self.position = (new_x, new_y)
                    else:
                        # Fallback: if no mini path is found, move directly.
                        self.position = (new_x, new_y)
                else:
                    # Direct step is clear.
                    self.position = (new_x, new_y)
        # Update facing direction based on movement.
        if abs(dx) > abs(dy):
            self.direction = 'right' if dx > 0 else 'left'
        else:
            self.direction = 'down' if dy > 0 else 'up'
        # Update animation frame.
        self.frame_timer += 1
        if self.frame_timer >= self.frames_per_step:
            self.frame_timer = 0
            self.current_frame = (self.current_frame + 1) % 2
        self.current_image = self.images[self.direction][self.current_frame]
        """
        Move the enemy toward the center of the next cell in its patrol route.
        If the enemy is close enough to the target cell, snap exactly to that center and advance the waypoint.
        """
        if not hasattr(self, 'complete_patrol_route') or not self.complete_patrol_route:
            return

        if self.patrol_index >= len(self.complete_patrol_route):
            self.patrol_index = 0

        target_cell = self.complete_patrol_route[self.patrol_index]
        target_pixel = self.grid_to_pixel(target_cell)
        dx = target_pixel[0] - self.position[0]
        dy = target_pixel[1] - self.position[1]
        dist = math.hypot(dx, dy)

        if dist < self.move_speed:
            self.position = target_pixel
            self.patrol_index = (self.patrol_index + 1) % len(self.complete_patrol_route)
        else:
            dx_norm = dx / dist
            dy_norm = dy / dist
            new_x = self.position[0] + dx_norm * self.move_speed
            new_y = self.position[1] + dy_norm * self.move_speed
            self.position = (new_x, new_y)

        # Update facing direction.
        if abs(dx) > abs(dy):
            self.direction = 'right' if dx > 0 else 'left'
        else:
            self.direction = 'down' if dy > 0 else 'up'

        # Update animation frame.
        self.frame_timer += 1
        if self.frame_timer >= self.frames_per_step:
            self.frame_timer = 0
            self.current_frame = (self.current_frame + 1) % 2
        self.current_image = self.images[self.direction][self.current_frame]

    def update(self, player_pos):
        """
        Update the enemy's behavior. Currently, it only patrols its route.
        The player_pos parameter is accepted for future BFS/chasing logic.
        """
        self.move_patrol_area()

    # --- BFS and auxiliary functions (kept for future use) ---

    def find_path(self, target_cell, start_cell=None):
        """
        Use BFS to find a path from start_cell to target_cell.
        If start_cell is None, uses the enemy's current grid cell.
        Returns a list of grid cells (including both endpoints).
        """
        start = start_cell if start_cell is not None else self.pixel_to_grid(self.position)
        if not self.is_walkable(start) or not self.is_walkable(target_cell):
            return []
        queue = deque([start])
        came_from = {start: None}
        visited = {start}
        found = False
        while queue and not found:
            current = queue.popleft()
            if current == target_cell:
                found = True
                break
            for neighbor in self.get_neighbors(current):
                if neighbor not in visited and self.is_walkable(neighbor):
                    visited.add(neighbor)
                    came_from[neighbor] = current
                    queue.append(neighbor)
        if not found:
            return []
        path = []
        node = target_cell
        while node != start:
            path.append(node)
            node = came_from[node]
        path.append(start)
        path.reverse()
        return path

    def get_neighbors(self, cell):
        """
        Return valid (right, down, left, up) neighbors for a given grid cell.
        """
        col, row = cell
        neighbors = [
            (col + 1, row),  # right
            (col, row + 1),  # down
            (col - 1, row),  # left
            (col, row - 1)   # up
        ]
        return [(c, r) for (c, r) in neighbors if 0 <= c < GRID_COLS and 0 <= r < GRID_ROWS]

    def check_collision(self, pixel_pos):
        """
        Check if the given pixel position collides with a blocked cell.
        """
        grid_cell = self.pixel_to_grid(pixel_pos)
        if not self.in_bounds(grid_cell):
            return True
        col, row = grid_cell
        return (matrix[row][col] == 0)

    def is_walkable(self, cell):
        """
        Check if a grid cell is walkable.
        """
        col, row = cell
        if not self.in_bounds(cell):
            return False
        return (matrix[row][col] == 1 or matrix[row][col] == 2)

    def pixel_to_grid(self, pixel_pos):
        """
        Convert pixel coordinates to a grid cell (col, row).
        """
        x, y = pixel_pos
        col = int(x // PIXEL_ONE_X)
        row = int(y // PIXEL_ONE_Y)
        return (col, row)

    def grid_to_pixel(self, cell):
        """
        Convert a grid cell (col, row) to the pixel coordinates of its center.
        """
        col, row = cell
        px = col * PIXEL_ONE_X + PIXEL_ONE_X / 2
        py = row * PIXEL_ONE_Y + PIXEL_ONE_Y / 2
        return (px, py)

    def in_bounds(self, cell):
        """
        Check if a grid cell is within bounds.
        """
        col, row = cell
        return 0 <= col < GRID_COLS and 0 <= row < GRID_ROWS

    def get_position(self):
        """
        Return the enemy's current pixel position.
        """
        return self.position

    def draw(self, screen):
        """
        Draw the enemy sprite on the screen with a fixed offset.
        """
        x_offset = 20
        y_offset = 20
        screen.blit(self.current_image, (self.position[0] - x_offset, self.position[1] - y_offset))
