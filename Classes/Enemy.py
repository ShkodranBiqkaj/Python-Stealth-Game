import math
import time
from collections import deque
import pygame

from constants.matrix_sizes import PIXEL_ONE_X, PIXEL_ONE_Y, matrix, GRID_ROWS, GRID_COLS

class Enemy:
    def __init__(self, position, patrol_route, move_speed=1.3, update_interval=1):
        """
        Initialize the enemy with a starting pixel position, a precomputed patrol route (list of grid cells),
        a patrol movement speed (slow), and an update interval.
        """
        # Load normal enemy images.
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
        # Load alert images (with "_alert" in their names).
        self.alert_images = {
            'down': [
                pygame.transform.scale(
                    pygame.image.load("../assets/enemy_down_alert_1.png").convert_alpha(), (40, 40)
                ),
                pygame.transform.scale(
                    pygame.image.load("../assets/enemy_down_alert_2.png").convert_alpha(), (40, 40)
                )
            ],
            'up': [
                pygame.transform.scale(
                    pygame.image.load("../assets/enemy_up_alert_1.png").convert_alpha(), (40, 40)
                ),
                pygame.transform.scale(
                    pygame.image.load("../assets/enemy_up_alert_2.png").convert_alpha(), (40, 40)
                )
            ],
            'left': [
                pygame.transform.scale(
                    pygame.image.load("../assets/enemy_left_alert_1.png").convert_alpha(), (40, 40)
                ),
                pygame.transform.scale(
                    pygame.image.load("../assets/enemy_left_alert_2.png").convert_alpha(), (40, 40)
                )
            ],
            'right': [
                pygame.transform.scale(
                    pygame.image.load("../assets/enemy_right_alert_1.png").convert_alpha(), (40, 40)
                ),
                pygame.transform.scale(
                    pygame.image.load("../assets/enemy_right_alert_2.png").convert_alpha(), (40, 40)
                )
            ]
        }
        
        self.direction = 'down'
        self.position = position  # Pixel coordinates
        # Base (patrol) speed is slow.
        self.patrol_speed = 1.5 
        # Alert (chase) speed is faster.
        self.alert_speed = 3
        self.update_interval = update_interval
        self.last_update_time = time.time()

        # Animation variables.
        self.frames_per_step = 10
        self.frame_timer = 0
        self.current_frame = 0
        self.current_image = self.images[self.direction][self.current_frame]

        # Patrol route (precomputed externally): list of grid cells.
        self.complete_patrol_route = patrol_route  
        self.patrol_index = 0

        # For chasing: store the BFS path (list of grid cells) in self.path.
        self.path = []

        # AI state management.
        self.state = "patrol"  # "patrol" or "alert"
        self.alert_start_time = None
        self.patrol_index_backup = None

    def update(self, player_pos):
        # Check if the player is hidden.
        player_cell = self.pixel_to_grid(player_pos)
        # Note: matrix is indexed as matrix[row][col].
        if matrix[player_cell[1]][player_cell[0]] == 3:
            # Player is hidden; force enemy to remain in patrol mode.
            self.state = "patrol"
            self.move_patrol_area()
            return

        enemy_cell = self.pixel_to_grid(self.position)
        manhattan_dist = abs(enemy_cell[0] - player_cell[0]) + abs(enemy_cell[1] - player_cell[1])
        
        # Enter alert mode if within 2 blocks.
        if manhattan_dist <= 2:
            if self.state != "alert":
                self.state = "alert"
                self.patrol_index_backup = self.patrol_index
            self.move_alert(player_pos)
        # Exit alert mode if player is more than 5 blocks away.
        elif self.state == "alert" and manhattan_dist > 5:
            self.state = "patrol"
            if self.patrol_index_backup is not None:
                self.patrol_index = self.patrol_index_backup
            if not self.is_walkable(self.pixel_to_grid(self.position)):
                target_cell = self.find_nearest_walkable()
                if target_cell:
                    target_pixel = self.grid_to_pixel(target_cell)
                    self.go_to_point(target_pixel)
                    return
            self.move_patrol_area()
        # Otherwise, if already alert, continue alert behavior; else patrol.
        else:
            if self.state == "alert":
                self.move_alert(player_pos)
            else:
                self.move_patrol_area()

    def go_to_point(self, target_pixel):
        """
        Compute a valid BFS path from the enemy's current grid cell to the cell corresponding to target_pixel,
        then follow the next step along that path.
        """
        target_cell = self.pixel_to_grid(target_pixel)
        start_cell = self.pixel_to_grid(self.position)
        if start_cell == target_cell:
            return
        path = self.find_path_between(start_cell, target_cell)
        if not path or len(path) < 2:
            return
        next_cell = path[1]
        next_pixel = self.grid_to_pixel(next_cell)
        dx = next_pixel[0] - self.position[0]
        dy = next_pixel[1] - self.position[1]
        dist = math.hypot(dx, dy)
        if dist < self.patrol_speed:
            self.position = next_pixel
        else:
            dx_norm = dx / dist
            dy_norm = dy / dist
            new_x = self.position[0] + dx_norm * self.patrol_speed
            new_y = self.position[1] + dy_norm * self.patrol_speed
            self.position = (new_x, new_y)
        self.update_animation(dx, dy)

    def find_path_between(self, start, goal):
        """
        Use BFS to compute a path (a list of grid cells) from start to goal.
        Only walkable cells (matrix value 1 or 2) are enqueued.
        Returns a list of grid cells (including start and goal) representing the path.
        """
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
        path.append(start)
        path.reverse()
        return path

    def find_nearest_walkable(self):
        """
        Use BFS to find the nearest walkable grid cell from the enemy's current grid cell.
        Returns that grid cell.
        """
        start = self.pixel_to_grid(self.position)
        if self.is_walkable(start):
            return start
        queue = deque([start])
        visited = {start}
        while queue:
            cell = queue.popleft()
            if self.is_walkable(cell):
                return cell
            for neighbor in self.get_neighbors(cell):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        return None

    def move_patrol_area(self):
        """
        Move the enemy along its precomputed patrol route (complete_patrol_route).
        Compute a BFS path from the enemy's current cell to the next patrol target and follow the next step.
        """
        if not self.complete_patrol_route:
            return
        if self.patrol_index >= len(self.complete_patrol_route):
            self.patrol_index = 0
        target_cell = self.complete_patrol_route[self.patrol_index]
        start_cell = self.pixel_to_grid(self.position)
        path = self.find_path_between(start_cell, target_cell)
        if path and len(path) >= 2:
            next_cell = path[1]
            target_pixel = self.grid_to_pixel(next_cell)
        else:
            target_pixel = self.grid_to_pixel(target_cell)
        dx = target_pixel[0] - self.position[0]
        dy = target_pixel[1] - self.position[1]
        dist = math.hypot(dx, dy)
        if dist < self.patrol_speed:
            self.position = target_pixel
            self.patrol_index = (self.patrol_index + 1) % len(self.complete_patrol_route)
        else:
            dx_norm = dx / dist
            dy_norm = dy / dist
            new_x = self.position[0] + dx_norm * self.patrol_speed
            new_y = self.position[1] + dy_norm * self.patrol_speed
            self.position = (new_x, new_y)
        self.update_animation(dx, dy)

    def move_alert(self, player_pos):
        """
        Chase the player using BFS.
        Recalculate the BFS path every update_interval seconds.
        Use alert_speed (fast) for movement.
        """
        if time.time() - self.last_update_time >= self.update_interval:
            self.find_path(player_pos)
            self.last_update_time = time.time()
        if not self.path:
            return
        next_cell = self.path[0]
        target_pixel = self.grid_to_pixel(next_cell)
        dx = target_pixel[0] - self.position[0]
        dy = target_pixel[1] - self.position[1]
        dist = math.hypot(dx, dy)
        if dist > 0:
            dx /= dist
            dy /= dist
        new_x = self.position[0] + dx * self.alert_speed
        new_y = self.position[1] + dy * self.alert_speed
        if not self.check_collision((new_x, new_y)):
            self.position = (new_x, new_y)
            self.frame_timer += 1
            if self.frame_timer >= self.frames_per_step:
                self.frame_timer = 0
                self.current_frame = (self.current_frame + 1) % 2
            self.current_image = self.alert_images[self.direction][self.current_frame]
            new_dist = math.hypot(target_pixel[0] - self.position[0],
                                  target_pixel[1] - self.position[1])
            if new_dist < self.alert_speed:
                self.path.pop(0)
        else:
            self.path.pop(0)
            self.find_path(player_pos)
        self.update_animation(dx, dy)

    def update_animation(self, dx, dy):
        """
        Update facing direction and animation frame.
        Use alert images if in alert mode; otherwise, use normal images.
        """
        if abs(dx) > abs(dy):
            self.direction = 'right' if dx > 0 else 'left'
        else:
            self.direction = 'down' if dy > 0 else 'up'
        self.frame_timer += 1
        if self.frame_timer >= self.frames_per_step:
            self.frame_timer = 0
            self.current_frame = (self.current_frame + 1) % 2
        if self.state == "alert":
            self.current_image = self.alert_images[self.direction][self.current_frame]
        else:
            self.current_image = self.images[self.direction][self.current_frame]

    def find_path(self, player_pos):
        """
        Use BFS to compute a path from the enemy's current grid cell to the player's grid cell.
        Only walkable cells (matrix value 1 or 2) are considered.
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
        if not found:
            self.path = []
            return
        path = []
        node = goal
        while node != start:
            path.append(node)
            node = came_from[node]
        path.append(start)
        path.reverse()
        self.path = path

    def get_neighbors(self, cell):
        """Return valid (up, down, left, right) neighbors for BFS."""
        col, row = cell
        neighbors = [
            (col, row - 1),
            (col, row + 1),
            (col - 1, row),
            (col + 1, row)
        ]
        return [(c, r) for (c, r) in neighbors if 0 <= c < GRID_COLS and 0 <= r < GRID_ROWS]

    def check_collision(self, pixel_pos):
        """
        Convert pixel position to a grid cell and check for collision (matrix value 0).
        """
        grid_cell = self.pixel_to_grid(pixel_pos)
        if not self.in_bounds(grid_cell):
            return True
        col, row = grid_cell
        return (matrix[row][col] == 0)

    def is_walkable(self, cell):
        """
        Return True if the given cell is walkable (matrix value 1 or 2).
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
        Return True if the cell is within grid bounds.
        """
        col, row = cell
        return (0 <= col < GRID_COLS and 0 <= row < GRID_ROWS)

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
