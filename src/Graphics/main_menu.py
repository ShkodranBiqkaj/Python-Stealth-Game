import pygame
global SIZE_X
global SIZE_Y 
SIZE_X, SIZE_Y = 1000, 750

class Main_Menu:
    def __init__(self):
        pygame.init()
        pygame.font.init()
        self.font = pygame.font.SysFont(None, 48)
        self.labels = ("NEW GAME", "DEVELOPER MODE", "QUIT")
        self.game_state = 0

    def show_main_menu(self) -> int:
        """
        Display the main menu and return:
          0 for NEW GAME,
          1 for DEVELOPER MODE,
          2 for QUIT.
        """
        pygame.init()
        screen = pygame.display.set_mode((SIZE_X, SIZE_Y))
        pygame.display.set_caption("Stealth Game")
        clock = pygame.time.Clock()

        choice   = 0
        n_labels = len(self.labels)

        # load & scale your background once
        menu_bg = pygame.transform.scale(
            pygame.image.load("Assets/Menu_sc.png").convert(),
            (SIZE_X, SIZE_Y)
        )

        running = True
        while running:
            screen.blit(menu_bg, (0, 0))
            for i, lbl in enumerate(self.labels):
                color = (255,255,0) if i == choice else (255,255,255)
                txt = self.font.render(lbl, True, color)
                rect = txt.get_rect(center=(SIZE_X//2, 300 + i*60))
                screen.blit(txt, rect)
            pygame.display.flip()

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    return 2
                if e.type == pygame.KEYDOWN:
                    if e.key in (pygame.K_UP, pygame.K_w):
                        choice = (choice - 1) % n_labels
                    elif e.key in (pygame.K_DOWN, pygame.K_s):
                        choice = (choice + 1) % n_labels
                    elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                        return choice
            clock.tick(30)

    def get_state(self):
        return self.game_state

