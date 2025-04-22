import pygame
import random
from collections import deque

# ── Global maze settings with default values. ─────────────────────────
maze_difficulty = "hard"  # "easy" (with loops) or "hard" (perfect maze)
BASE_ROWS       = 10
BASE_COLS       = 10
enemy_count     = 2

# ── Tile codes ─────────────────────────────────────────────────────────
T_WALL    = 0  # crate / wall
T_FLOOR   = 1  # open floor
T_PLAYER  = 2  # player start
T_HIDDEN  = 3  # hidden bonus room
T_KEY     = 4  # the key
T_DOOR_C  = 5  # closed door
T_DOOR_O  = 6  # opened door

# ── Options screen ────────────────────────────────────────────────────
def maze_options_screen(screen, clock):
    """
    Let player pick difficulty, rows, cols, enemy count.
    Controls:
      1/2: easy/hard
      ↑/↓: rows up/down
      →/←: cols up/down
      E/Q: enemy count +/-
      ENTER: confirm
    """
    global maze_difficulty, BASE_ROWS, BASE_COLS, enemy_count
    font = pygame.font.SysFont(None, 36)
    choosing = True
    while choosing:
        screen.fill((0, 0, 0))
        opts = [
            f"Maze Difficulty: {maze_difficulty} (1=Easy, 2=Hard)",
            f"Maze Rows:       {BASE_ROWS} (Up/Down)",
            f"Maze Cols:       {BASE_COLS} (Right/Left)",
            f"Enemy Count:     {enemy_count} (E/Q)",
            "Press ENTER to start"
        ]
        for i, t in enumerate(opts):
            screen.blit(font.render(t, True, (255,255,255)), (50, 50 + i*40))
        pygame.display.flip()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_1: maze_difficulty = "easy"
                if e.key == pygame.K_2: maze_difficulty = "hard"
                if e.key == pygame.K_UP:    BASE_ROWS += 1
                if e.key == pygame.K_DOWN:  BASE_ROWS = max(3, BASE_ROWS-1)
                if e.key == pygame.K_RIGHT: BASE_COLS += 1
                if e.key == pygame.K_LEFT:  BASE_COLS = max(3, BASE_COLS-1)
                if e.key == pygame.K_e:     enemy_count += 1
                if e.key == pygame.K_q:     enemy_count = max(1, enemy_count-1)
                if e.key == pygame.K_RETURN:
                    choosing = False
        clock.tick(30)
    return maze_difficulty, BASE_ROWS, BASE_COLS, enemy_count

# ── Perfect‐maze carving (recursive DFS) ───────────────────────────────
def create_maze_map(base_rows, base_cols):
    rows, cols = 2*base_rows+1, 2*base_cols+1
    maze = [[T_WALL for _ in range(cols)] for _ in range(rows)]
    visited = [[False]*base_cols for _ in range(base_rows)]
    dirs = [(-1,0),(1,0),(0,-1),(0,1)]

    def cell_to_mat(r,c): return 2*r+1, 2*c+1
    def in_bounds(r,c): return 0<=r<base_rows and 0<=c<base_cols

    def carve(r,c):
        visited[r][c] = True
        mr, mc = cell_to_mat(r,c)
        maze[mr][mc] = T_FLOOR
        random.shuffle(dirs)
        for dr,dc in dirs:
            nr, nc = r+dr, c+dc
            if in_bounds(nr,nc) and not visited[nr][nc]:
                maze[mr+dr][mc+dc] = T_FLOOR
                carve(nr,nc)

    carve(random.randrange(base_rows), random.randrange(base_cols))
    return maze

# ── Add loops for “easy” mode ──────────────────────────────────────────
def add_loops_to_maze(maze, p=0.3):
    R, C = len(maze), len(maze[0])
    for r in range(1,R-1):
        for c in range(1,C-1):
            if maze[r][c]==T_WALL:
                # horizontal loop
                if maze[r][c-1]==T_FLOOR and maze[r][c+1]==T_FLOOR and random.random()<p:
                    maze[r][c]=T_FLOOR
                # vertical loop
                if maze[r-1][c]==T_FLOOR and maze[r+1][c]==T_FLOOR and random.random()<p:
                    maze[r][c]=T_FLOOR
    return maze

# ── Top‐level maze generator ──────────────────────────────────────────
def generate_maze(base_rows, base_cols, difficulty):
    m = create_maze_map(base_rows, base_cols)
    if difficulty == "easy":
        m = add_loops_to_maze(m, 0.3)
    return m

# ── Hidden‐room distribution ─────────────────────────────────────────
def distribute_hidden_rooms(maze, num_hidden_per_quadrant=4):
    R, C = len(maze), len(maze[0])
    quads = [
        (0,R//2,    0,C//2),
        (0,R//2,    C//2,C),
        (R//2,R,    0,C//2),
        (R//2,R,    C//2,C)
    ]
    for r0,r1,c0,c1 in quads:
        cand = []
        for r in range(r0,r1):
            for c in range(c0,c1):
                if maze[r][c]==T_WALL:
                    cnt = 0
                    for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]:
                        rr,cc = r+dr, c+dc
                        if 0<=rr<R and 0<=cc<C and maze[rr][cc]==T_FLOOR:
                            cnt += 1
                    if cnt==1:
                        cand.append((r,c))
        random.shuffle(cand)
        added = 0
        for r,c in cand:
            if added>=num_hidden_per_quadrant: break
            if any(0<=r+dr<R and 0<=c+dc<C and maze[r+dr][c+dc]==T_HIDDEN
                   for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]):
                continue
            maze[r][c] = T_HIDDEN
            added += 1
    return maze

# ── Pygame setup & generate everything ───────────────────────────────
pygame.init()
SIZE_X, SIZE_Y = 1000, 750

# temp screen for options
screen = pygame.display.set_mode((SIZE_X, SIZE_Y))
clock  = pygame.time.Clock()

# 1) pick settings
maze_difficulty, BASE_ROWS, BASE_COLS, enemy_count = maze_options_screen(screen, clock)

# 2) build & decorate maze
matrix = generate_maze(BASE_ROWS, BASE_COLS, maze_difficulty)
matrix = distribute_hidden_rooms(matrix, 4)

# 3) grid metrics
GRID_ROWS = len(matrix)
GRID_COLS = len(matrix[0])
PIXEL_ONE_X = SIZE_X / GRID_COLS
PIXEL_ONE_Y = SIZE_Y / GRID_ROWS

# ── Find the player start (bottom‑leftmost floor) ───────────────────
def find_start():
    for i in range(1, GRID_ROWS):
        for j in range(GRID_COLS):
            if matrix[GRID_ROWS - i][j] == T_FLOOR:
                return (GRID_ROWS - i, j)
    return (0, 0)

# ── Flood fill reachable floor/hidden ───────────────────────────────
def _reachable(start):
    R, C = GRID_ROWS, GRID_COLS
    vis = {start}
    q = deque([start])
    while q:
        r, c = q.popleft()
        for dr,dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if 0<=nr<R and 0<=nc<C and (nr,nc) not in vis \
               and matrix[nr][nc] in (T_FLOOR, T_HIDDEN):
                vis.add((nr,nc)); q.append((nr,nc))
    return vis

# ── Place key & door based on reachability ──────────────────────────
start_cell = find_start()
reach = _reachable(start_cell)
KEY_POS = max(reach, key=lambda rc: (rc[0], rc[1]))
DOOR_POS = min(reach, key=lambda rc: rc[0] + (GRID_COLS-1-rc[1]))
matrix[KEY_POS[0]][KEY_POS[1]]   = T_KEY
matrix[DOOR_POS[0]][DOOR_POS[1]] = T_DOOR_C

# ── Build border_tuples for walls & hidden rooms ────────────────────
border_tuples = []
for r in range(GRID_ROWS):
    for c in range(GRID_COLS):
        if matrix[r][c] in (T_WALL, T_HIDDEN):
            x = c * PIXEL_ONE_X
            y = r * PIXEL_ONE_Y
            border_tuples.append((r, c, x, y, PIXEL_ONE_X, PIXEL_ONE_Y))

# ── Compute player start in pixels ──────────────────────────────────
pr, pc = find_start()
player_start_x = pc * PIXEL_ONE_X
player_start_y = pr * PIXEL_ONE_Y
