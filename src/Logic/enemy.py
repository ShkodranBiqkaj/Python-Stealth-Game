# src/Logic/enemy.py

import math
import time
from collections import deque
import pygame

class Enemy:
    def __init__(
        self,
        position,
        patrol_route,
        matrix,
        grid_rows,
        grid_cols,
        tile_size,
        move_speed=1.3,
        update_interval=0.1
    ):
        """
        Enemy AI that patrols, sees the player (LoS + Manhattan),
        and switches to alert chase when close.
        """
        # grid & tile info
        self.GRID_ROWS = grid_rows
        self.GRID_COLS = grid_cols
        self.PIXEL_ONE_X, self.PIXEL_ONE_Y = tile_size

        #state & movement
        self.position = position  # pixel coords (x, y)
        self.patrol_speed = move_speed
        self.alert_speed = 2.6
        self.update_interval = update_interval
        self.last_update_time = time.time()
        self.matrix = matrix

        #load normal enemy images
        self.images = {
            'down': [
                pygame.transform.scale(
                    pygame.image.load("assets/enemy_down_1.png").convert_alpha(), (40, 40)
                ),
                pygame.transform.scale(
                    pygame.image.load("assets/enemy_down_2.png").convert_alpha(), (40, 40)
                )
            ],
            'up': [
                pygame.transform.scale(
                    pygame.image.load("assets/enemy_up_1.png").convert_alpha(), (40, 40)
                ),
                pygame.transform.scale(
                    pygame.image.load("assets/enemy_up_2.png").convert_alpha(), (40, 40)
                )
            ],
            'left': [
                pygame.transform.scale(
                    pygame.image.load("assets/enemy_left_1.png").convert_alpha(), (40, 40)
                ),
                pygame.transform.scale(
                    pygame.image.load("assets/enemy_left_2.png").convert_alpha(), (40, 40)
                )
            ],
            'right': [
                pygame.transform.scale(
                    pygame.image.load("assets/enemy_right_1.png").convert_alpha(), (40, 40)
                ),
                pygame.transform.scale(
                    pygame.image.load("assets/enemy_right_2.png").convert_alpha(), (40, 40)
                )
            ]
        }

        # load alert (chasing) images
        self.alert_images = {
            'down': [
                pygame.transform.scale(
                    pygame.image.load("assets/enemy_down_alert_1.png").convert_alpha(), (40, 40)
                ),
                pygame.transform.scale(
                    pygame.image.load("assets/enemy_down_alert_2.png").convert_alpha(), (40, 40)
                )
            ],
            'up': [
                pygame.transform.scale(
                    pygame.image.load("assets/enemy_up_alert_1.png").convert_alpha(), (40, 40)
                ),
                pygame.transform.scale(
                    pygame.image.load("assets/enemy_up_alert_2.png").convert_alpha(), (40, 40)
                )
            ],
            'left': [
                pygame.transform.scale(
                    pygame.image.load("assets/enemy_left_alert_1.png").convert_alpha(), (40, 40)
                ),
                pygame.transform.scale(
                    pygame.image.load("assets/enemy_left_alert_2.png").convert_alpha(), (40, 40)
                )
            ],
            'right': [
                pygame.transform.scale(
                    pygame.image.load("assets/enemy_right_alert_1.png").convert_alpha(), (40, 40)
                ),
                pygame.transform.scale(
                    pygame.image.load("assets/enemy_right_alert_2.png").convert_alpha(), (40, 40)
                )
            ]
        }

        # animation
        self.frames_per_step = 10
        self.frame_timer = 0
        self.current_frame = 0
        self.direction = 'down'
        self.current_image = self.images[self.direction][self.current_frame]

        #patrol and alert data
        self.complete_patrol_route = patrol_route  #list of (col,row)
        self.patrol_index = 0
        self.path = []  #the BFS path in alert mode

        # AI state
        self.state = "patrol"  #or "alert"
        self.patrol_index_backup = None

        # overlay attributes (set by PatrolGenerator)
        self.route_marker = None
        self.route_color = None

    def update(self, player_pos):
        """
        Called each frame: decide whether to patrol or chase,
        then move and mark overlay.
        """
        enemy_cell = self.pixel_to_grid(self.position)
        player_cell = self.pixel_to_grid(player_pos)
        manhattan = abs(enemy_cell[0] - player_cell[0]) + abs(enemy_cell[1] - player_cell[1])

        # if player is hidden, always patrol
        if self.matrix[player_cell[1]][player_cell[0]] == 3:
            self.state = "patrol"
            self.move_patrol_area()

        # if player is near, go alert
        elif manhattan <= 2:
            if self.state != "alert":
                self.state = "alert"
                self.patrol_index_backup = self.patrol_index
            self.move_alert(player_pos)

        # if chasing but player escaped far away, resume patrol
        elif self.state == "alert" and manhattan > 5:
            self.state = "patrol"
            if self.patrol_index_backup is not None:
                self.patrol_index = self.patrol_index_backup
            # if stuck, find nearest walkable
            if not self.is_walkable(self.pixel_to_grid(self.position)):
                target = self.find_nearest_walkable()
                if target:
                    self.go_to_point(self.grid_to_pixel(target))
                    return
            self.move_patrol_area()

        # otherwise continue with current state
        else:
            if self.state == "alert":
                self.move_alert(player_pos)
            else:
                self.move_patrol_area()

        # mark overlay cell
        col, row = self.pixel_to_grid(self.position)
        if self.route_marker is not None:
            self.matrix[row][col] = self.route_marker

    def can_see_player(self, player_pos):
        """
        Bresenham line-of-sight: if any wall (0) in between, return False.
        """
        start = self.pixel_to_grid(self.position)
        end = self.pixel_to_grid(player_pos)
        for c, r in self.line_of_sight(start[0], start[1], end[0], end[1]):
            if self.matrix[r][c] == 0:
                return False
        return True

    def line_of_sight(self, x0, y0, x1, y1):
        """
        Bresenham's algorithm: yields all (col,row) between two cells.
        """
        cells = []
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        x, y = x0, y0
        sx = 1 if x1 > x0 else -1
        sy = 1 if y1 > y0 else -1
        if dx > dy:
            err = dx / 2
            while x != x1:
                cells.append((x, y))
                err -= dy
                if err < 0:
                    y += sy
                    err += dx
                x += sx
        else:
            err = dy / 2
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
        """
        A single-step move toward target_pixel using BFS path.
        """
        start = self.pixel_to_grid(self.position)
        goal = self.pixel_to_grid(target_pixel)
        if start == goal:
            return
        path = self.find_path_between(start, goal)
        if len(path) < 2:
            return
        next_cell = path[1]
        next_px = self.grid_to_pixel(next_cell)
        dx = next_px[0] - self.position[0]
        dy = next_px[1] - self.position[1]
        dist = math.hypot(dx, dy)
        if dist < self.patrol_speed:
            self.position = next_px
        else:
            self.position = (
                self.position[0] + dx / dist * self.patrol_speed,
                self.position[1] + dy / dist * self.patrol_speed
            )
        self.update_animation(dx, dy)

    def find_path_between(self, start, goal):
        """
        BFS from start to goal on walkable cells.
        Returns list of cells from start to goal inclusive.
        """
        if not self.is_walkable(start) or not self.is_walkable(goal):
            return []
        queue = deque([start])
        came_from = {start: None}
        visited = {start}
        while queue:
            cur = queue.popleft()
            if cur == goal:
                break
            for nb in self.get_neighbors(cur):
                if nb not in visited and self.is_walkable(nb):
                    visited.add(nb)
                    came_from[nb] = cur
                    queue.append(nb)
        if goal not in came_from:
            return []
        path = []
        node = goal
        while node is not None:
            path.append(node)
            node = came_from[node]
        return list(reversed(path))

    def find_nearest_walkable(self):
        """
        BFS outward until a walkable cell is found.
        """
        start = self.pixel_to_grid(self.position)
        if self.is_walkable(start):
            return start
        queue = deque([start])
        visited = {start}
        while queue:
            c = queue.popleft()
            for nb in self.get_neighbors(c):
                if nb not in visited:
                    visited.add(nb)
                    if self.is_walkable(nb):
                        return nb
                    queue.append(nb)
        return None

    def move_patrol_area(self):
        """
        Follow the precomputed patrol route in complete_patrol_route.
        """
        if not self.complete_patrol_route:
            return
        if self.patrol_index >= len(self.complete_patrol_route):
            self.patrol_index = 0
        target_cell = self.complete_patrol_route[self.patrol_index]
        start_cell = self.pixel_to_grid(self.position)
        path = self.find_path_between(start_cell, target_cell)
        if len(path) >= 2:
            next_cell = path[1]
        else:
            next_cell = target_cell
        next_px = self.grid_to_pixel(next_cell)
        dx = next_px[0] - self.position[0]
        dy = next_px[1] - self.position[1]
        dist = math.hypot(dx, dy)
        if dist < self.patrol_speed:
            self.position = next_px
            self.patrol_index = (self.patrol_index + 1) % len(self.complete_patrol_route)
        else:
            self.position = (
                self.position[0] + dx / dist * self.patrol_speed,
                self.position[1] + dy / dist * self.patrol_speed
            )
        self.update_animation(dx, dy)

    def move_alert(self, player_pos):
        if not self.can_see_player(player_pos):
            self.state = "patrol"
            self.move_patrol_area()
            return

        now = time.time()
        if not self.path or now - self.last_update_time >= self.update_interval:
            self.find_path(player_pos)
            self.last_update_time = now

        if not self.path:
            return

        next_cell = self.path[0]
        target_px = self.grid_to_pixel(next_cell)
        dx = target_px[0] - self.position[0]
        dy = target_px[1] - self.position[1]
        dist = math.hypot(dx, dy)
        if dist > 0:
            dx /= dist; dy /= dist

        new_pos = (
            self.position[0] + dx * self.alert_speed,
            self.position[1] + dy * self.alert_speed
        )
        if not self.check_collision(new_pos):
            self.position = new_pos
            # advance animation/frame as you already have it
            ...
            # if we reached this cell, pop it
            if math.hypot(target_px[0] - self.position[0],
                        target_px[1] - self.position[1]) < self.alert_speed:
                self.path.pop(0)
        else:
            # bump into obstacle, force a replan next call
            self.path = []

        # 5) Update sprite direction/frame
        self.update_animation(dx, dy)

    def find_path(self, player_pos):
        """
        BFS from current position to player's cell, store in self.path.
        """
        start = self.pixel_to_grid(self.position)
        goal = self.pixel_to_grid(player_pos)
        self.path = []
        if not self.is_walkable(start) or not self.is_walkable(goal):
            return
        queue = deque([start])
        came_from = {start: None}
        visited = {start}
        while queue:
            cur = queue.popleft()
            if cur == goal:
                break
            for nb in self.get_neighbors(cur):
                if nb not in visited and self.is_walkable(nb):
                    visited.add(nb)
                    came_from[nb] = cur
                    queue.append(nb)
        if goal not in came_from:
            return
        # reconstruct
        rev = []
        node = goal
        while node is not None:
            rev.append(node)
            node = came_from[node]
        self.path = list(reversed(rev))

    def update_animation(self, dx, dy):
        """
        Set self.direction and pick the correct frame/image.
        """
        # determine direction
        if abs(dx) > abs(dy):
            self.direction = 'right' if dx > 0 else 'left'
        else:
            self.direction = 'down' if dy > 0 else 'up'

        # advance frame timer
        self.frame_timer += 1
        if self.frame_timer >= self.frames_per_step:
            self.frame_timer = 0
            self.current_frame = (self.current_frame + 1) % 2

        # pick correct image set
        if self.state == "alert":
            self.current_image = self.alert_images[self.direction][self.current_frame]
        else:
            self.current_image = self.images[self.direction][self.current_frame]

    def get_neighbors(self, cell):
        c, r = cell
        nbrs = [(c+1,r),(c-1,r),(c,r+1),(c,r-1)]
        return [(x,y) for x,y in nbrs if 0 <= x < self.GRID_COLS and 0 <= y < self.GRID_ROWS]

    def check_collision(self, x, y=None):
        """
        Return True if (x,y) is colliding with a wall or out of bounds.
        Accepts either check_collision(x, y) or check_collision((x,y)).
        """
        # unpack if called with a tuple
        if y is None:
            x, y = x

        # compute grid cell
        col, row = self.pixel_to_grid((x, y))
        # out of bounds?
        if not self.in_bounds((col, row)):
            return True
        # wall?
        return (self.matrix[row][col] == 0)

    def is_walkable(self, cell):
        """
        Walkable if floor (1), player start (2), open door (>=5), or overlay markers (>=5).
        """
        c, r = cell
        if not self.in_bounds(cell):
            return False
        val = self.matrix[r][c]
        return (val == 1 or val == 2 or val >= 5)

    def in_bounds(self, cell):
        c, r = cell
        return 0 <= c < self.GRID_COLS and 0 <= r < self.GRID_ROWS

    def pixel_to_grid(self, pixel_pos):
        x, y = pixel_pos
        return (int(x // self.PIXEL_ONE_X), int(y // self.PIXEL_ONE_Y))

    def grid_to_pixel(self, cell):
        c, r = cell
        return (
            c * self.PIXEL_ONE_X + self.PIXEL_ONE_X / 2,
            r * self.PIXEL_ONE_Y + self.PIXEL_ONE_Y / 2
        )

    def get_position(self):
        return self.position
