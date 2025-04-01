import pygame
import random

def insert_u_shape_with_connectivity(maze, top_left_row, top_left_col, pattern):
    """
    Inserts a U-shaped pattern into the maze at the specified top-left position.
    Then, it forces connectivity by ensuring a predetermined connecting cell is open.
    
    Parameters:
      maze: 2D list representing the maze.
      top_left_row, top_left_col: the top-left coordinates where the pattern will be inserted.
      pattern: a 2D list representing the desired U-shape pattern.
    """
    rows = len(pattern)
    cols = len(pattern[0])
    # Insert the pattern into the maze.
    for i in range(rows):
        for j in range(cols):
            maze[top_left_row + i][top_left_col + j] = pattern[i][j]
    
    # Force connectivity:
    # For example, force the bottom middle cell to be walkable.
    bottom_middle_row = top_left_row + rows - 1
    bottom_middle_col = top_left_col + cols // 2
    maze[bottom_middle_row][bottom_middle_col] = 1

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

def unlock_hidden_room(maze):
    # Suppose we stored the blocked cell as (blocked_r, blocked_c)
    # For simplicity, let's just search for any cell that is 0 but
    # neighbors a '2' cell. We turn it into 1.
    print("Unlocked")
    rows = len(maze)
    cols = len(maze[0])
    for r in range(rows):
        for c in range(cols):
            if maze[r][c] == 0:
                # Check if it neighbors a 2
                for (dr, dc) in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < rows and 0 <= nc < cols:
                        if maze[nr][nc] == 2:
                            maze[r][c] = 1
                            return  # done, we unlocked it

# --- Pygame Setup ---
pygame.init()

SIZE_X = 1000
SIZE_Y = 750

GRID_ROWS = 10
GRID_COLS = 10

PIXEL_ONE_X = SIZE_X / GRID_COLS
PIXEL_ONE_Y = SIZE_Y / GRID_ROWS

# Generate the maze map.
matrix = create_maze_map(GRID_ROWS, GRID_COLS)

# Insert a U-shape pattern into the maze.
# Choose a top-left position (make sure the area fits inside the maze).
# For example, here we insert it at row 2, column 2.
u_shape = [
    [1, 0, 1],
    [1, 1, 0],
    [1, 0, 1]
]
insert_u_shape_with_connectivity(matrix, 2, 2, u_shape)

# Create border_tuples for each blocked cell.
border_tuples = []
for row in range(GRID_ROWS):
    for col in range(GRID_COLS):
        if matrix[row][col] == 0:
            x_start = col * PIXEL_ONE_X
            x_end   = x_start + PIXEL_ONE_X
            y_start = row * PIXEL_ONE_Y
            y_end   = y_start + PIXEL_ONE_Y
            border_tuples.append(((x_start, x_end), (y_start, y_end)))

def find_start():
    for i in range(1, len(matrix)):
        for j in range(len(matrix[0])):
            if matrix[len(matrix)-i][j] == 1:
                return len(matrix)-i, j
    return 0, 0

player_start_y, player_start_x = find_start()
print(player_start_x, player_start_y)
player_start_x = player_start_x * PIXEL_ONE_X
player_start_y = player_start_y * PIXEL_ONE_Y

# Now border_tuples can be used in your game loop to draw crates or obstacles.
