import pygame
import random
from core.config import WIDTH, HEIGHT

class Item(pygame.sprite.Sprite):
    def __init__(self, image, tipo, valor, efeito=None, speed_range=(150, 250)):
        super().__init__()
        self.image = image
        self.tipo = tipo
        self.valor = valor
        self.efeito = efeito
        self.speed = random.randint(*speed_range)
        self.rect = self.image.get_rect(
            midtop=(random.randint(0, WIDTH - self.image.get_width()), -self.image.get_height())
        )

    def update(self, dt):
        self.rect.y += self.speed * dt
        if self.rect.top > HEIGHT:
            self.kill()
