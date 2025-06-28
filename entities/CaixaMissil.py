import pygame
import math

class CaixaMissil(pygame.sprite.Sprite):
    def __init__(self, x, y, image, target, speed=300):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(midtop=(x, y))
        self.target = target
        self.speed = speed

    def update(self, dt):
        # calcula vetor direção até o alvo
        dir_x = self.target.rect.centerx - self.rect.centerx
        dir_y = self.target.rect.centery - self.rect.centery
        dist = math.hypot(dir_x, dir_y)
        if dist != 0:
            dir_x /= dist
            dir_y /= dist
        # move em direção ao alvo
        self.rect.x += dir_x * self.speed * dt
        self.rect.y += dir_y * self.speed * dt

        # remover se sair da tela
        if (self.rect.top > 600 or self.rect.bottom < 0 or
            self.rect.left > 800 or self.rect.right < 0):
            self.kill()
