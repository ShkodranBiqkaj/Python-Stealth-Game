# options.py
import pygame
from Graphics.main_menu import SIZE_X,SIZE_Y


class DeveloperOptions:
    """
    Let player pick difficulty, rows, cols, enemy count.
    Controls:
      1/2: easy/hard
      ↑/↓: rows up/down
      →/←: cols up/down
      E/Q: enemy count +/-
      ENTER: confirm (returns the selected settings)
    """
    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.font = pygame.font.SysFont(None, 36)

        # initial settings
        self.maze_difficulty = "hard"
        self.rows            = 8
        self.cols            = 8
        self.enemy_count     = 2


    def draw_developer_options(self):
        #create window & clock
        screen = pygame.display.set_mode((SIZE_X, SIZE_Y))
        pygame.display.set_caption("Maze Options")
        clock  = pygame.time.Clock()
        menu_bg = pygame.transform.scale(
            pygame.image.load("Assets/Menu_sc.png").convert(),
            (SIZE_X, SIZE_Y)
        )


        choosing = True
        while choosing:
            # draw background
            screen.blit(menu_bg, (0, 0))

            # build and render option lines
            opts = [
                f"Maze Difficulty: {self.maze_difficulty} (1=Easy, 2=Hard)",
                f"Maze Rows:       {self.rows}            (Up/Down)",
                f"Maze Cols:       {self.cols}            (Right/Left)",
                f"Enemy Count:     {self.enemy_count}      (E/Q)",
                "",
                "Press ENTER to confirm"
            ]
            for i, line in enumerate(opts):
                txt = self.font.render(line, True, (255, 255, 0))
                screen.blit(txt, (50, 50 + i*40))

            pygame.display.flip()

            #handle input
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_1:
                        self.maze_difficulty = "easy"
                    elif e.key == pygame.K_2:
                        self.maze_difficulty = "hard"
                    elif e.key == pygame.K_UP:
                        self.rows += 1
                    elif e.key == pygame.K_DOWN:
                        self.rows = max(3, self.rows - 1)
                    elif e.key == pygame.K_RIGHT:
                        self.cols += 1
                    elif e.key == pygame.K_LEFT:
                        self.cols = max(3, self.cols - 1)
                    elif e.key == pygame.K_e:
                        self.enemy_count += 1
                    elif e.key == pygame.K_q:
                        self.enemy_count = max(1, self.enemy_count - 1)
                    elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                        choosing = False

            clock.tick(30)

        # return the final settings
        return (self.maze_difficulty,
                self.rows,
                self.cols,
                self.enemy_count)
    

    def update(self, dt):
        pass

    def render(self, surface):
        lines = [
            f"Difficulty: {self.gc.difficulty} (1/2)",
            f"Rows:       {self.gc.rows} (↑/↓)",
            # …
        ]
        surface.fill((0,0,0))
        for i, line in enumerate(lines):
            surf = self.font.render(line, True, (255,255,255))
            surface.blit(surf, (50, 50 + i*40))
