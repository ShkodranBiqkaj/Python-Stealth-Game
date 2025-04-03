import pygame
from constants.matrix_sizes import matrix, PIXEL_ONE_X, PIXEL_ONE_Y, unlock_hidden_room

class Player:
    def __init__(self, player_pos_x, player_pos_y):
        # Load and scale images for each direction (two images per direction, 30x30)
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

        # Mark the player's initial position in the matrix.
        col, row = self.pixel_to_grid((self.pos_X, self.pos_Y))
        matrix[row][col] = 2  # 2 = player

        self.game_over = False

    def move(self):
        # Check if player's current grid cell indicates game over (using proper row,col indexing)
        col, row = self.pixel_to_grid((self.pos_X, self.pos_Y))
        if matrix[row][col] == 4:
            self.game_over = True

        keys = pygame.key.get_pressed()

        # Store old position.
        old_x, old_y = self.pos_X, self.pos_Y

        # Compute intended movement along each axis.
        dx = 0
        dy = 0
        if keys[pygame.K_w]:
            dy -= self.speed
            self.direction = 'up'
        if keys[pygame.K_s]:
            dy += self.speed
            self.direction = 'down'
        if keys[pygame.K_a]:
            dx -= self.speed
            self.direction = 'left'
        if keys[pygame.K_d]:
            dx += self.speed
            self.direction = 'right'

        # If E is pressed, try to unlock the hidden room.
        if keys[pygame.K_e]:
            unlock_hidden_room(matrix)

        # If no key is pressed, do nothing.
        if dx == 0 and dy == 0:
            return

        # Attempt movement along each axis separately.
        new_x = old_x + dx
        new_y = old_y + dy

        # Check horizontal movement (only x changes).
        if dx != 0:
            if not self.check_collision(new_x, old_y):
                old_x = new_x
            else:
                new_x = old_x
        # Check vertical movement (only y changes).
        if dy != 0:
            if not self.check_collision(old_x, new_y):
                old_y = new_y
            else:
                new_y = old_y

        # Update the player's position.
        self.pos_X, self.pos_Y = old_x, old_y

        # Update matrix: mark the new cell as occupied by the player.
        new_col, new_row = self.pixel_to_grid((self.pos_X, self.pos_Y))
        if matrix[new_row][new_col] != 3:
            matrix[new_row][new_col] = 2


        # Update animation.
        self.frame_timer += 1
        if self.frame_timer >= self.frames_per_step:
            self.frame_timer = 0
            self.current_frame = (self.current_frame + 1) % 2
        self.current_image = self.images[self.direction][self.current_frame]

    def check_collision(self, new_x, new_y):
        """
        Check if any of the four corners of the 30x30 sprite at (new_x, new_y)
        collides with a blocked tile (value 0) or is out of bounds.
        Now treats cells with values 1, 2, or 3 as walkable.
        """
        corners = [
            (new_x, new_y),               # top-left
            (new_x + 29, new_y),          # top-right
            (new_x, new_y + 29),          # bottom-left
            (new_x + 29, new_y + 29)      # bottom-right
        ]
        for corner_x, corner_y in corners:
            col, row = self.pixel_to_grid((corner_x, corner_y))
            if not (0 <= row < len(matrix) and 0 <= col < len(matrix[0])):
                return True  # Out of bounds.
            if matrix[row][col] ==0:
                return True  # Collides if not walkable.
        return False

    def pixel_to_grid(self, pixel_pos):
        """
        Convert pixel coordinates to matrix coordinates (col, row).
        """
        x, y = pixel_pos
        col = int(x // PIXEL_ONE_X)
        row = int(y // PIXEL_ONE_Y)
        return col, row

    def draw(self, screen):
        screen.blit(self.current_image, (self.pos_X, self.pos_Y))

    def get_position(self):
        """Return the player's current (x, y) in pixels."""
        return (self.pos_X, self.pos_Y)
