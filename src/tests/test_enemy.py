# tests/test_enemy.py
import math
import time
import pytest
from Logic.enemy import Enemy

@pytest.fixture
def matrix_3x3():
    # a simple 3×3 open matrix
    return [[1,1,1],
            [1,1,1],
            [1,1,1]]

@pytest.fixture
def enemy(matrix_3x3):
    # place enemy at pixel (15, 25) in a 3×3 grid of 10×10 tiles
    return Enemy(
        position=(15,25),
        patrol_route=[(0,0),(2,2)],
        matrix=matrix_3x3,
        grid_rows=3,
        grid_cols=3,
        tile_size=(10,10),
        move_speed=1.0,
        update_interval=1.0
    )

#getter test
def test_get_position(enemy):
    # get_position() should return the same tuple as the .position attribute
    assert enemy.get_position() == enemy.position

#grid_to_pixel(self,cell)
def test_grid_to_pixel(enemy):
    # With tile_size=(10,10), grid cell (2,1) should map to pixel (2*10 + 5, 1*10 + 5)
    expected_x = 2 * enemy.PIXEL_ONE_X + enemy.PIXEL_ONE_X / 2
    expected_y = 1 * enemy.PIXEL_ONE_Y + enemy.PIXEL_ONE_Y / 2
    px, py = enemy.grid_to_pixel((2, 1))
    assert px == expected_x
    assert py == expected_y

@pytest.mark.parametrize("cell,exp", [
    ((0,0),(5,5)),
    ((1,0),(15,5)),
    ((0,2),(5,25)),
    ((3,4),(35,45)),
])

#pixel_to_grid(self, cell)
def test_grid_to_pixel_various(enemy, cell, exp):
    px, py = enemy.grid_to_pixel(cell)
    assert (px, py) == exp

#in_bounds(self,cell)
@pytest.mark.parametrize("pixel,expected", [
    # Just inside the top‐left tile
    (( 9.9999,  9.9999), (0, 0)),
    # Exactly on the vertical boundary moves you to the next column
    ((10.0,     5.0   ), (1, 0)),
    # Just past the boundary still column 1
    ((10.0001,  5.0   ), (1, 0)),
    # On the horizontal boundary moves you to the next row
    (( 5.0,    10.0  ), (0, 1)),
])
def test_pixel_to_grid_boundaries(enemy, pixel, expected):
    """Edge‐cases around tile boundaries and floating‐point rounding."""
    assert enemy.pixel_to_grid(pixel) == expected

def test_pixel_to_grid_out_of_bounds(enemy):
    """Negative or oversize pixels map outside and in_bounds() catches them."""
    # Negative pixel should yield negative cell
    neg_cell = enemy.pixel_to_grid((-0.1, -0.1))
    assert neg_cell == (-1, -1)
    assert not enemy.in_bounds(neg_cell)

    # Pixel just past bottom‐right of a 3×3 grid (30×30 px)
    max_px = (enemy.GRID_COLS * enemy.PIXEL_ONE_X, 
              enemy.GRID_ROWS * enemy.PIXEL_ONE_Y)
    cell = enemy.pixel_to_grid(max_px)
    assert cell == (enemy.GRID_COLS, enemy.GRID_ROWS)
    assert not enemy.in_bounds(cell)

@pytest.mark.parametrize("cell,expected", [
    ((0, 0), True),    # top-left
    ((2, 2), True),    # bottom-right of a 3×3
    ((-1, 0), False),  # c < 0
    ((0, -1), False),  # r < 0
    ((3, 0), False),   # c == GRID_COLS
    ((0, 3), False),   # r == GRID_ROWS
    ((3, 3), False),   # both out
])
def test_in_bounds_various(enemy, cell, expected):
    assert enemy.in_bounds(cell) is expected


#is_walkable(self,cell)
#all is_walkable does is check if a position in the matrix is walkable by enemy ai
@pytest.mark.parametrize("matrix, cell, expected", [
    # Single-cell matrices (1×1)
    ([[1]],        (0, 0), True),   # floor
    ([[2]],        (0, 0), True),   # player start
    ([[5]],        (0, 0), True),   # closed door
    ([[6]],        (0, 0), True),   # open door
    ([[7]],        (0, 0), True),   # overlay marker (>=5)

    ([[0]],        (0, 0), False),  # wall
    ([[3]],        (0, 0), False),  # hidden room
    ([[4]],        (0, 0), False),  # key

    # Out‐of‐bounds on a 1×1 matrix
    ([[1]],        (1, 0), False),
    ([[1]],        (0, 1), False),
    ([[1]],        (-1,0), False),
    ([[1]],        (0,-1), False),

    # Bigger matrix example
    (
      [            # 2×2:
        [1, 0],    # floor, wall
        [4, 5]     # key, closed door
      ],
      (1, 1),      # testing cell with value 5
      True
    ),
    (
      [             
        [1, 0],
        [4, 5]
      ],
      (0, 1),      # testing cell with value 4 (key)
      False
    ),
])

def test_is_walkable_with_various_matrices(matrix, cell, expected):
    """
    Instantiate a fresh Enemy for each matrix so that each case is completely isolated.
    """
    rows = len(matrix)
    cols = len(matrix[0])
    e = Enemy(
        position=(0,0),
        patrol_route=[],
        matrix=matrix,
        grid_rows=rows,
        grid_cols=cols,
        tile_size=(10,10)
    )
    assert e.is_walkable(cell) is expected

#check_collision() checks
@pytest.fixture
def small_enemy():
    # 3×3 open floor matrix initially
    mat = [[1]*3 for _ in range(3)]
    return Enemy(
        position=(0,0),
        patrol_route=[],
        matrix=mat,
        grid_rows=3,
        grid_cols=3,
        tile_size=(10,10)
    )

def test_check_collision_no_collision(small_enemy):
    # floor at (0,0) -> pixel (5,5)
    assert not small_enemy.check_collision(5, 5)
    assert not small_enemy.check_collision((5, 5))

def test_check_collision_wall(small_enemy):
    # make cell (1,1) a wall
    small_enemy.matrix[1][1] = 0
    px = 1 * small_enemy.PIXEL_ONE_X + 1  # somewhere in that tile
    py = 1 * small_enemy.PIXEL_ONE_Y + 1
    assert small_enemy.check_collision(px, py)
    assert small_enemy.check_collision((px, py))

def test_check_collision_out_of_bounds(small_enemy):
    # negative pixel → column,row = (-1,-1)
    assert small_enemy.check_collision(-1, -1)
    # pixel just past right edge (3*10 = 30 px) → out-of-bounds
    assert small_enemy.check_collision(30, 5)
    # and via tuple style
    assert small_enemy.check_collision((5, 30))

def test_get_neighbors_interior(enemy):
    # In a 3×3 grid, the center cell (1,1) has all four neighbors
    nbrs = set(enemy.get_neighbors((1,1)))
    assert nbrs == {(2,1), (0,1), (1,2), (1,0)}

@pytest.mark.parametrize("cell,expected", [
    # top-left corner → only right & down
    ((0,0), {(1,0), (0,1)}),
    # right edge center → left, up, down
    ((2,1), {(1,1), (2,2), (2,0)}),
    # bottom-right corner → left & up
    ((2,2), {(1,2), (2,1)}),
])
def test_get_neighbors_edges(enemy, cell, expected):
    assert set(enemy.get_neighbors(cell)) == expected

def test_find_path_reachable(enemy):
    # 1) Place enemy at top-left cell (0,0)
    enemy.position = enemy.grid_to_pixel((0,0))
    # 2) Ensure the matrix is fully walkable
    enemy.matrix = [[1]*3 for _ in range(3)]
    # 3) Compute path to bottom-right cell (2,2)
    target_px = enemy.grid_to_pixel((2,2))
    enemy.find_path(target_px)

    # 4) Expected shortest path is right→right→down→down
    assert enemy.path == [
        (0,0), (1,0), (2,0), (2,1), (2,2)
    ]

def test_find_path_unreachable(enemy):
    # 1) Place enemy at (0,0)
    enemy.position = enemy.grid_to_pixel((0,0))
    # 2) Block off row 0 and column 0 so (2,2) is isolated
    enemy.matrix = [
        [1,0,0],
        [0,1,0],
        [0,0,1],
    ]
    # 3) Attempt path to (2,2)
    target_px = enemy.grid_to_pixel((2,2))
    enemy.find_path(target_px)

    # 4) No route exists ⇒ path stays empty
    assert enemy.path == []

def test_find_path_start_or_goal_unwalkable(enemy):
    # 1) Place enemy at (0,0) but make that start‐cell a wall
    enemy.position = enemy.grid_to_pixel((0,0))
    enemy.matrix[0][0] = 0
    # 2) Also make goal (1,1) a floor but start unwalkable
    target_px = enemy.grid_to_pixel((1,1))
    enemy.find_path(target_px)
    assert enemy.path == []

    # 3) Now restore start, block goal
    enemy.matrix[0][0] = 1
    enemy.matrix[1][1] = 0
    enemy.find_path(target_px)
    assert enemy.path == []

#valid path
def validate_path(enemy, path, start, goal):
    # 1) If no path, both start and goal must be unconnected
    if not path:
        # nothing to validate here
        return

    # 2) Path must start and end correctly
    assert path[0] == start,  f"Path does not start at {start}: {path}"
    assert path[-1] == goal, f"Path does not end at {goal}: {path}"

    # 3) Consecutive steps must be neighbors and walkable
    for a, b in zip(path, path[1:]):
        # neighbor check
        nbrs = enemy.get_neighbors(a)
        assert b in nbrs, f"Step {a} → {b} not neighbors: {nbrs}"
        # walkable check
        assert enemy.is_walkable(b), f"Cell {b} is not walkable"

    # 4) (Optional) also check the start cell is walkable
    assert enemy.is_walkable(start), f"Start {start} unwalkable"

def test_find_path_between_validity(enemy):
    start, goal = (0,0), (2,0)
    path = enemy.find_path_between(start, goal)
    validate_path(enemy, path, start, goal)

def test_find_path_validity(enemy):
    # position at (0,0)
    start = (0,0)
    enemy.position = enemy.grid_to_pixel(start)
    goal = (2,2)
    target_px = enemy.grid_to_pixel(goal)
    enemy.matrix = [[1]*3 for _ in range(3)]  # clear map
    enemy.find_path(target_px)
    validate_path(enemy, enemy.path, start, goal)

#------------move_patrol_area
def test_move_patrol_area_empty_route(enemy):
    """No patrol route ⇒ no change to position or index."""
    orig_pos = enemy.position
    orig_idx = enemy.patrol_index
    enemy.complete_patrol_route = []
    enemy.move_patrol_area()
    assert enemy.position == orig_pos
    assert enemy.patrol_index == orig_idx

def test_move_patrol_area_index_wraps(enemy):
    """
    If patrol_index is ≥ len(route), it should reset to 0 before moving,
    and then move one step toward the first route cell.
    """
    # route of two points
    enemy.complete_patrol_route = [(1,1), (2,2)]
    enemy.patrol_index = 5      # out‐of‐range
    # start at (0,0)
    enemy.position = enemy.grid_to_pixel((0,0))
    enemy.patrol_speed = 100    # force snap-to-next-cell
    enemy.move_patrol_area()

    # 1) patrol_index wrapped 5→0 and then advanced to 1
    assert enemy.patrol_index == 1

    # 2) position snapped to the *next* step on the way to (1,1):
    #    path was [(0,0),(1,0),(1,1)], so next cell is (1,0)
    assert enemy.position == enemy.grid_to_pixel((1,0))

def test_move_patrol_area_partial_step(enemy):
    """
    When dist > patrol_speed, move only partway toward the target
    and do NOT advance patrol_index.
    """
    # Define a simple two‐point route
    enemy.complete_patrol_route = [(0,0), (0,1)]
    # Set index=1 so our target_cell is (0,1)
    enemy.patrol_index = 1
    # Start at the center of (0,0)
    enemy.position = enemy.grid_to_pixel((0,0))
    # Speed = 5px, half the 10px tile height → partial step
    enemy.patrol_speed = 5

    start_px = enemy.position
    next_px  = enemy.grid_to_pixel((0,1))
    dx = next_px[0] - start_px[0]
    dy = next_px[1] - start_px[1]
    dist = math.hypot(dx, dy)

    enemy.move_patrol_area()

    # We should have moved exactly 5px toward (0,1)
    expected_x = start_px[0] + dx / dist * 5
    expected_y = start_px[1] + dy / dist * 5
    assert math.isclose(enemy.position[0], expected_x, abs_tol=1e-6)
    assert math.isclose(enemy.position[1], expected_y, abs_tol=1e-6)

    # And since we didn’t reach the target, patrol_index stays at 1
    assert enemy.patrol_index == 1

def test_move_patrol_area_exact_speed_no_index_advance(enemy):
    """
    When dist == patrol_speed, the else‐branch runs (partial‐move code),
    which still lands exactly on next_px but does NOT advance patrol_index.
    """
    # Set up a two‐point route
    enemy.complete_patrol_route = [(0,0), (0,1)]
    # Point the target at (0,1)
    enemy.patrol_index = 1
    # Start at (0,0)
    enemy.position = enemy.grid_to_pixel((0,0))
    # Distance from (0,0)→(0,1) is 10px; set speed equal to 10px
    enemy.patrol_speed = 10
    next_px = enemy.grid_to_pixel((0,1))

    # Perform the move
    enemy.move_patrol_area()

    # 1) It should land exactly on next_px
    assert enemy.position == next_px

    # 2) But because dist < speed is False when dist==speed,
    #    the "else" partial-move branch runs and does NOT advance patrol_index
    assert enemy.patrol_index == 1

def test_move_patrol_area_unreachable_target(enemy):
    """
    If find_path_between returns empty, code falls back to target_cell,
    so we still move toward it (or snap if speed big).
    """
    enemy.complete_patrol_route = [(0,2)]
    enemy.patrol_index = 1
    # start at (0,0)
    enemy.position = enemy.grid_to_pixel((0,0))
    # make (0,2) unreachable by walls
    m = [[1,0,0],
         [0,0,0],
         [0,0,0]]
    enemy.matrix = m
    enemy.patrol_speed = 100  # force snap

    enemy.move_patrol_area()

    # should have “snapped” to center of (0,2)
    assert enemy.position == enemy.grid_to_pixel((0,2))
    # but since we used the else-branch (dist<speed=True), index advances:
    assert enemy.patrol_index == (0 + 1) % 1  # still 0, since route has length 1

def test_move_patrol_area_full_step(enemy):
    # A longer route, but patrol_index=0 always targets the FIRST point: (0,0)
    enemy.complete_patrol_route = [(0,0),(0,1),(0,2),(1,2)]
    enemy.patrol_index = 0
    # Start at center of (1,2)
    enemy.position = enemy.grid_to_pixel((1,2))
    # Make patrol_speed large so dist < speed
    enemy.patrol_speed = 20

    enemy.move_patrol_area()

    # It should have snapped to the SECOND cell on that path: (0,2)
    assert enemy.position == enemy.grid_to_pixel((0,2))
    # And patrol_index should now be 1 (pointing at the next route entry)
    assert enemy.patrol_index == 1


