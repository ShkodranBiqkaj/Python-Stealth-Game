import pygame
import random

# Global maze settings with default values.
maze_difficulty = "hard"  # "easy" (with loops) or "hard" (perfect maze)
BASE_ROWS = 10
BASE_COLS = 10
enemy_count = 2

def maze_options_screen(screen, clock):
    """
    Displays an options screen for maze and enemy settings.
    Controls:
      - Maze Difficulty: Press 1 for Easy, 2 for Hard.
      - Maze Rows: Up arrow to increase, Down arrow to decrease.
      - Maze Columns: Right arrow to increase, Left arrow to decrease.
      - Enemy Count: Press E to increase, Q to decrease.
      - Press ENTER to confirm choices.
    Updates global variables accordingly.
    """
    global maze_difficulty, BASE_ROWS, BASE_COLS, enemy_count
    font = pygame.font.SysFont(None, 36)
    choosing = True
    while choosing:
        screen.fill((0, 0, 0))
        option_texts = [
            f"Maze Difficulty: {maze_difficulty} (Press 1 for Easy, 2 for Hard)",
            f"Maze Rows: {BASE_ROWS} (Up/Down arrows to adjust)",
            f"Maze Columns: {BASE_COLS} (Right/Left arrows to adjust)",
            f"Enemy Count: {enemy_count} (Press E to increase, Q to decrease)",
            "Press ENTER to confirm"
        ]
        for i, text in enumerate(option_texts):
            text_surface = font.render(text, True, (255, 255, 255))
            screen.blit(text_surface, (50, 50 + i * 40))
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    maze_difficulty = "easy"
                elif event.key == pygame.K_2:
                    maze_difficulty = "hard"
                elif event.key == pygame.K_UP:
                    BASE_ROWS += 1
                elif event.key == pygame.K_DOWN:
                    BASE_ROWS = max(3, BASE_ROWS - 1)
                elif event.key == pygame.K_RIGHT:
                    BASE_COLS += 1
                elif event.key == pygame.K_LEFT:
                    BASE_COLS = max(3, BASE_COLS - 1)
                elif event.key == pygame.K_e:
                    enemy_count += 1
                elif event.key == pygame.K_q:
                    enemy_count = max(1, enemy_count - 1)
                elif event.key == pygame.K_RETURN:
                    choosing = False
        clock.tick(30)
    return maze_difficulty, BASE_ROWS, BASE_COLS, enemy_count

def create_maze_map(base_rows, base_cols):
    """
    Creates a perfect maze using the two-layer approach:
      - Logical maze size: base_rows x base_cols
      - Actual matrix size: (2*base_rows + 1) x (2*base_cols + 1)
    In a perfect maze, there is exactly one solution.
    """
    rows = 2 * base_rows + 1
    cols = 2 * base_cols + 1
    maze = [[0 for _ in range(cols)] for _ in range(rows)]
    
    def cell_to_matrix(r, c):
        return 2 * r + 1, 2 * c + 1
    
    visited = [[False] * base_cols for _ in range(base_rows)]
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    
    def in_bounds(r, c):
        return 0 <= r < base_rows and 0 <= c < base_cols
    
    def carve_dfs(r, c):
        visited[r][c] = True
        mr, mc = cell_to_matrix(r, c)
        maze[mr][mc] = 1  # Carve the cell center.
        random.shuffle(directions)
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if in_bounds(nr, nc) and not visited[nr][nc]:
                maze[mr + dr][mc + dc] = 1  # Carve the wall between cells.
                carve_dfs(nr, nc)
    
    start_r = random.randint(0, base_rows - 1)
    start_c = random.randint(0, base_cols - 1)
    carve_dfs(start_r, start_c)
    return maze

def add_loops_to_maze(maze, extra_loop_prob):
    """
    Iterates over interior wall cells and, if the wall lies between two open cells horizontally or vertically,
    removes it with probability extra_loop_prob. This adds extra passages (loops) for multiple solutions.
    """
    rows = len(maze)
    cols = len(maze[0])
    for r in range(1, rows - 1):
        for c in range(1, cols - 1):
            if maze[r][c] == 0:
                if maze[r][c - 1] == 1 and maze[r][c + 1] == 1:
                    if random.random() < extra_loop_prob:
                        maze[r][c] = 1
                if maze[r - 1][c] == 1 and maze[r + 1][c] == 1:
                    if random.random() < extra_loop_prob:
                        maze[r][c] = 1
    return maze

def generate_maze(base_rows, base_cols, difficulty):
    """
    Generates the maze using the given logical dimensions and difficulty.
    If difficulty is "easy", extra loops are added to produce multiple solutions.
    """
    maze = create_maze_map(base_rows, base_cols)
    if difficulty == "easy":
        maze = add_loops_to_maze(maze, 0.3)
    return maze

def distribute_hidden_rooms(maze, num_hidden_per_quadrant=4):
    """
    Divides the maze into 4 quadrants and, in each quadrant, converts up to 
    num_hidden_per_quadrant wall cells (value 0) that are adjacent to exactly one 
    open cell (value 1) into hidden spots (value 3). It also ensures that hidden spots 
    are not directly adjacent to one another.
    
    This way the hidden spots serve as bonus rooms (or dead ends) without adding extra 
    connectivity that would let the player bypass maze sections.
    """
    rows = len(maze)
    cols = len(maze[0])
    # Define quadrant boundaries.
    quadrants = [
        (0, rows // 2, 0, cols // 2),            # Top-left
        (0, rows // 2, cols // 2, cols),           # Top-right
        (rows // 2, rows, 0, cols // 2),           # Bottom-left
        (rows // 2, rows, cols // 2, cols)           # Bottom-right
    ]
    for (r_start, r_end, c_start, c_end) in quadrants:
        candidates = []
        for r in range(r_start, r_end):
            for c in range(c_start, c_end):
                if maze[r][c] == 0:
                    # Count how many neighbors are open.
                    open_neighbors = 0
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        rr, cc = r + dr, c + dc
                        if 0 <= rr < rows and 0 <= cc < cols:
                            if maze[rr][cc] == 1:
                                open_neighbors += 1
                    # Only consider wall cells with exactly one open neighbor.
                    if open_neighbors == 1:
                        candidates.append((r, c))
        random.shuffle(candidates)
        hidden_count = 0
        for (r, c) in candidates:
            if hidden_count >= num_hidden_per_quadrant:
                break
            # Ensure no adjacent cell is already a hidden spot.
            adjacent_hidden = False
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                rr, cc = r + dr, c + dc
                if 0 <= rr < rows and 0 <= cc < cols:
                    if maze[rr][cc] == 3:
                        adjacent_hidden = True
                        break
            if not adjacent_hidden:
                maze[r][c] = 3
                hidden_count += 1
    return maze

# def unlock_hidden_room(maze):
#     print("Unlocked")
#     rows = len(maze)
#     cols = len(maze[0])
#     for r in range(rows):
#         for c in range(cols):
#             if maze[r][c] == 0:
#                 for (dr, dc) in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
#                     nr, nc = r + dr, c + dc
#                     if 0 <= nr < rows and 0 <= nc < cols:
#                         if maze[nr][nc] == 2:
#                             maze[r][c] = 1
#                             return

# --- Pygame Setup and Maze Generation ---
pygame.init()
SIZE_X = 1000
SIZE_Y = 750

# Create a temporary screen and clock for the options menu.
screen = pygame.display.set_mode((SIZE_X, SIZE_Y))
clock = pygame.time.Clock()

# Display the options menu and record player's choices.
maze_difficulty, BASE_ROWS, BASE_COLS, enemy_count = maze_options_screen(screen, clock)

# Generate the maze based on the chosen settings.
matrix = generate_maze(BASE_ROWS, BASE_COLS, maze_difficulty)
# Distribute hidden spots: in each quadrant, place 4 hidden rooms.
matrix = distribute_hidden_rooms(matrix, num_hidden_per_quadrant=4)

# Compute grid and pixel dimensions.
GRID_ROWS = len(matrix)
GRID_COLS = len(matrix[0])
PIXEL_ONE_X = SIZE_X / GRID_COLS
PIXEL_ONE_Y = SIZE_Y / GRID_ROWS

# Instead of storing just the rectangle, store (row, col, x_start, y_start, width, height)
border_tuples = []
for row in range(GRID_ROWS):
    for col in range(GRID_COLS):
        if matrix[row][col] == 0 or matrix[row][col] == 3:
            x_start = col * PIXEL_ONE_X
            y_start = row * PIXEL_ONE_Y
            width = PIXEL_ONE_X
            height = PIXEL_ONE_Y
            border_tuples.append((row, col, x_start, y_start, width, height))

def find_start():
    for i in range(1, GRID_ROWS):
        for j in range(GRID_COLS):
            if matrix[GRID_ROWS - i][j] == 1:
                return GRID_ROWS - i, j
    return 0, 0

player_start_y, player_start_x = find_start()
print(player_start_x, player_start_y)
player_start_x = player_start_x * PIXEL_ONE_X
player_start_y = player_start_y * PIXEL_ONE_Y
