import pygame
import math
from constants.matrix_sizes import SIZE_X, SIZE_Y, border_tuples, player_start_x, player_start_y, matrix, GRID_COLS, GRID_ROWS, PIXEL_ONE_X, PIXEL_ONE_Y
from Player import Player
from Enemy import Enemy

# --- Helper Functions for Patrol Route Generation ---

def get_neighbors(cell):
    col, row = cell
    # Fixed neighbor order: right, down, left, up
    return [(col + 1, row), (col, row + 1), (col - 1, row), (col, row - 1)]

def get_region(patrolling_area):
    """
    Given a patrolling_area as (x_min, y_min, x_max, y_max) in pixels,
    return a set of walkable grid cells (col, row) based on the global matrix.
    Walkable cells are those where matrix[row][col] == 1.
    """
    x_min, y_min, x_max, y_max = patrolling_area
    col_min = int(x_min // PIXEL_ONE_X)
    row_min = int(y_min // PIXEL_ONE_Y)
    col_max = int(x_max // PIXEL_ONE_X)
    row_max = int(y_max // PIXEL_ONE_Y)
    region = set()
    for row in range(row_min, row_max):
        for col in range(col_min, col_max):
            if 0 <= col < GRID_COLS and 0 <= row < GRID_ROWS:
                if matrix[row][col] == 1:
                    region.add((col, row))
    return region

def choose_starting_points(region, guard_count):
    """
    Choose guard_count starting cells from region.
    One simple strategy is to pick one random cell for each guard.
    """
    region_list = list(region)
    import random
    random.shuffle(region_list)
    return region_list[:guard_count]

def partition_region_among_guards(region, starting_points):
    """
    Partition the region among guards using multi-source BFS.
    Each cell is assigned to the nearest starting point.
    Returns a list of sets (one per guard) representing the partition.
    """
    guard_count = len(starting_points)
    partitions = [set() for _ in range(guard_count)]
    assignments = {}  # cell -> guard index
    frontier = []
    for i, cell in enumerate(starting_points):
        frontier.append((cell, i))
        assignments[cell] = i

    while frontier:
        current, guard_idx = frontier.pop(0)
        partitions[guard_idx].add(current)
        for neighbor in get_neighbors(current):
            if neighbor in region and neighbor not in assignments:
                assignments[neighbor] = guard_idx
                frontier.append((neighbor, guard_idx))
    return partitions

def dfs_euler(start, region):
    """
    Perform DFS (Euler tour) starting from 'start' over the given region.
    When backtracking, append the current cell so that the route is continuous.
    """
    route = []
    visited = set()
    def dfs(cell):
        visited.add(cell)
        route.append(cell)
        for neighbor in get_neighbors(cell):
            if neighbor in region and neighbor not in visited:
                dfs(neighbor)
                route.append(cell)  # backtracking step
    dfs(start)
    if route[-1] != start:
        route.append(start)
    return route

def optimize_patrol_route(route):
    """
    Remove redundant backtracking steps.
    For instance, remove consecutive duplicates and simple A, B, A patterns.
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

def generate_guard_patrol_routes(region, guard_count, difficulty):
    """
    Partition the region among guard_count guards and generate a patrol route for each.
    If difficulty is high, the routes will be optimized.
    Returns a list of patrol routes (each a list of grid cells), one per guard.
    """
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
        self.guard_count = 2  # Number of guards
        self.difficulty = 3   # 1: easy, 2: medium, 3: hard
        self.enemies = []
        # Define overall patrol area (entire level)
        self.patrolling_area = (0, 0, SIZE_X, SIZE_Y)

    def draw_map(self):
        crate_image = pygame.image.load("../Assets/walls.png").convert_alpha()
        for (x_start, x_end), (y_start, y_end) in border_tuples:
            width = x_end - x_start
            height = y_end - y_start
            rect = pygame.Rect(math.floor(x_start), math.floor(y_start), width, height)
            scaled_crate = pygame.transform.scale(crate_image, (int(width), int(height)))
            self.screen.blit(scaled_crate, rect)

    def level_changes(self):
        """
        Partition the overall patrol area among guards.
        Generate patrol routes for each guard using dynamic partitioning.
        """
        region = get_region(self.patrolling_area)
        patrol_routes = generate_guard_patrol_routes(region, self.guard_count, self.difficulty)
        for i, route in enumerate(patrol_routes):
            if not route:
                continue
            spawn_cell = route[0]
            spawn_x = spawn_cell[0] * PIXEL_ONE_X + PIXEL_ONE_X / 2
            spawn_y = spawn_cell[1] * PIXEL_ONE_Y + PIXEL_ONE_Y / 2
            print(f"Guard {i} patrol route:", route)
            self.enemies.append(Enemy((spawn_x, spawn_y), route, move_speed=3, update_interval=1))

    def start_screen(self):
        """
        Display a start screen until the user presses any key or clicks the mouse.
        """
        waiting = True
        font = pygame.font.SysFont(None, 48)
        text_surface = font.render("Press any key to start", True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(SIZE_X // 2, SIZE_Y // 2))
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                elif event.type == pygame.KEYDOWN or event.type == pygame.MOUSEBUTTONDOWN:
                    waiting = False
            self.screen.blit(self.background, (0, 0))
            self.screen.blit(text_surface, text_rect)
            pygame.display.flip()
            self.clock.tick(60)

    def game_loop(self):
        self.start_screen()  # Wait for user to start the game.
        running = True
        self.level_changes()
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
