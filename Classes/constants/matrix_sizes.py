import pygame
import random

# Initialize Pygame
pygame.init()

SIZE_X = 1000
SIZE_Y = 750

# Let's define how many rows and columns the matrix has
GRID_ROWS = 10
GRID_COLS = 10

PIXEL_ONE_X = SIZE_X / GRID_COLS
PIXEL_ONE_Y = SIZE_Y / GRID_ROWS

matrix = [[1 for _ in range(GRID_COLS)] for _ in range(GRID_ROWS)]

# Example: Set the edges to 1
for i in range(GRID_ROWS):
    matrix[i][0] = 1
    matrix[i][GRID_COLS - 1] = 1
    matrix[0][i] = 1
    matrix[GRID_ROWS - 1][i] = 1

# Add some random 0's in the middle
num_random_ones = 7
for _ in range(num_random_ones):
    x, y = random.randint(1, GRID_ROWS - 2), random.randint(1, GRID_COLS - 2)
    matrix[x][y] = 0

# border_tuples for obstacles
border_tuples = []
for row in range(GRID_ROWS):
    for col in range(GRID_COLS):
        if matrix[row][col] == 0:
            x_start = col * PIXEL_ONE_X
            x_end   = x_start + PIXEL_ONE_X
            y_start = row * PIXEL_ONE_Y
            y_end   = y_start + PIXEL_ONE_Y
            border_tuples.append(((x_start, x_end), (y_start, y_end)))
