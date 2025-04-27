# src/Logic/logic_setup.py

from .Map_creation import (
    MapCreation,
    T_FLOOR, T_KEY, T_DOOR_C, T_DOOR_O,
    T_WALL, T_HIDDEN
)
from .Patrol import PatrolGenerator
from .enemy import Enemy
from .Player import Player
from collections import deque

SIZE_X, SIZE_Y = 1000, 750

class LogicSetup:
    """
    Combines maze generation, player placement, key/door setup and guard patrol routing.
    """
    def __init__(self, difficulty: str, rows: int, cols: int, enemy_count: int):
        self.map_gen     = MapCreation(difficulty, rows, cols, enemy_count)
        self.enemy_count = enemy_count
        self.difficulty  = difficulty

    def generate_game(self):
        # 1) Generate maze and compute grid metrics
        self.matrix     = self.map_gen.generate_maze()
        self.GRID_ROWS  = len(self.matrix)
        self.GRID_COLS  = len(self.matrix[0])
        self.PIXEL_ONE_X = SIZE_X / self.GRID_COLS
        self.PIXEL_ONE_Y = SIZE_Y / self.GRID_ROWS

        # 2) Find player start (bottom-leftmost floor cell)
        self.player_start_cell = self._find_start_cell()
        px, py = self.player_start_cell
        self.player = Player(
            px * self.PIXEL_ONE_X,
            py * self.PIXEL_ONE_Y,
            self.matrix,
            self.PIXEL_ONE_X,
            self.PIXEL_ONE_Y
        )

        # 3) Place key and closed door in matrix
        self.key_pos, self.door_pos = self._place_key_and_door()

        # 4) Instantiate Enemy objects with proper tile_size
        self.enemies = [
            Enemy(
                position=(0, 0),
                patrol_route=[],
                matrix=self.matrix,
                grid_rows=self.GRID_ROWS,
                grid_cols=self.GRID_COLS,
                tile_size=(self.PIXEL_ONE_X, self.PIXEL_ONE_Y),
                move_speed=1.5,
                update_interval=1
            )
            for _ in range(self.enemy_count)
        ]

        # 5) Generate patrol routes and assign to enemies
        PatrolGenerator(
            matrix=self.matrix,
            grid_cols=self.GRID_COLS,
            grid_rows=self.GRID_ROWS,
            tile_size=(self.PIXEL_ONE_X, self.PIXEL_ONE_Y),
            patrolling_area=(0, 0, SIZE_X, SIZE_Y),
            enemies=self.enemies,
            difficulty_level=1 if self.difficulty == 'easy' else 3,
            base_marker=T_DOOR_O + 1,
            palette=[(0, 0, 255, 128), (255, 0, 0, 128), (0, 255, 0, 128)]
        )
        # PatrolGenerator.__init__ calls setup_patrols()

    def handle_input(self, keys):
        """
        keys is pygame.key.get_pressed(), but Player.move() does its own key check.
        We just invoke the move() method here.
        """
        self.player.move()

    def update(self):
        # 1) Key pickup
        px, py = self.player.get_position()
        col = int(px // self.PIXEL_ONE_X)
        row = int(py // self.PIXEL_ONE_Y)

        if not self.player.has_key and self.matrix[row][col] == T_KEY:
            self.player.has_key = True
            self.matrix[row][col] = T_FLOOR

        # 2) Open door when adjacent
        if self.player.has_key and self.door_pos:
            dr, dc = self.door_pos
            if self.player.near_door((dr, dc)):
                self.matrix[dr][dc] = T_DOOR_O

        # 3) Update all enemies
        player_pos = self.player.get_position()
        for en in self.enemies:
            en.update(player_pos)

        self._check_enemy_collision()
        
        # 4) Check win/lose
        return {
            'won':  self.player.get_win(),
            'lost': self.player.game_over
        }

    def _find_start_cell(self):
        for i in range(1, self.GRID_ROWS + 1):
            for x in range(self.GRID_COLS):
                if self.matrix[self.GRID_ROWS - i][x] == T_FLOOR:
                    return (x, self.GRID_ROWS - i)
        return (0, 0)

    def _place_key_and_door(self):
        """
        BFS from the player start to compute true shortest‐path
        distances to every floor‐cell. Then place:
          – door at the farthest cell (as before)
          – key at the ‘median’ cell in that sorted list,
            so you have to traverse roughly half the maze.
        """
        from collections import deque

        start = self.player_start_cell
        R, C = self.GRID_ROWS, self.GRID_COLS

        # 1) BFS to build distance map
        dist = {start: 0}
        q = deque([start])
        while q:
            c, r = q.popleft()
            for dc, dr in [(1,0),(-1,0),(0,1),(0,-1)]:
                nb = (c+dc, r+dr)
                if (0 <= nb[0] < C and 0 <= nb[1] < R
                        and nb not in dist
                        and self.matrix[nb[1]][nb[0]] == T_FLOOR):
                    dist[nb] = dist[(c, r)] + 1
                    q.append(nb)

        # 2) Sort all reachable (excluding start)
        reachable = [cell for cell in dist.keys() if cell != start]
        reachable.sort(key=lambda cell: dist[cell])

        # 3) Farthest = door
        door_cell = reachable[-1]

        # 4) Median = key
        mid = len(reachable) // 2
        key_cell = reachable[mid]

        # 5) Write to matrix
        kx, ky = key_cell
        dx, dy = door_cell
        self.matrix[ky][kx] = T_KEY
        self.matrix[dy][dx] = T_DOOR_C

        return key_cell, door_cell
    
    def _check_enemy_collision(self):
        """If any enemy shares the player’s grid‐cell, trigger game over."""
        # get player cell
        px, py = self.player.get_position()
        pcol = int(px // self.PIXEL_ONE_X)
        prow = int(py // self.PIXEL_ONE_Y)
        # for each enemy, compare grid‐coords
        for en in self.enemies:
            ex, ey = en.get_position()
            ecol = int(ex // self.PIXEL_ONE_X)
            erow = int(ey // self.PIXEL_ONE_Y)
            if ecol == pcol and erow == prow:
                self.player.game_over = True
                return
    
    def border_tuples(self):
        out = []
        for r in range(self.GRID_ROWS):
            for c in range(self.GRID_COLS):
                if self.matrix[r][c] in (T_WALL, T_HIDDEN):
                    x = c * self.PIXEL_ONE_X
                    y = r * self.PIXEL_ONE_Y
                    out.append((r, c, x, y, self.PIXEL_ONE_X, self.PIXEL_ONE_Y))
        return out

    def get_graphics_attributes(self):
        return (
            self.border_tuples(),
            self.matrix,
            (self.GRID_ROWS, self.GRID_COLS),
            (self.PIXEL_ONE_X, self.PIXEL_ONE_Y),
            self.key_pos,
            self.door_pos,
            self.player,
            self.enemies
        )
