import pygame
import math
import random
from collections import deque
from constants.matrix_sizes import SIZE_X, SIZE_Y, border_tuples, player_start_x, player_start_y, matrix, GRID_COLS, GRID_ROWS, PIXEL_ONE_X, PIXEL_ONE_Y, enemy_count, maze_difficulty
from Player import Player
from Enemy import Enemy

# --- Helper Functions for Patrol Route Generation ---

def get_neighbors(cell):
    col, row = cell
    return [(col + 1, row), (col, row + 1), (col - 1, row), (col, row - 1)]

def get_region(patrolling_area):
    x_min, y_min, x_max, y_max = patrolling_area
    col_min = int(x_min // PIXEL_ONE_X)
    row_min = int(y_min // PIXEL_ONE_Y)
    col_max = int(x_max // PIXEL_ONE_X)
    row_max = int(y_max // PIXEL_ONE_Y)
    region = set()
    for row in range(row_min, row_max):
        for col in range(col_min, col_max):
            if 0 <= col < GRID_COLS and 0 <= row < GRID_ROWS:
                # Include cells with 1 (open) or 2 (player)
                if matrix[row][col] in (1, 2):
                    region.add((col, row))
    return region

def choose_starting_points(region, guard_count):
    """
    Choose 'guard_count' starting points from the given region.
    Pick one random point and then add additional points one by one, ensuring
    they are spread out. Even if some overlap, that's acceptable.
    """
    region_list = list(region)
    import random
    chosen = []
    if not region_list:
        return chosen
    # Pick one random starting point.
    chosen.append(random.choice(region_list))
    threshold = max(GRID_COLS, GRID_ROWS) // 4
    while len(chosen) < guard_count and region_list:
        candidate = random.choice(region_list)
        if all(abs(candidate[0] - p[0]) + abs(candidate[1] - p[1]) >= threshold for p in chosen):
            chosen.append(candidate)
        else:
            if random.random() < 0.3:
                chosen.append(candidate)
        region_list.remove(candidate)
    return chosen

def partition_region_among_guards(region, starting_points):
    from collections import deque
    guard_count = len(starting_points)
    partitions = [set() for _ in range(guard_count)]
    assignments = {}
    frontier = deque()
    for i, cell in enumerate(starting_points):
        frontier.append((cell, i))
        assignments[cell] = i
    while frontier:
        current, guard_idx = frontier.popleft()
        partitions[guard_idx].add(current)
        for neighbor in get_neighbors(current):
            if neighbor in region and neighbor not in assignments:
                assignments[neighbor] = guard_idx
                frontier.append((neighbor, guard_idx))
    for i in range(guard_count):
        if not partitions[i]:
            partitions[i] = set(region)
    return partitions

def dfs_euler(start, region):
    """
    Generates a route through the region using DFS.
    The route is allowed to end at a dead end (it is not forced to loop back).
    """
    route = []
    visited = set()
    def dfs(cell):
        visited.add(cell)
        route.append(cell)
        for neighbor in get_neighbors(cell):
            if neighbor in region and neighbor not in visited:
                dfs(neighbor)
                route.append(cell)
    dfs(start)
    return route

def optimize_patrol_route(route):
    """
    Remove redundant moves from a route.
    For example, A -> B -> C -> B -> D becomes A -> B -> D.
    """
    if not route:
        return route
    optimized = []
    for cell in route:
        if not optimized or optimized[-1] != cell:
            optimized.append(cell)
    i = 0
    while i < len(optimized) - 2:
        if optimized[i] == optimized[i+2]:
            del optimized[i+1]
        else:
            i += 1
    return optimized

def bfs_path(start, goal, region):
    """
    Uses BFS to find a path from start to goal through cells in 'region'.
    Returns a list of cells [start, ..., goal] if found, else [].
    """
    from collections import deque
    queue = deque([start])
    came_from = {start: None}
    visited = {start}
    while queue:
        current = queue.popleft()
        if current == goal:
            path = []
            node = goal
            while node is not None:
                path.append(node)
                node = came_from[node]
            path.reverse()
            return path
        for nb in get_neighbors(current):
            if nb in region and nb not in visited:
                visited.add(nb)
                came_from[nb] = current
                queue.append(nb)
    return []

def join_dead_end_routes(routes, region):
    """
    For any route ending in a dead end (with no new adjacent cells),
    attempt to connect it to another route so the enemy doesn't oscillate.
    """
    for i, route in enumerate(routes):
        if not route:
            continue
        last_cell = route[-1]
        free_neighbors = [n for n in get_neighbors(last_cell) if n in region and n not in route]
        if not free_neighbors:
            for j, other_route in enumerate(routes):
                if i == j or not other_route:
                    continue
                for cell in other_route:
                    if cell in get_neighbors(last_cell):
                        path = bfs_path(last_cell, cell, region)
                        if path and len(path) >= 2:
                            extension = path[1:]  # skip duplicate
                            route.extend(extension)
                            break
                else:
                    continue
                break
    return routes

def generate_guard_patrol_routes(region, guard_count, difficulty):
    starting_points = choose_starting_points(region, guard_count)
    partitions = partition_region_among_guards(region, starting_points)
    patrol_routes = []
    for i in range(guard_count):
        part = partitions[i]
        if starting_points[i] in part:
            route = dfs_euler(starting_points[i], part)
        else:
            route = dfs_euler(next(iter(part)), part)
        if difficulty >= 3:
            route = optimize_patrol_route(route)
        patrol_routes.append(route)
    patrol_routes = join_dead_end_routes(patrol_routes, region)
    return patrol_routes

# --- Game Class ---

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SIZE_X, SIZE_Y))
        pygame.display.set_caption("Stealth Game - Dynamic Guard Patrols")
        self.clock = pygame.time.Clock()
        self.background = pygame.image.load("../Assets/background.jpg").convert()
        self.player = Player(player_start_x, player_start_y)
        self.guard_count = enemy_count  # Use enemy_count from options
        self.difficulty = 1 if maze_difficulty == "easy" else 3
        self.enemies = []
        self.patrolling_area = (0, 0, SIZE_X, SIZE_Y)
        # Default setting for showing enemy patrol pattern overlay.
        self.show_route_pattern = True

    def options_screen(self):
        """
        Displays a front-screen options menu.
        Press 'P' to toggle whether the enemy patrol pattern (colored overlay)
        is displayed beneath the enemies.
        Press ENTER to start the game.
        """
        font = pygame.font.SysFont(None, 36)
        show_overlay = True
        while True:
            self.screen.fill((0, 0, 0))
            option_texts = [
                f"Show Enemy Patrol Pattern Overlay: {'ON' if show_overlay else 'OFF'} (Press P to toggle)",
                "Press ENTER to start the game."
            ]
            for i, text in enumerate(option_texts):
                text_surface = font.render(text, True, (255, 255, 255))
                self.screen.blit(text_surface, (50, 50 + i * 40))
            pygame.display.flip()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_p:
                        show_overlay = not show_overlay
                    elif event.key == pygame.K_RETURN:
                        self.show_route_pattern = show_overlay
                        return

    def pixel_to_grid(self, pixel_pos):
        x, y = pixel_pos
        col = int(x // PIXEL_ONE_X)
        row = int(y // PIXEL_ONE_Y)
        return col, row

    def draw_map(self):
        crate_image = pygame.image.load("../Assets/walls.png").convert_alpha()
        hidden_image = pygame.image.load("../Assets/hidden_room.png").convert_alpha()
        for (row, col, x_start, y_start, width, height) in border_tuples:
            rect = pygame.Rect(math.floor(x_start), math.floor(y_start), width, height)
            image = hidden_image if matrix[row][col] == 3 else crate_image
            scaled_image = pygame.transform.scale(image, (int(width), int(height)))
            self.screen.blit(scaled_image, rect)
        # Draw the patrol-route overlay only if enabled.
        if self.show_route_pattern:
            route_color_dict = {}
            for enemy in self.enemies:
                route_color_dict[enemy.route_marker] = enemy.route_color
            for r in range(GRID_ROWS):
                for c in range(GRID_COLS):
                    if matrix[r][c] >= 5:
                        color = route_color_dict.get(matrix[r][c], (0, 0, 0, 128))
                        x_start = c * PIXEL_ONE_X
                        y_start = r * PIXEL_ONE_Y
                        overlay = pygame.Surface((int(PIXEL_ONE_X), int(PIXEL_ONE_Y)), pygame.SRCALPHA)
                        overlay.fill(color)
                        self.screen.blit(overlay, (x_start, y_start))

    def level_changes(self):
        region = get_region(self.patrolling_area)
        patrol_routes = generate_guard_patrol_routes(region, self.guard_count, self.difficulty)
        route_colors = [
            (0, 0, 255, 128),
            (255, 0, 0, 128),
            (0, 255, 0, 128),
            (255, 255, 0, 128),
            (255, 0, 255, 128),
            (0, 255, 255, 128)
        ]
        for i, route in enumerate(patrol_routes):
            if not route:
                continue
            spawn_cell = route[0]
            spawn_x = spawn_cell[0] * PIXEL_ONE_X + PIXEL_ONE_X / 2
            spawn_y = spawn_cell[1] * PIXEL_ONE_Y + PIXEL_ONE_Y / 2
            print(f"Guard {i} patrol route:", route)
            enemy = Enemy((spawn_x, spawn_y), route, move_speed=3, update_interval=1)
            enemy.route_marker = 5 + i
            enemy.route_color = route_colors[i % len(route_colors)]
            self.enemies.append(enemy)

    def game_loop(self):
        # Show the front-screen options menu.
        self.options_screen()
        # Set up level changes (patrol routes and enemies).
        self.level_changes()
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
            self.screen.blit(self.background, (0, 0))
            self.draw_map()
            self.player.move()
            player_pos = self.player.get_position()
            for enemy in self.enemies:
                enemy.update(player_pos)
            self.player.draw(self.screen)
            for enemy in self.enemies:
                enemy.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(60)
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.game_loop()
