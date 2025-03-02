import heapq
from constants.matrix_sizes import *

MOVES = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # Right, Down, Left, Up

def a_star(start, grid):
    open_list = []
    heapq.heappush(open_list, (0, start))  # (cost, node)
    
    came_from = {}  # To store the path
    g_score = {start: 0}  # Cost to reach each node
    f_score = {start: float('inf')}  # Estimated total cost

    # Find the player's position (goal)
    goal = None
    for y in range(SIZE_OF_Y):
        for x in range(SIZE_OF_X):
            if grid[y][x] == 2:  # Player's position
                goal = (x, y)
                break
        if goal:
            break  # Stop searching once the goal is found

    if not goal:
        print("Player position (2) not found in the grid.")
        return []  # No goal found, return empty path
    
    f_score[start] = heuristic(start, goal)

    print(f"Enemy starts at: {start}")
    print(f"Player (goal) found at: {goal}")

    while open_list:
        _, current = heapq.heappop(open_list)

        # If the enemy reaches the player, reconstruct the path
        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.reverse()
            print(f"Path found: {path}")
            return path  # Return the shortest path to the player
        
        # Explore neighbors
        for move in MOVES:
            neighbor = (current[0] + move[0], current[1] + move[1])
            
            # Check if the neighbor is within bounds and is a valid move (1 or 2)
            if 0 <= neighbor[0] < SIZE_OF_X and 0 <= neighbor[1] < SIZE_OF_Y:
                if grid[neighbor[1]][neighbor[0]] in (1, 2):  # Can move on 1 (walkable space) or 2 (player)
                    tentative_g_score = g_score[current] + 1  # Assume uniform cost
                    
                    if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g_score
                        f_score[neighbor] = tentative_g_score + heuristic(neighbor, goal)
                        heapq.heappush(open_list, (f_score[neighbor], neighbor))
    
    print("No path found.")
    return []  # No path found
def heuristic(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])  # Manhattan distance
