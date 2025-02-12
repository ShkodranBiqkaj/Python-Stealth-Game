import pygame

class Player:
    def __init__(self):
        self.pos_X = 0
        self.pos_Y = 0
        self.speed = 10

    def move(self, pos):
        from Game import Screen_size
        pygame.event.pump()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_w]:
            if self.pos_Y - self.speed >= 0:
                self.pos_Y -= self.speed
        if keys[pygame.K_s]:
            if self.pos_Y + self.speed <= Screen_size.sizeY:
                self.pos_Y += self.speed
        if keys[pygame.K_a]:
            if self.pos_X - self.speed >= 0 :
                self.pos_X -= self.speed
        if keys[pygame.K_d]:
            if self.pos_X + self.speed <= Screen_size.sizeX:
                self.pos_X += self.speed

    def get_position(self):
        return (self.pos_X, self.pos_Y)
            