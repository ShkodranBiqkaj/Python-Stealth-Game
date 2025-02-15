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
    [1, 1, 1, 0],
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

#2 put all 0 coordinates in an array. as double tuples. so ((start_of_x,end_of_x),(start_of_y,end_of_y))
border_tuples = []

for i in range(SIZE_OF_Y):
    for j in range(SIZE_OF_X):
        if(graph[i][j] == 0):
            start_X = i * PIXEL_ONE_X
            end_x = start_X + PIXEL_ONE_X
            X_BORDERS = (start_X, end_x)
            start_y = j * PIXEL_ONE_Y
            end_y = start_y + PIXEL_ONE_Y
            Y_BORDERS = (start_y, end_y)
            border_tuples.append((X_BORDERS,Y_BORDERS))
