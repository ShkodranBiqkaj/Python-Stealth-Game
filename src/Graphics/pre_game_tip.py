import pygame
import time

class PreGameTip:
    """
    Display “Press SPACE to pause or get help” centered on screen for 'duration' seconds,
    then return.
    """
    def __init__(self, surface, font=None, duration=1.0):
        self.surface  = surface
        self.duration = duration
        self.font     = font or pygame.font.SysFont(None, 36)

    def show(self):
        start = time.time()
        message = "Press SPACE to pause"
        txt = self.font.render(message, True, (255,255,255))
        rect = txt.get_rect(center=(self.surface.get_width()//2,
                                     self.surface.get_height()//2))

        # Loop until time’s up
        while time.time() - start < self.duration:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    exit()

            self.surface.fill((0,0,0))
            self.surface.blit(txt, rect)
            pygame.display.flip()
            pygame.time.delay(10)
