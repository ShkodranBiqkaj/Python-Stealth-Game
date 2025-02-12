import pygame
import Player
import math

class Screen_size:
    sizeX = 1100
    sizeY = 750
    size_of_sides = 4
    count_of_parts = math.floor((1100*750)/16)
    #implement what the size of the squares would be in a map


    matrix = {
    (0, 0): [(0, 1), (1, 0)],
    (0, 1): [(0, 0), (0, 2), (1, 1)],
    (0, 2): [(0, 1), (0, 3), (1, 2)],
    (0, 3): [(0, 2), (1, 3)],
    (1, 0): [(1, 1), (0, 0), (2, 0)],
    (1, 1): [(1, 0), (1, 2), (0, 1), (2, 1)],
    (1, 2): [(1, 1), (1, 3), (0, 2), (2, 2)],
    (1, 3): [(1, 2), (0, 3), (2, 3)],
    (2, 0): [(2, 1), (1, 0), (3, 0)],
    (2, 1): [(2, 0), (2, 2), (1, 1), (3, 1)],
    (2, 2): [(2, 1), (2, 3), (1, 2), (3, 2)],
    (2, 3): [(2, 2), (1, 3), (3, 3)],
    (3, 0): [(3, 1), (2, 0)],
    (3, 1): [(3, 0), (3, 2), (2, 1)],
    (3, 2): [(3, 1), (3, 3), (2, 2)],
    (3, 3): [(3, 2), (2, 3)]
    }


class Game:
    def __init__(self):
        self.test = Player.Player()


    def draw_map(self, screen):
        

    def game_loop(self):
        pygame.init()
        screen = pygame.display.set_mode((Screen_size.sizeX, Screen_size.sizeY))
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
            
            pygame.display.flip()
            clock.tick(60)


game = Game()
game.game_loop()