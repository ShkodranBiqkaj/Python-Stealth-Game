import pygame
import math
from constants.matrix_sizes import SIZE_X, SIZE_Y, border_tuples, player_start_x, player_start_y, matrix, GRID_COLS, GRID_ROWS, PIXEL_ONE_X, PIXEL_ONE_Y
from Player import Player
from Enemy import Enemy

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SIZE_X, SIZE_Y))
        pygame.display.set_caption("Stealth Game - BFS Enemy")
        self.clock = pygame.time.Clock()
        self.background = pygame.image.load("../Assets/background.jpg").convert()
        self.player = Player(player_start_x, player_start_y)
        # Define the patrol area in pixel coordinates.
        # For example, to patrol the left half of the screen:
        # (x_min, y_min, x_max, y_max) = (0, 0, (GRID_COLS/2)*PIXEL_ONE_X, GRID_ROWS*PIXEL_ONE_Y)
        self.level = 2
        self.enemies = []

    def draw_map(self):
        crate_image = pygame.image.load("../Assets/walls.png").convert_alpha()
        for (x_start, x_end), (y_start, y_end) in border_tuples:
            width = x_end - x_start
            height = y_end - y_start
            rect = pygame.Rect(math.floor(x_start), math.floor(y_start), width, height)
            scaled_crate = pygame.transform.scale(crate_image, (int(width), int(height)))
            self.screen.blit(scaled_crate, rect)

    def level_changes(self):
        unit = PIXEL_ONE_X*GRID_COLS/self.level
        for i in range(self.level):
            # x min, y min, x max, y max
            patrolling_area = (i*unit, 0, (i+1)*(unit), GRID_ROWS * PIXEL_ONE_Y)
            self.enemies.append(Enemy((i*unit, 30), patrolling_area, move_speed=3, update_interval=1))
            print(patrolling_area)

    def game_loop(self):
        running = True
        self.level_changes()
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            self.screen.blit(self.background, (0, 0))
            self.draw_map()

            self.player.move()
            player_pos = self.player.get_position()

            # Update the enemy behavior (patrol or chase based on stimulus)
            for e in range(len(self.enemies)):
                self.enemies[e].update(player_pos)


            self.player.draw(self.screen)
            for e in range(len(self.enemies)):
                self.enemies[e].draw(self.screen)


            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.game_loop()