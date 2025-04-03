import math
import time
from collections import deque
import pygame

from constants.matrix_sizes import PIXEL_ONE_X, PIXEL_ONE_Y, matrix, GRID_ROWS, GRID_COLS

class Enemy:
    def __init__(self, position, patrol_route, move_speed=1.3, update_interval=1):
        """
        Initialize the enemy with a starting pixel position, a precomputed patrol route (list of grid cells),
        a patrol movement speed, and an update interval.
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
        # Load alert images.
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
        self.patrol_speed = 1.5    # Patrol speed
        self.alert_speed = 2.9     # Alert (chase) speed
        self.update_interval = update_interval
        self.last_update_time = time.time()

        # Animation variables.
        self.frames_per_step = 10
        self.frame_timer = 0
        self.current_frame = 0
        self.current_image = self.images[self.direction][self.current_frame]

        # Precomputed patrol route (list of grid cells).
        self.complete_patrol_route = patrol_route  
        self.patrol_index = 0

        # For alert chasing: BFS path computed towards the player.
        self.path = []

        # AI state management.
        self.state = "patrol"  # "patrol" or "alert"
        self.alert_start_time = None
        self.patrol_index_backup = None

        # Attributes to be set externally:
        # self.route_marker: a unique integer marker for overlay.
        # self.route_color: an RGBA color tuple for overlay.
        
    def update(self, player_pos):
        enemy_cell = self.pixel_to_grid(self.position)
        player_cell = self.pixel_to_grid(player_pos)
        manhattan_dist = abs(enemy_cell[0] - player_cell[0]) + abs(enemy_cell[1] - player_cell[1])
        
        # If the player is hidden (matrix value 3), do not chase.
        if matrix[player_cell[1]][player_cell[0]] == 3:
            self.state = "patrol"
            self.move_patrol_area()
        # Otherwise, if the player is near, switch to alert mode.
        elif manhattan_dist <= 2:
            if self.state != "alert":
                self.state = "alert"
                self.patrol_index_backup = self.patrol_index
            self.move_alert(player_pos)
        # If in alert mode but the player is far away, return to patrol.
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
        else:
            if self.state == "alert":
                self.move_alert(player_pos)
            else:
                self.move_patrol_area()

        # Optionally mark the matrix cell for overlay.
        col, row = self.pixel_to_grid(self.position)
        matrix[row][col] = self.route_marker

    def can_see_player(self, player_pos):
        """
        Returns True if there is a clear line-of-sight between the enemy and the player.
        Uses Bresenham's Line Algorithm to iterate through the grid cells between the enemy and player.
        If any cell along the line is a wall (matrix value 0), returns False.
        """
        enemy_cell = self.pixel_to_grid(self.position)
        player_cell = self.pixel_to_grid(player_pos)
        line = self.bresenham_line(enemy_cell[0], enemy_cell[1], player_cell[0], player_cell[1])
        for cell in line:
            col, row = cell
            if matrix[row][col] == 0:
                return False
        return True

    def bresenham_line(self, x0, y0, x1, y1):
        """
        Bresenham's Line Algorithm.
        Returns a list of grid cells from (x0, y0) to (x1, y1).
        """
        cells = []
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        x, y = x0, y0
        sx = -1 if x0 > x1 else 1
        sy = -1 if y0 > y1 else 1
        if dx > dy:
            err = dx / 2.0
            while x != x1:
                cells.append((x, y))
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                x += sx
        else:
            err = dy / 2.0
            while y != y1:
                cells.append((x, y))
                err -= dx
                if err < 0:
                    x += sx
                    err += dy
                y += sy
        cells.append((x1, y1))
        return cells

    def go_to_point(self, target_pixel):
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
        # First, check if the enemy still has a clear view.
        if not self.can_see_player(player_pos):
            # If something is in between, stop alert mode and return to patrol.
            self.state = "patrol"
            self.move_patrol_area()
            return

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
        col, row = cell
        neighbors = [
            (col, row - 1),
            (col, row + 1),
            (col - 1, row),
            (col + 1, row)
        ]
        return [(c, r) for (c, r) in neighbors if 0 <= c < GRID_COLS and 0 <= r < GRID_ROWS]

    def check_collision(self, pixel_pos):
        grid_cell = self.pixel_to_grid(pixel_pos)
        if not self.in_bounds(grid_cell):
            return True
        col, row = grid_cell
        return (matrix[row][col] == 0)

    def is_walkable(self, cell):
        col, row = cell
        if not self.in_bounds(cell):
            return False
        return (matrix[row][col] == 1 or matrix[row][col] == 2 or matrix[row][col] >= 5)

    def pixel_to_grid(self, pixel_pos):
        x, y = pixel_pos
        col = int(x // PIXEL_ONE_X)
        row = int(y // PIXEL_ONE_Y)
        return (col, row)

    def grid_to_pixel(self, cell):
        col, row = cell
        px = col * PIXEL_ONE_X + PIXEL_ONE_X / 2
        py = row * PIXEL_ONE_Y + PIXEL_ONE_Y / 2
        return (px, py)

    def in_bounds(self, cell):
        col, row = cell
        return (0 <= col < GRID_COLS and 0 <= row < GRID_ROWS)

    def get_position(self):
        return self.position

    def draw(self, screen):
        x_offset = 20
        y_offset = 20
        screen.blit(self.current_image, (self.position[0] - x_offset, self.position[1] - y_offset))
