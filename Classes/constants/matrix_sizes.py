import pygame
import numpy as np

# Initialize Pygame
pygame.init()

# Constants
SIZE_X = 1100
SIZE_Y = 750
BROWN = (139, 69, 19)  # Brown color for walls

# 4x4 Graph (1 = Path, 0 = Wall)
graph = np.array([
    [0, 1, 1, 0],
    [1, 0, 1, 1],
    [1, 1, 0, 1],
    [0, 1, 1, 0]
])

SIZE_OF_X = len(graph[0])  # Columns
SIZE_OF_Y = len(graph)      # Rows

# Width and height of each grid cell
PIXEL_ONE_X = SIZE_X / SIZE_OF_X
PIXEL_ONE_Y = SIZE_Y / SIZE_OF_Y

# Set up the display
screen = pygame.display.set_mode((SIZE_X, SIZE_Y))
pygame.display.set_caption("Stealth Game - Map")

# Store the wall positions
border_tuples = []
for i in range(SIZE_OF_Y):
    for j in range(SIZE_OF_X):  # Fix: Loop over SIZE_OF_X instead of SIZE_X
        if graph[i][j] == 0:
            start_X = j * PIXEL_ONE_X
            start_Y = i * PIXEL_ONE_Y
            border_tuples.append((start_X, start_Y))  # Fix: Store as (x, y)
