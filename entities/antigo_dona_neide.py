import pygame

class DonaNeide(pygame.sprite.Sprite):
    def __init__(self, image, shield_image):
        super().__init__()
        self.image = image
        self.shield_image = shield_image
        self.rect = self.image.get_rect(midbottom=(400, 580))  # ajuste conforme necessidade

        # Estados de jogo
        self.shield_active = False
        self.shield_duration = 1.0  # segundos de duração do escudo
        self.shield_timer = 0.0

        # Outros atributos existentes
        self.vida = 3
        self.pontos = 0
        self.speed = 200
        self.boost_timer = 0.0
        self.boost_multiplier = 1.0

    def process_input(self, events, keys):
        # Ativa o escudo com tecla Espaço
        if keys[pygame.K_SPACE] and not self.shield_active:
            self.shield_active = True
            self.shield_timer = 0.0
        # Movimentação horizontal
        dx = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -1
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = 1
        self.rect.x += dx * self.speed * self.boost_multiplier * self.dt
        # Limites de tela
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > 800:
            self.rect.right = 800

    def update(self, keys, dt):
        # Salva dt para usar na movimentação
        self.dt = dt
        # Processa entrada de usuário
        self.process_input(None, keys)

        # Atualiza escudo
        if self.shield_active:
            self.shield_timer += dt
            if self.shield_timer >= self.shield_duration:
                self.shield_active = False

        # Atualiza boost de velocidade se houver
        if self.boost_timer > 0:
            self.boost_timer -= dt
            if self.boost_timer <= 0:
                self.boost_multiplier = 1.0

    def boost_speed(self, multiplier=1.5, duration=6.0):
        self.boost_multiplier = multiplier
        self.boost_timer = duration

    def escorregar(self):
        # Lógica de escorregão (banana)
        # Por exemplo, bloqueia movimento por um breve instante
        pass

    def draw(self, screen):
        # Desenha com escudo ou imagem normal
        if self.shield_active and self.shield_image:
            screen.blit(self.shield_image, self.rect)
        else:
            screen.blit(self.image, self.rect)
