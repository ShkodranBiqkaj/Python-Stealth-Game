import pytest
from Logic.patrol_generator import PatrolGenerator

@pytest.fixture

def generator():
    # Minimal dummy generator; matrix and region size don't affect _neighbors
    return PatrolGenerator(
        matrix=[[1]],
        grid_cols=1,
        grid_rows=1,
        tile_size=(10, 10),
        patrolling_area=(0, 0, 10, 10),
        enemies=[],
        difficulty_level=1,
        base_marker=5,
        palette=[(0,0,0,0)]
    )


def test_neighbors_center(generator):
    # Even outside bounds, _neighbors yields all four orthogonal offsets
    cell = (5, 5)
    nbrs = set(generator._neighbors(cell))
    assert nbrs == {(6,5), (4,5), (5,6), (5,4)}


def test_neighbors_corner(generator):
    # Corner cell should still yield four potential neighbors
    cell = (0, 0)
    nbrs = set(generator._neighbors(cell))
    assert nbrs == {(1,0), (-1,0), (0,1), (0,-1)}

def test_bfs_path_trivial(generator):
    """
    When start == goal, should return the single-cell path.
    """
    region = {(0, 0)}
    assert generator._bfs_path((0, 0), (0, 0), region) == [(0, 0)]

def test_bfs_path_simple_route(generator):
    """
    In a small L-shaped region, ensure we get a valid shortest path.
    """
    region = {(0,0), (1,0), (1,1)}
    start, goal = (0,0), (1,1)
    path = generator._bfs_path(start, goal, region)
    assert path == [(0,0), (1,0), (1,1)]

def test_bfs_path_unreachable(generator):
    """
    If goal is not in region or no connecting route, should return an empty list.
    """
    region = {(0,0), (1,0), (0,1)}
    # goal (1,1) is absent
    assert generator._bfs_path((0,0), (1,1), region) == []

def test_bfs_path_blocked(generator):
    """
    Even if goal is in region, if walls block connectivity, return empty.
    """
    region = {(0,0), (1,1)}  # direct neighbor missing
    assert generator._bfs_path((0,0), (1,1), region) == []

@pytest.mark.parametrize("region, start, expected", [
    # Single-cell region
    ({(0,0)}, (0,0), [(0,0)]),
    # Two-cell linear: should go out and back
    ({(0,0),(1,0)}, (0,0), [(0,0),(1,0),(0,0)]),
    # L-shape: (0,0)->(1,0)->(1,1)->back to (1,0)->(0,0)
    ({(0,0),(1,0),(1,1)}, (0,0), [(0,0),(1,0),(1,1),(1,0),(0,0)]),
    ])

def test_dfs_euler_basic(generator, region, start, expected):
    # Verify Eulerian DFS tour includes backtracking steps
    route = generator._dfs_euler(start, region)
    assert route == expected

def test_dfs_euler_full_cover(generator):
    # For a 2x2 square, ensure all cells appear at least once
    region = {(0,0),(1,0),(0,1),(1,1)}
    start = (0,0)
    route = generator._dfs_euler(start, region)
    # Every region cell visited at least once
    for cell in region:
        assert cell in route
    # First element is the start
    assert route[0] == start
    # Last element is also the start (full backtrack)
    assert route[-1] == start

#optimize
@pytest.mark.parametrize("route, expected", [
    # Empty route remains empty
    ([], []),
    # Single-element remains
    ([(0,0)], [(0,0)]),
    # Collapse consecutive duplicates, e.g. AAA -> A
    ([(1,1), (1,1), (1,1)], [(1,1)]),
    # Remove a single U-turn X->Y->X
    ([(0,0), (1,0), (0,0)], [(0,0), (0,0)]),
    # Longer U-turn C->A->B->A->C pattern
    ([(0,0),(1,0),(2,0),(1,0),(0,0)], [(0,0),(1,0),(1,0),(0,0)]),
    # Multiple consecutive U-turns: A-B-C-B-A -> remove C then B
    ([(0,0),(1,0),(2,0),(1,0),(0,0)], [(0,0),(1,0),(1,0),(0,0)])
    ])
def test_optimize_various(generator, route, expected):
    """
    Ensure that _optimize collapses duplicates and removes all X→Y→X patterns.
    """
    result = generator._optimize(route)
    assert result == expected

@pytest.fixture
def small_generator():
    # 3×3 grid with a mix of floor (1) and wall (0)
    matrix = [
    [0, 1, 0],
    [1, 1, 1],
    [0, 1, 0],
    ]
    return PatrolGenerator(
    matrix=matrix,
    grid_cols=3,
    grid_rows=3,
    tile_size=(10, 10),
    patrolling_area=(0, 0, 30, 30),  # cover full map
    enemies=[],
    difficulty_level=1,
    base_marker=5,
    palette=[(0,0,0,0)]
    )

def test_extract_full_area(small_generator):
    """
    With patrolling_area covering the entire map, region should include
    only those cells whose matrix value is in FLOORS (1).
    """
    expected = {(1,0), (0,1), (1,1), (2,1), (1,2)}
    region = small_generator._extract_region()
    assert region == expected

@pytest.fixture
def partial_generator():
    # 3×3 grid all floor
    matrix = [[1]*3 for _ in range(3)]
    # Restrict patrol area to the bottom-left 2×2 pixels -> cells (0,0),(1,0),(0,1),(1,1)
    return PatrolGenerator(
    matrix=matrix,
    grid_cols=3,
    grid_rows=3,
    tile_size=(10, 10),
    patrolling_area=(0, 0, 20, 20),
    enemies=[],
    difficulty_level=1,
    base_marker=5,
    palette=[(0,0,0,0)]
    )

def test_extract_partial_area(partial_generator):
    """
    patrolling_area=(0,0,20,20) should include cells with c in [0,1], r in [0,1].
    """
    expected = {(0,0), (1,0), (0,1), (1,1)}
    region = partial_generator._extract_region()
    assert region == expected

@pytest.fixture
def out_of_bounds_generator():
    # 2×2 grid of floors
    matrix = [[1,1],[1,1]]
    # patrol area partially outside pixel bounds
    return PatrolGenerator(
    matrix=matrix,
    grid_cols=2,
    grid_rows=2,
    tile_size=(10, 10),
    patrolling_area=(-10, -10, 15, 15),
    enemies=[],
    difficulty_level=1,
    base_marker=5,
    palette=[(0,0,0,0)]
    )

def test_extract_with_out_of_bounds(out_of_bounds_generator):
    """
    Negative start and end beyond grid should be clamped to valid cells.
    patrolling_area=(-10,-10,15,15) => c0=-1,c1=1 yields only cell (0,0)
    """
    expected = {(0,0)}
    region = out_of_bounds_generator._extract_region()
    assert region == expected

#choose_starts


#partition

#join dead ends

#generate routes
