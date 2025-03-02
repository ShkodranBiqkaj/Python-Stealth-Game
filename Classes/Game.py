import pygame
import math
from constants.matrix_sizes import SIZE_X, SIZE_Y, border_tuples
from Player import Player
from Enemy import Enemy

class Game:
    def __init__(self):
        # Initialize Pygame and set up the display BEFORE creating any objects that load images
        pygame.init()
        self.screen = pygame.display.set_mode((SIZE_X, SIZE_Y))
        pygame.display.set_caption("Stealth Game - BFS Enemy")

        # Create a clock for managing the frame rate
        self.clock = pygame.time.Clock()

        # Load background image after display is set
        self.background = pygame.image.load("../Assets/background.jpg").convert()

        # Now that the display is ready, we can create the Player and Enemy
        self.player = Player()
        self.enemy = Enemy(position=(50, 50), move_speed=3, update_interval=1)

    def draw_map(self):
        """
        Draw obstacles using border_tuples.
        You can replace these crate images with any image or color fill.
        """
        crate_image = pygame.image.load("../Assets/walls.png").convert_alpha()

        for (x_start, x_end), (y_start, y_end) in border_tuples:
            width = x_end - x_start
            height = y_end - y_start
            rect = pygame.Rect(math.floor(x_start), math.floor(y_start), width, height)
            # Scale crate image to fit each obstacle cell
            scaled_crate = pygame.transform.scale(crate_image, (int(width), int(height)))
            self.screen.blit(scaled_crate, rect)

    def game_loop(self):
        running = True
        while running:
            # Basic event handling (close window)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Draw background
            self.screen.blit(self.background, (0, 0))

            # Draw obstacles
            self.draw_map()

            # Player logic
            self.player.move()
            player_pos = self.player.get_position()

            # Enemy logic
            self.enemy.move(player_pos)
            enemy_pos = self.enemy.get_position()

            # Draw the player (sprite instead of circle)
            self.player.draw(self.screen)

            # Draw the enemy (green circle)
            pygame.draw.circle(self.screen, (0, 255, 0), (int(enemy_pos[0]), int(enemy_pos[1])), 15)

            # Update the display
            pygame.display.flip()

            # Cap the frame rate at 60 FPS
            self.clock.tick(60)

        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.game_loop()
