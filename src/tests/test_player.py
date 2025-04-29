import pytest
import pygame
from Logic.player import Player
from Logic.map_creation import T_WALL, T_FLOOR, T_KEY, T_DOOR_C, T_DOOR_O, T_HIDDEN

@pytest.fixture
def simple_matrix():
    # 4×4 grid so we can test edges easily
    # start with all floors
    return [[T_FLOOR]*4 for _ in range(4)]

@pytest.fixture
def player(simple_matrix):
    # place player at pixel (15,25) in a 4×4 grid of 10×10 tiles
    # so grid cell = (1,2)
    return Player(
        player_pos_x=15,
        player_pos_y=25,
        matrix=[row[:] for row in simple_matrix],
        PIXEL_ONE_X=10,
        PIXEL_ONE_Y=10
    )

def test_get_position_returns_current_coords(player):
    """
    get_position() should always return the tuple (pos_X, pos_Y).
    """
    # initial
    assert player.get_position() == (player.pos_X, player.pos_Y) == (15, 25)

    # now mutate the internal fields and verify it follows suit
    player.pos_X = 99
    player.pos_Y =  42
    assert player.get_position() == (99, 42)

@pytest.mark.parametrize("door_pos, expected", [
    # door_pos = (row, col)

    ((2, 1), True),   # same cell:  |1−1|+|2−2| = 0
    ((1, 1), True),   # above-left:  |1−1|+|2−1| = 1
    ((2, 2), True),   # right:       |1−2|+|2−2| = 1
    ((3, 2), False),  # two down:    |1−2|+|2−3| = 2
    ((2, 3), False),  # two right:   |1−3|+|2−2| = 2
])

def test_near_door_manhattan(player, door_pos, expected):
    """
    near_door returns True iff the manhattan distance
    between the player's current grid cell and door_pos ≤ 1.
    """
    assert player.near_door(door_pos) is expected

@pytest.mark.parametrize("pixel, expected_cell", [
    # Center of top‐left tile → (0,0)
    ((5.0,   5.0),   (0, 0)),
    # Just inside bottom‐right of (0,0)
    ((9.999, 9.999), (0, 0)),
    # Exactly on vertical boundary → moves to column 1
    ((10.0,  4.0),   (1, 0)),
    # Exactly on horizontal boundary → moves to row 1
    (( 4.0, 10.0),   (0, 1)),
    # Center of bottom‐right tile (2,2)
    ((25.0, 25.0),   (2, 2)),
    # Out‐of‐bounds maps outside range
    ((-0.1, -0.1),   (-1, -1)),
    ((30.0, 15.0),   ( 3,  1)),
])
def test_player_pixel_to_grid_various(player, pixel, expected_cell):
    """
    pixel_to_grid should floor‐divide by the tile size,
    so boundaries move you into the next cell;
    out‐of‐bounds pixels produce out‐of‐range cells.
    """
    assert player.pixel_to_grid(pixel) == expected_cell

def test_check_collision(player):
    # 1) No collision when all four corners are over floor.
    assert not player.check_collision(5, 5)

    # 2) Collision if any corner hits a wall cell.
    #    Make the cell at (1,1) a wall; placing sprite at (10,10) 
    #    puts its top-left corner there → collision.
    player.matrix[1][1] = T_WALL
    assert player.check_collision(10, 10)

    # 3) Collision if any corner is out-of-bounds (negative coords).
    assert player.check_collision(-1, 5)

    # 4) Collision if any corner is out-of-bounds (beyond map edge).
    #    On a 3×3 grid, pixel x=30 lies just past the rightmost tile.
    assert player.check_collision(30, 5)

#test update
@pytest.fixture
def roomy_player():
    """
    Create a large open map (10×10 tiles) and center the player so
    there's ample space for movement without hitting collisions.
    """
    matrix = [[T_FLOOR] * 10 for _ in range(10)]
    # Center at pixel (50,50) -> cell (5,5)
    return Player(player_pos_x=50, player_pos_y=50,
                  matrix=matrix,
                  PIXEL_ONE_X=10, PIXEL_ONE_Y=10)

# Utility to simulate a single key press
def simulate_key(monkeypatch, key):
    def get_pressed():
        keys = [False] * 512
        keys[key] = True
        return keys
    monkeypatch.setattr(pygame.key, 'get_pressed', get_pressed)

@pytest.mark.parametrize("key, attr, sign", [
    (pygame.K_w, 'pos_Y', -1),  # up: decrease Y
    (pygame.K_s, 'pos_Y',  1),  # down: increase Y
    (pygame.K_a, 'pos_X', -1),  # left: decrease X
    (pygame.K_d, 'pos_X',  1),  # right: increase X
])
def test_move_directions(monkeypatch, roomy_player, key, attr, sign):
    """Test movement in all four directions via parametrize."""
    initial = getattr(roomy_player, attr)
    simulate_key(monkeypatch, key)
    roomy_player.move()
    updated = getattr(roomy_player, attr)
    if sign < 0:
        assert updated < initial, f"Expected {attr} < {initial}, got {updated}"
    else:
        assert updated > initial, f"Expected {attr} > {initial}, got {updated}"


def test_key_pickup(monkeypatch, roomy_player):
    """Moving onto a key tile should set has_key and clear the tile."""
    # Increase speed so single move crosses into the next cell
    roomy_player.speed = roomy_player.PIXEL_ONE_X

    col, row = roomy_player.pixel_to_grid((50,50))
    roomy_player.matrix[row][col+1] = T_KEY

    simulate_key(monkeypatch, pygame.K_d)
    roomy_player.move()
    assert roomy_player.has_key, "Player did not pick up the key after moving onto it"
    # original key cell becomes floor
    assert roomy_player.matrix[row][col+1] == T_FLOOR

def test_closed_door_block(monkeypatch, roomy_player):
    """Moving onto a closed door without a key should rollback to start."""
    col, row = roomy_player.pixel_to_grid((50,50))
    roomy_player.matrix[row][col-1] = T_DOOR_C
    initial = (roomy_player.pos_X, roomy_player.pos_Y)
    simulate_key(monkeypatch, pygame.K_a)
    roomy_player.move()
    assert (roomy_player.pos_X, roomy_player.pos_Y) == initial


def test_open_door_win(monkeypatch, roomy_player):
    """Moving onto an open door should set win=True."""
    # Make sure one move crosses into the door cell:
    roomy_player.speed = roomy_player.PIXEL_ONE_X

    col, row = roomy_player.pixel_to_grid((50,50))
    roomy_player.matrix[row+1][col] = T_DOOR_O

    simulate_key(monkeypatch, pygame.K_s)
    roomy_player.move()
    assert roomy_player.win, "Player did not win after moving onto an open door"
