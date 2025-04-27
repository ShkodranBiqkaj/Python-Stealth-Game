import random

# ── Tile codes ─────────────────────────────────────────────────────────
T_WALL    = 0  # crate / wall
T_FLOOR   = 1  # open floor
T_PLAYER  = 2  # player start
T_HIDDEN  = 3  # hidden bonus room
T_KEY     = 4  # the key
T_DOOR_C  = 5  # closed door
T_DOOR_O  = 6  # opened door

class MapCreation:
    """
    Encapsulates maze generation logic: perfect DFS carve, optional loops, and hidden rooms.
    """
    def __init__(self, difficulty: str, rows: int, cols: int, enemy_count: int):
        self.maze_difficulty = difficulty  # "easy" or "hard"
        self.BASE_ROWS = rows
        self.BASE_COLS = cols
        self.enemy_count = enemy_count

    def create_maze_map(self) -> list[list[int]]:
        """
        Carve a perfect maze using recursive DFS on a grid of size BASE_ROWS x BASE_COLS.
        Returns a 2D list with walls and floors.
        """
        rows, cols = 2*self.BASE_ROWS + 1, 2*self.BASE_COLS + 1
        maze = [[T_WALL for _ in range(cols)] for _ in range(rows)]
        visited = [[False]*self.BASE_COLS for _ in range(self.BASE_ROWS)]
        dirs = [(-1,0),(1,0),(0,-1),(0,1)]

        def carve(r, c):
            visited[r][c] = True
            maze[2*r+1][2*c+1] = T_FLOOR
            random.shuffle(dirs)
            for dr, dc in dirs:
                nr, nc = r+dr, c+dc
                if 0 <= nr < self.BASE_ROWS and 0 <= nc < self.BASE_COLS and not visited[nr][nc]:
                    maze[2*r+1+dr][2*c+1+dc] = T_FLOOR
                    carve(nr, nc)

        # start carving from a random cell
        carve(random.randrange(self.BASE_ROWS), random.randrange(self.BASE_COLS))
        return maze

    def add_loops_to_maze(self, maze: list[list[int]], p: float = 0.3) -> list[list[int]]:
        """
        In "easy" mode, randomly punch loops by turning some wall cells into floor
        where they connect two floor cells on opposite sides.
        """
        R, C = len(maze), len(maze[0])
        for r in range(1, R-1):
            for c in range(1, C-1):
                if maze[r][c] == T_WALL:
                    # horizontal loop
                    if maze[r][c-1] == T_FLOOR and maze[r][c+1] == T_FLOOR and random.random() < p:
                        maze[r][c] = T_FLOOR
                    # vertical loop
                    if maze[r-1][c] == T_FLOOR and maze[r+1][c] == T_FLOOR and random.random() < p:
                        maze[r][c] = T_FLOOR
        return maze

    def distribute_hidden_rooms(self, maze: list[list[int]], num_hidden_per_quadrant: int = 4) -> list[list[int]]:
        """
        Place small "hidden rooms" (dead-end walls) in each quadrant. Marks them with T_HIDDEN.
        """
        R, C = len(maze), len(maze[0])
        # define four quadrants
        quads = [
            (0, R//2,    0, C//2),
            (0, R//2,    C//2, C),
            (R//2, R,    0, C//2),
            (R//2, R,    C//2, C)
        ]
        for r0, r1, c0, c1 in quads:
            candidates = []
            for r in range(r0, r1):
                for c in range(c0, c1):
                    if maze[r][c] == T_WALL:
                        # count adjacent floor
                        cnt = sum(
                            1 for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]
                            if 0 <= r+dr < R and 0 <= c+dc < C and maze[r+dr][c+dc] == T_FLOOR
                        )
                        if cnt == 1:
                            candidates.append((r, c))
            random.shuffle(candidates)
            added = 0
            for r, c in candidates:
                if added >= num_hidden_per_quadrant:
                    break
                # skip if adjacent to another hidden room
                if any(
                    0 <= r+dr < R and 0 <= c+dc < C and maze[r+dr][c+dc] == T_HIDDEN
                    for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]
                ):
                    continue
                maze[r][c] = T_HIDDEN
                added += 1
        return maze

    def generate_maze(self) -> list[list[int]]:
        """
        Full pipeline: carve, optionally add loops, then place hidden rooms.
        """
        maze = self.create_maze_map()
        if self.maze_difficulty == "easy":
            maze = self.add_loops_to_maze(maze)
        maze = self.distribute_hidden_rooms(maze)
        return maze
