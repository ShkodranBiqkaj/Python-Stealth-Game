import pygame
import random

def create_maze_map(rows, cols):
    """
    Creates a maze-like map using DFS where:
      0 = blocked
      1 = walkable
    Ensures there's a single connected path that visits many cells,
    but doesn't automatically open the entire grid.
    """
    maze = [[0 for _ in range(cols)] for _ in range(rows)]
    stack = []

    # Start from a random cell
    r = random.randint(0, rows - 1)
    c = random.randint(0, cols - 1)
    maze[r][c] = 1
    stack.append((r, c))

    while stack:
        r, c = stack[-1]

        # Potential directions
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        random.shuffle(directions)

        carved_next = False
        for (dr, dc) in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                if maze[nr][nc] == 0:
                    # Check how many neighbors of (nr, nc) are carved
                    carved_neighbors = 0
                    for (dr2, dc2) in [(-1,0),(1,0),(0,-1),(0,1)]:
                        rr, cc = nr + dr2, nc + dc2
                        if 0 <= rr < rows and 0 <= cc < cols:
                            if maze[rr][cc] == 1:
                                carved_neighbors += 1

                    # Only carve if it has exactly 1 carved neighbor
                    if carved_neighbors == 1:
                        maze[nr][nc] = 1
                        stack.append((nr, nc))
                        carved_next = True
                        break

        if not carved_next:
            stack.pop()

    return maze

# --- Pygame Setup ---
pygame.init()

SIZE_X = 1000
SIZE_Y = 750

GRID_ROWS = 10
GRID_COLS = 10

PIXEL_ONE_X = SIZE_X / GRID_COLS
PIXEL_ONE_Y = SIZE_Y / GRID_ROWS

# Generate a 5x5 "maze" map
# 1 = walkable, 0 = blocked
matrix = create_maze_map(GRID_ROWS, GRID_COLS)

# Create border_tuples for each blocked cell
border_tuples = []
for row in range(GRID_ROWS):
    for col in range(GRID_COLS):
        if matrix[row][col] == 0:
            x_start = col * PIXEL_ONE_X
            x_end   = x_start + PIXEL_ONE_X
            y_start = row * PIXEL_ONE_Y
            y_end   = y_start + PIXEL_ONE_Y
            border_tuples.append(((x_start, x_end), (y_start, y_end)))

# Now you can use border_tuples to draw crates or obstacles in your game loop.
