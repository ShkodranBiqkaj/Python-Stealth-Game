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

        # Initial direction, frame, and image
        self.direction = 'down'
        self.current_frame = 0
        self.current_image = self.images[self.direction][self.current_frame]

        # Position and speed
        self.pos_X = player_pos_x
        self.pos_Y = player_pos_y
        self.speed = 4

        # Animation timing: switch foot every N frames
        self.frames_per_step = 10
        self.frame_timer = 0

        # Mark the player's initial position in the matrix
        col, row = self.pixel_to_grid((self.pos_X, self.pos_Y))
        matrix[row][col] = 2  # 2 = player

    def move(self):
        keys = pygame.key.get_pressed()

        # Store old position for collision checks
        old_x, old_y = self.pos_X, self.pos_Y
        old_col, old_row = self.pixel_to_grid((old_x, old_y))

        # Compute a potential new position
        new_x, new_y = old_x, old_y
        moved = False
        if keys[pygame.K_e]:
            unlock_hidden_room(matrix)

        if keys[pygame.K_w]:
            new_y -= self.speed
            self.direction = 'up'
            moved = True

        if keys[pygame.K_s]:
            new_y += self.speed
            self.direction = 'down'
            moved = True

        if keys[pygame.K_a]:
            new_x -= self.speed
            self.direction = 'left'
            moved = True

        if keys[pygame.K_d]:
            new_x += self.speed
            self.direction = 'right'
            moved = True

        if moved:
            # Check for collisions using all four corners of the 30x30 sprite
            if self.check_collision(new_x, new_y):
                # Collision detected; revert to old position
                new_x, new_y = old_x, old_y
                moved = False
            else:
                # We can move, so update the matrix
                matrix[old_row][old_col] = 1  # old cell is now walkable
                new_col, new_row = self.pixel_to_grid((new_x, new_y))
                matrix[new_row][new_col] = 2  # new cell is occupied by player

                # Update the player's position
                self.pos_X, self.pos_Y = new_x, new_y

                # Increment animation timer
                self.frame_timer += 1
                if self.frame_timer >= self.frames_per_step:
                    self.frame_timer = 0
                    # Toggle between frame 0 and 1
                    self.current_frame = (self.current_frame + 1) % 2

                # Update current image based on direction & current frame
                self.current_image = self.images[self.direction][self.current_frame]

    def check_collision(self, new_x, new_y):
        """
        Check if any of the four corners of the 30x30 sprite at (new_x, new_y)
        collides with a blocked tile (0) or is out of bounds.
        """
        # The four corners of the 30x30 sprite:
        corners = [
            (new_x,       new_y),       # top-left
            (new_x + 29,  new_y),       # top-right  (use +29 if sprite is 30 wide)
            (new_x,       new_y + 29),  # bottom-left
            (new_x + 29,  new_y + 29)   # bottom-right
        ]

        for corner_x, corner_y in corners:
            col, row = self.pixel_to_grid((corner_x, corner_y))
            
            # Check out-of-bounds
            if not (0 <= row < len(matrix) and 0 <= col < len(matrix[0])):
                return True  # Out of bounds => collision

            # Check if blocked
            if matrix[row][col] == 0:
                return True

        return False

    def pixel_to_grid(self, pixel_pos):
        """
        Convert pixel position to matrix coordinates.
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