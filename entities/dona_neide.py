import pygame

class DonaNeide(pygame.sprite.Sprite):
    def __init__(self, image, shield_image):
        super().__init__()
        self.image = image
        self.shield_image = shield_image
        self.rect = self.image.get_rect(midbottom=(400, 580))

        # Estados de escudo
        self.shield_active = False
        self.shield_duration = 1.0      # segundos de duração do escudo
        self.shield_timer = 0.0         # tempo desde ativação
        self.shield_cooldown = 5.0      # segundos de recarga
        self.cooldown_timer = 0.0       # tempo restante de recarga

        # Estados de escorregão (banana)
        self.slip_timer = 0.0           # tempo restante do escorregão
        self.slip_duration = 0.5        # duração do efeito de escorregão
        self.can_move = True            # controla se o personagem pode se mover

        # Outros atributos existentes
        self.vida = 3
        self.pontos = 0
        self.speed = 200
        self.boost_timer = 0.0
        self.boost_multiplier = 1.0
        # Para movimentação frame-rate independent
        self.dt = 0.0

    def process_input(self, events, keys):
        # Se estiver escorregando, não processa movimento ou escudo
        if self.slip_timer > 0.0:
            return

        # Tenta ativar escudo
        if keys[pygame.K_SPACE] and not self.shield_active and self.cooldown_timer <= 0.0:
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
        self.dt = dt
        # Atualiza estado de escorregão
        if self.slip_timer > 0.0:
            self.slip_timer -= dt
            if self.slip_timer <= 0.0:
                self.slip_timer = 0.0
                self.can_move = True
        # Processa entrada de usuário
        self.process_input(None, keys)

        # Atualiza estado do escudo
        if self.shield_active:
            self.shield_timer += dt
            # Quando duração termina, desativa e inicia recarga
            if self.shield_timer >= self.shield_duration:
                self.shield_active = False
                self.cooldown_timer = self.shield_cooldown
        else:
            # Atualiza recarga
            if self.cooldown_timer > 0.0:
                self.cooldown_timer -= dt
                if self.cooldown_timer < 0.0:
                    self.cooldown_timer = 0.0

        # Atualiza boost de velocidade se houver
        if self.boost_timer > 0.0:
            self.boost_timer -= dt
            if self.boost_timer <= 0.0:
                self.boost_multiplier = 1.0

    def boost_speed(self, multiplier=1.5, duration=6.0):
        self.boost_multiplier = multiplier
        self.boost_timer = duration

    def escorregar(self):
        # Ativa efeito de escorregão: bloqueia movimento por slip_duration
        self.slip_timer = self.slip_duration
        self.can_move = False

    def draw(self, screen):
        # Desenha a imagem do escudo ou sem escudo
        if self.shield_active and self.shield_image:
            screen.blit(self.shield_image, self.rect)
        else:
            screen.blit(self.image, self.rect)