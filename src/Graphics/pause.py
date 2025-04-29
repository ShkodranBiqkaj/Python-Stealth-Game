import pygame

class Pause:
    """
    Freezes whatever’s currently on `surface` and draws a translucent help box on top.
    Press SPACE to resume or Q to quit to main menu.
    """
    def __init__(self, surface, help_lines=None, font=None):
        self.surface    = surface
        self.font       = font or pygame.font.SysFont(None, 28)
        self.help_lines = help_lines or [
            "GAME PAUSED",
            "",
            "SPACE : Resume",
            "W/A/S/D : Movement",
            "Q     : Quit to menu",
            "Tip: the door shapes on the walls are hidden rooms that the enemies won't see you in!"
        ]
        self.show_help = True

    def draw_pause(self):
        clock = pygame.time.Clock()

        # Just draw overlay once on top of the current frame
        overlay = pygame.Surface(self.surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))  # translucent black

        while True:
            #Event handling 
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    exit()
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_SPACE:
                        return  # resume
                    if e.key == pygame.K_h:
                        self.show_help = not self.show_help
                    if e.key == pygame.K_q:
                        raise KeyboardInterrupt("Quit to menu")

            # Draw overlay ( screen beneath stays unchanged) 
            self.surface.blit(overlay, (0,0))

            #Draw help text on top
            if self.show_help:
                for i, line in enumerate(self.help_lines):
                    txt = self.font.render(line, True, (255,255,255))
                    self.surface.blit(txt, (50, 50 + i*30))

            pygame.display.flip()
            clock.tick(30)
