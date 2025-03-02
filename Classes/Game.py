import pygame
import math
from constants.matrix_sizes import SIZE_X, SIZE_Y, border_tuples
from Player import Player
from Enemy import Enemy

class Game:
    def __init__(self):
        self.player = Player()
        # Start enemy near top-left corner, for instance
        self.enemy = Enemy(position=(50, 50), move_speed=3, update_interval=1)

    def draw_map(self, screen):
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
            screen.blit(scaled_crate, rect)

    def game_loop(self):
        pygame.init()
        screen = pygame.display.set_mode((SIZE_X, SIZE_Y))
        pygame.display.set_caption("Stealth Game - BFS Enemy")

        clock = pygame.time.Clock()
        background = pygame.image.load("../Assets/background.jpg").convert()

        running = True
        while running:
            # Basic event handling (close window)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Draw background
            screen.blit(background, (0, 0))

            # Draw obstacles
            self.draw_map(screen)

            # Player logic
            self.player.move()
            player_pos = self.player.get_position()

            # Enemy logic
            self.enemy.move(player_pos)
            enemy_pos = self.enemy.get_position()

            # Draw the player (red circle)
            pygame.draw.circle(screen, (255, 0, 0), (int(player_pos[0]), int(player_pos[1])), 15)

            # Draw the enemy (green circle)
            pygame.draw.circle(screen, (0, 255, 0), (int(enemy_pos[0]), int(enemy_pos[1])), 15)

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.game_loop()
