import pygame, os
from assets.loader import load_image
from core.config import WIDTH

# Carregar ícones uma única vez
# Ajuste caminhos e tamanhos conforme seus sprites:
HEART_ICON = None
SHIELD_ICON = None

def init_hud_icons():
    global HEART_ICON, SHIELD_ICON
    heart_path = os.path.join("assets", "images", "efeitos", "heart.png")
    shield_path = os.path.join("assets", "images", "efeitos", "shield_icon.png")
    if os.path.exists(heart_path):
        HEART_ICON = load_image(heart_path, (32, 32))
    else:
        HEART_ICON = pygame.Surface((32, 32))
        HEART_ICON.fill((255, 0, 0))
    if os.path.exists(shield_path):
        SHIELD_ICON = load_image(shield_path, (32, 32))
    else:
        SHIELD_ICON = pygame.Surface((32, 32))
        SHIELD_ICON.fill((0, 0, 255))

def draw_hud(screen, pontos, vida, shield_available):
    # Desenha um painel semitransparente
    panel_w, panel_h = 200, 70
    panel = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    panel.fill((0, 0, 0, 150))  # RGBA, alpha 150
    screen.blit(panel, (10, 10))

    # Texto de pontos
    font = pygame.font.SysFont(None, 28)
    txt = font.render(f"Pontos: {pontos}", True, (255, 255, 255))
    screen.blit(txt, (20, 20))

    # Ícones de vida
    x = 20
    for i in range(vida):
        screen.blit(HEART_ICON, (x, 45))
        x += HEART_ICON.get_width() + 5

    # Ícone de escudo (mostra se disponível)
    if shield_available:
        screen.blit(SHIELD_ICON, (x + 10, 45))
