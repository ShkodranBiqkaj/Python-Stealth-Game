import math
import time
from collections import deque
import pygame

from constants.matrix_sizes import PIXEL_ONE_X, PIXEL_ONE_Y, matrix, GRID_ROWS, GRID_COLS

class Enemy:
    def __init__(self, position, patrolling_area, move_speed=3, update_interval=1):
        """
        :param position: (x, y) pixel coordinates for the enemy's start
        :param move_speed: pixels the enemy moves each update
        :param update_interval: seconds between path recalculations
        """
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
        self.position = position
        self.move_speed = move_speed
        self.update_interval = update_interval

        self.last_update_time = time.time()
        self.path = []  # Used when chasing the player
        self.frames_per_step = 10
        self.frame_timer = 0
        self.current_frame = 0
        self.current_image = self.images[self.direction][self.current_frame]
        self.patrolling_area = patrolling_area

        # Build a complete patrol route covering all walkable cells in the patrol area.
        self.build_complete_patrol_route()
        self.patrol_index = 0

        # Placeholder for stimulus; when True the enemy chases the player.
        self.stimulus = False

    def build_complete_patrol_route(self):
        """
        Build an ordered list of grid cells (only walkable ones) from the patrolling_area.
        We use a greedy algorithm (choosing the nearest unvisited cell by Manhattan distance)
        starting from the enemy's current grid cell. Then we smooth the route to remove
        unnecessary angular changes and finally close the loop by appending the starting cell.
        """
        x_min, y_min, x_max, y_max = self.patrolling_area
        col_min = int(x_min // PIXEL_ONE_X)
        row_min = int(y_min // PIXEL_ONE_Y)
        col_max = int(x_max // PIXEL_ONE_X)
        row_max = int(y_max // PIXEL_ONE_Y)

        # Create candidate list from walkable cells (matrix value 1)
        candidates = []
        for row in range(row_min, row_max + 1):
            for col in range(col_min, col_max + 1):
                if 0 <= col < GRID_COLS and 0 <= row < GRID_ROWS:
                    if matrix[row][col] == 1:
                        candidates.append((col, row))

        start = self.pixel_to_grid(self.position)
        route = [start]
        if start in candidates:
            candidates.remove(start)
        current = start

        while candidates:
            next_cell = min(candidates, key=lambda cell: abs(cell[0] - current[0]) + abs(cell[1] - current[1]))
            route.append(next_cell)
            candidates.remove(next_cell)
            current = next_cell

        # Close the loop by returning to start
        route.append(start)
        # Smooth the route to remove unnecessary turns
        self.complete_patrol_route = self.smooth_route(route)

    def smooth_route(self, route):
        """
        A simple route smoothing: if three consecutive waypoints
        lie on a straight line, remove the middle one.
        """
        if not route or len(route) < 3:
            return route
        smoothed = [route[0]]
        for i in range(1, len(route) - 1):
            prev = smoothed[-1]
            curr = route[i]
            nxt = route[i + 1]
            # Calculate differences in x and y for both segments
            dx1 = curr[0] - prev[0]
            dy1 = curr[1] - prev[1]
            dx2 = nxt[0] - curr[0]
            dy2 = nxt[1] - curr[1]
            # If the direction doesn't change, skip the current waypoint.
            if dx1 == dx2 and dy1 == dy2:
                continue
            smoothed.append(curr)
        smoothed.append(route[-1])
        return smoothed

    def find_path_to_target(self, target_cell):
        """
        Perform BFS to find a path from the enemy's current grid cell to target_cell.
        Returns a list of grid cells (path) or an empty list if no path is found.
        """
        start = self.pixel_to_grid(self.position)
        goal = target_cell
        if not self.is_walkable(start) or not self.is_walkable(goal):
            return []
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
        if not found:
            return []
        path = []
        node = goal
        while node != start:
            path.append(node)
            node = came_from[node]
        path.reverse()
        return path

    def move_patrol_area(self):
        """
        Move the enemy along the complete patrol route.
        A BFS path is computed from the enemy’s current grid cell to the next patrol waypoint,
        and the enemy moves along the first step of that path.
        When it gets close enough to the waypoint, it advances to the next one.
        """
        if not hasattr(self, 'complete_patrol_route') or not self.complete_patrol_route:
            return
        if self.patrol_index >= len(self.complete_patrol_route):
            self.patrol_index = 0
        target_cell = self.complete_patrol_route[self.patrol_index]
        path = self.find_path_to_target(target_cell)
        if not path:
            self.patrol_index += 1
            return
        next_cell = path[0]
        target_pixel = self.grid_to_pixel(next_cell)
        dx = target_pixel[0] - self.position[0]
        dy = target_pixel[1] - self.position[1]
        dist = math.hypot(dx, dy)
        if dist > 0:
            dx /= dist
            dy /= dist
        if abs(dx) > abs(dy):
            self.direction = 'right' if dx > 0 else 'left'
        else:
            self.direction = 'down' if dy > 0 else 'up'
        new_x = self.position[0] + dx * self.move_speed
        new_y = self.position[1] + dy * self.move_speed
        if not self.check_collision((new_x, new_y)):
            self.position = (new_x, new_y)
            self.frame_timer += 1
            if self.frame_timer >= self.frames_per_step:
                self.frame_timer = 0
                self.current_frame = (self.current_frame + 1) % 2
            self.current_image = self.images[self.direction][self.current_frame]
        new_dist = math.hypot(target_pixel[0] - self.position[0], target_pixel[1] - self.position[1])
        if new_dist < self.move_speed:
            self.patrol_index += 1

    def move(self, player_pos):
        """
        Move the enemy toward the player using BFS.
        """
        current_time = time.time()
        if current_time - self.last_update_time >= self.update_interval:
            self.find_path(player_pos)
            self.last_update_time = current_time
        if not self.path:
            return
        next_cell = self.path[0]
        target_pixel = self.grid_to_pixel(next_cell)
        dx = target_pixel[0] - self.position[0]
        dy = target_pixel[1] - self.position[1]
        dist = math.sqrt(dx * dx + dy * dy)
        if dist > 0:
            dx /= dist
            dy /= dist
        if abs(dx) > abs(dy):
            self.direction = 'right' if dx > 0 else 'left'
        else:
            self.direction = 'down' if dy > 0 else 'up'
        new_x = self.position[0] + dx * self.move_speed
        new_y = self.position[1] + dy * self.move_speed
        if not self.check_collision((new_x, new_y)):
            self.position = (new_x, new_y)
            self.frame_timer += 1
            if self.frame_timer >= self.frames_per_step:
                self.frame_timer = 0
                self.current_frame = (self.current_frame + 1) % 2
            self.current_image = self.images[self.direction][self.current_frame]
            new_dist = math.sqrt((target_pixel[0] - new_x) ** 2 + (target_pixel[1] - new_y) ** 2)
            if new_dist < self.move_speed:
                self.path.pop(0)
        else:
            self.path.pop(0)
            self.find_path(player_pos)

    def update(self, player_pos):
        """
        Update the enemy's behavior.
        If stimulus is present, chase the player; otherwise, follow the patrol route.
        """
        if self.stimulus:
            self.move(player_pos)
        else:
            self.move_patrol_area()

    def find_path(self, player_pos):
        """
        BFS pathfinding from the enemy's current grid cell to the player's grid cell.
        """
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
        """
        Return valid up/down/left/right neighbors for BFS.
        """
        col, row = cell
        neighbors = [
            (col, row - 1),
            (col, row + 1),
            (col - 1, row),
            (col + 1, row)
        ]
        valid = [(c, r) for (c, r) in neighbors if 0 <= c < GRID_COLS and 0 <= r < GRID_ROWS]
        return valid

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
        Check if a cell is walkable.
        """
        col, row = cell
        if not self.in_bounds(cell):
            return False
        return (matrix[row][col] == 1 or matrix[row][col] == 2)

    def pixel_to_grid(self, pixel_pos):
        """
        Convert pixel coordinates to grid cell (col, row).
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
        Check if a cell is within the grid bounds.
        """
        c, r = cell
        return (0 <= c < GRID_COLS and 0 <= r < GRID_ROWS)

    def get_position(self):
        """
        Return the enemy's current pixel position.
        """
        return self.position

    def draw(self, screen):
        """
        Draw the enemy sprite on the screen.
        """
        x_offset = 20
        y_offset = 20
        screen.blit(self.current_image, (self.position[0] - x_offset, self.position[1] - y_offset))
