import pygame
from matrix_sizes import matrix, PIXEL_ONE_X, PIXEL_ONE_Y
import time
class Player:
    def __init__(self, player_pos_x, player_pos_y):
        # Load and scale images for each direction (two images per direction, 40×40)
        self.images = {
            'down': [
                pygame.transform.scale(
                    pygame.image.load("../assets/boy_down_1.png").convert_alpha(), (40, 40)
                ),
                pygame.transform.scale(
                    pygame.image.load("../assets/boy_down_2.png").convert_alpha(), (40, 40)
                )
            ],
            'up': [
                pygame.transform.scale(
                    pygame.image.load("../assets/boy_up_1.png").convert_alpha(), (40, 40)
                ),
                pygame.transform.scale(
                    pygame.image.load("../assets/boy_up_2.png").convert_alpha(), (40, 40)
                )
            ],
            'left': [
                pygame.transform.scale(
                    pygame.image.load("../assets/boy_left_1.png").convert_alpha(), (40, 40)
                ),
                pygame.transform.scale(
                    pygame.image.load("../assets/boy_left_2.png").convert_alpha(), (40, 40)
                )
            ],
            'right': [
                pygame.transform.scale(
                    pygame.image.load("../assets/boy_right_1.png").convert_alpha(), (40, 40)
                ),
                pygame.transform.scale(
                    pygame.image.load("../assets/boy_right_2.png").convert_alpha(), (40, 40)
                )
            ]
        }

        # Initial direction, frame, and image.
        self.direction = 'down'
        self.current_frame = 0
        self.current_image = self.images[self.direction][self.current_frame]

        # Position and speed.
        self.pos_X = player_pos_x
        self.pos_Y = player_pos_y
        self.speed = 2.5

        # Animation timing: switch foot every N frames.
        self.frames_per_step = 10
        self.frame_timer = 0

        # Key‐state
        self.has_key = False

        # Mark the player's initial position in the matrix.
        col, row = self.pixel_to_grid((self.pos_X, self.pos_Y))
        matrix[row][col] = 2  # 2 = player

        self.game_over = False
        self.win = False

    def move(self):
        # Check if player's current grid cell indicates game over (value 4)
        col, row = self.pixel_to_grid((self.pos_X, self.pos_Y))
        if matrix[row][col] == 4:
            self.game_over = True

        keys = pygame.key.get_pressed()
        old_x, old_y = self.pos_X, self.pos_Y
        dx = dy = 0
        if keys[pygame.K_w]:
            dy -= self.speed; self.direction = 'up'
        if keys[pygame.K_s]:
            dy += self.speed; self.direction = 'down'
        if keys[pygame.K_a]:
            dx -= self.speed; self.direction = 'left'
        if keys[pygame.K_d]:
            dx += self.speed; self.direction = 'right'

        if dx==0 and dy==0:
            return

        # horizontal move
        if dx:
            if not self.check_collision(old_x+dx, old_y):
                old_x += dx
        # vertical move
        if dy:
            if not self.check_collision(old_x, old_y+dy):
                old_y += dy

        self.pos_X, self.pos_Y = old_x, old_y

        # update matrix marker (unless it's a hidden‐room)
        new_col, new_row = self.pixel_to_grid((self.pos_X, self.pos_Y))
        if matrix[new_row][new_col] == 4:
            self.has_key = True

        if matrix[new_row][new_col] != 3 and not matrix[new_row][new_col] == 6:
            if matrix[new_row][new_col] == 5 and self.has_key:
                matrix[new_row][new_col] = 6
            if matrix[new_row][new_col] == 5:
                print("The key is in possession: " , self.has_key)
            else:
                matrix[new_row][new_col] = 2
        
        if matrix[new_row][new_col] == 6:
            self.win = True

        # animate
        self.frame_timer += 1
        if self.frame_timer >= self.frames_per_step:
            self.frame_timer = 0
            self.current_frame = (self.current_frame + 1) % 2
        self.current_image = self.images[self.direction][self.current_frame]

    def check_collision(self, x, y):
        """Four‐corner test against walls (0) and bounds."""
        corners = [
            (x, y),
            (x+29, y),
            (x, y+29),
            (x+29, y+29)
        ]
        for cx, cy in corners:
            col, row = self.pixel_to_grid((cx, cy))
            if not (0 <= row < len(matrix) and 0 <= col < len(matrix[0])):
                return True
            if matrix[row][col] == 0:
                return True
        return False

    def get_win(self):
        return self.win

    def pixel_to_grid(self, pixel_pos):
        """Convert pixel (x,y) to grid (col,row)."""
        x, y = pixel_pos
        return int(x // PIXEL_ONE_X), int(y // PIXEL_ONE_Y)

    def draw(self, screen):
        screen.blit(self.current_image, (self.pos_X, self.pos_Y))

    def get_position(self):
        """Return the player's current (x, y) in pixels."""
        return (self.pos_X, self.pos_Y)

    def near_door(self, door_pos):
        """
        Return True if player is adjacent (Manhattan ≤ 1)
        to the door's grid‐cell.
        """
        px, py = self.pixel_to_grid(self.get_position())
        dr, dc = door_pos
        return abs(px - dc) + abs(py - dr) <= 1
