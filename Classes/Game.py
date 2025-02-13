import pygame
import Player
import math
from constants.matrix_sizes import *

class Game:
    def __init__(self):
        self.test = Player.Player()

    def draw_map(self, screen):
        pygame.event.pump()
        for start_X, start_Y in border_tuples:
            pygame.draw.rect(screen, BROWN, (int(start_X), int(start_Y), int(PIXEL_ONE_X), int(PIXEL_ONE_Y)))

    def game_loop(self):
        pygame.init()
        screen = pygame.display.set_mode((SIZE_X, SIZE_Y))
        clock = pygame.time.Clock()
        player_pos = (100,100)
        running = True
        pygame.draw.circle(screen, "red", player_pos, 20)
        while running:
            pygame.event.pump()
            screen.fill("blue")
            self.test.move(player_pos)
            pygame.draw.circle(screen, "red", player_pos, 20)
            player_pos = self.test.get_position()
            self.draw_map(screen)
            self.test.move(player_pos)
            pygame.draw.circle(screen, "red", player_pos, 20)
            
            pygame.display.flip()
            clock.tick(60)


game = Game()
game.game_loop()