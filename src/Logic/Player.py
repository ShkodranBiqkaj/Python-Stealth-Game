# src/Logic/Player.py

import pygame
import time
from .map_creation import T_FLOOR, T_KEY, T_HIDDEN, T_DOOR_C, T_DOOR_O, T_WALL

class Player:
    def __init__(self, player_pos_x, player_pos_y, matrix, PIXEL_ONE_X, PIXEL_ONE_Y):
        # Load & scale images for each direction (40×40)
        self.images = {
            'down': [
                pygame.transform.scale(pygame.image.load("assets/boy_down_1.png").convert_alpha(), (40, 40)),
                pygame.transform.scale(pygame.image.load("assets/boy_down_2.png").convert_alpha(), (40, 40)),
            ],
            'up': [
                pygame.transform.scale(pygame.image.load("assets/boy_up_1.png").convert_alpha(), (40, 40)),
                pygame.transform.scale(pygame.image.load("assets/boy_up_2.png").convert_alpha(), (40, 40)),
            ],
            'left': [
                pygame.transform.scale(pygame.image.load("assets/boy_left_1.png").convert_alpha(), (40, 40)),
                pygame.transform.scale(pygame.image.load("assets/boy_left_2.png").convert_alpha(), (40, 40)),
            ],
            'right': [
                pygame.transform.scale(pygame.image.load("assets/boy_right_1.png").convert_alpha(), (40, 40)),
                pygame.transform.scale(pygame.image.load("assets/boy_right_2.png").convert_alpha(), (40, 40)),
            ],
        }

        # Initial state
        self.direction = 'down'
        self.current_frame = 0
        self.current_image = self.images[self.direction][0]

        # World data
        self.matrix = matrix
        self.PIXEL_ONE_X = PIXEL_ONE_X
        self.PIXEL_ONE_Y = PIXEL_ONE_Y

        # Position & movement
        self.pos_X = player_pos_x
        self.pos_Y = player_pos_y
        self.speed = 2.5

        # Animation timing
        self.frames_per_step = 10
        self.frame_timer = 0

        # Key state
        self.has_key = False

        # Game flags
        self.game_over = False
        self.win = False

    def move(self):
        # Store previous for possible rollback
        prev_x, prev_y = self.pos_X, self.pos_Y

        keys = pygame.key.get_pressed()
        dx = dy = 0
        if keys[pygame.K_w]:
            dy = -self.speed; self.direction = 'up'
        if keys[pygame.K_s]:
            dy =  self.speed; self.direction = 'down'
        if keys[pygame.K_a]:
            dx = -self.speed; self.direction = 'left'
        if keys[pygame.K_d]:
            dx =  self.speed; self.direction = 'right'
        if dx == 0 and dy == 0:
            return  # no movement

        # Attempt horizontal move
        new_x = self.pos_X + dx
        if not self.check_collision(new_x, self.pos_Y):
            self.pos_X = new_x

        # Attempt vertical move
        new_y = self.pos_Y + dy
        if not self.check_collision(self.pos_X, new_y):
            self.pos_Y = new_y

        # Handle interactions on the new cell
        col, row = self.pixel_to_grid((self.pos_X, self.pos_Y))
        tile = self.matrix[row][col]

        if tile == T_KEY:
            self.has_key = True
            self.matrix[row][col] = T_FLOOR

        elif tile == T_HIDDEN:
            # keep hidden room intact
            pass

        elif tile == T_DOOR_C:
            if self.has_key:
                self.matrix[row][col] = T_DOOR_O
            else:
                # bump into closed door: rollback
                self.pos_X, self.pos_Y = prev_x, prev_y

        elif tile == T_DOOR_O:
            self.win = True

        # Animate
        self.frame_timer += 1
        if self.frame_timer >= self.frames_per_step:
            self.frame_timer = 0
            self.current_frame = (self.current_frame + 1) % 2
        self.current_image = self.images[self.direction][self.current_frame]

    def check_collision(self, x, y):
        """
        Four-corner test against walls and out-of-bounds.
        Returns True if there's a collision.
        """
        corners = [
            (x,    y),
            (x+29, y),
            (x,    y+29),
            (x+29, y+29),
        ]
        for cx, cy in corners:
            col, row = self.pixel_to_grid((cx, cy))
            # Out of bounds
            if not (0 <= row < len(self.matrix) and 0 <= col < len(self.matrix[0])):
                return True
            # Wall collision
            if self.matrix[row][col] == T_WALL:
                return True
        return False

    def pixel_to_grid(self, pixel_pos):
        x, y = pixel_pos
        return (
            int(x // self.PIXEL_ONE_X),
            int(y // self.PIXEL_ONE_Y)
        )

    def get_win(self):
        return self.win

    def near_door(self, door_pos):
        px, py = self.pixel_to_grid((self.pos_X, self.pos_Y))
        dr, dc = door_pos
        return abs(px - dc) + abs(py - dr) <= 1

    def get_position(self):
        return (self.pos_X, self.pos_Y)

