import pygame, random
from entities.CaixaMissil import CaixaMissil


class EntregadorTemporal(pygame.sprite.Sprite):
    def __init__(self, image, missile_img, screen_rect, target):
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect(midtop=(screen_rect.centerx, 20))
        self.direction = 1
        self.speed = 100
        self.missile_img = missile_img
        self.screen_rect = screen_rect
        self.missile_timer = 0
        self.missile_interval = 2.0  # segundos
        self.hits_taken = 0
        self.max_hits = 20
        self.dead = False
        self.target = target

    def update(self, dt):
        self.rect.x += self.direction * self.speed * dt
        if self.rect.right > self.screen_rect.right or self.rect.left < self.screen_rect.left:
            self.direction *= -1

        self.missile_timer += dt

    def ready_to_fire(self):
        return self.missile_timer >= self.missile_interval

    def fire_missile(self):
        self.missile_timer = 0
        # passa referência ao jogador
        return CaixaMissil(self.rect.centerx, self.rect.bottom, self.missile_img, self.target)


    def register_hit(self):
        self.hits_taken += 1
        if self.hits_taken >= self.max_hits:
            self.dead = True
        elif self.hits_taken == self.max_hits // 2:
            self.missile_interval = 1.0  # acelera
