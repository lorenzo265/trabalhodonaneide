import pygame
from core.config import WIDTH, HEIGHT, FPS
from ui.hud import init_hud_icons
# importe a função
from core.video_player import play_cutscene_fullscreen

def run_game(width, height, fps, starting_scene_factory):
    pygame.init()
    try:
        pygame.mixer.init()
    except Exception:
        pass
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Dona Neide: Manhã do Caos")
    init_hud_icons()

    clock = pygame.time.Clock()
    active_scene = starting_scene_factory()

    while active_scene is not None:
        dt = clock.tick(fps) / 1000.0
        events = pygame.event.get()
        keys = pygame.key.get_pressed()
        for event in events:
            if event.type == pygame.QUIT:
                active_scene = None

        active_scene.process_input(events, keys)
        active_scene.update(dt)
        # Antes de renderizar ou após, verifica se active_scene.request_cutscene
        # Mas normalmente, a cena mesma chama a cutscene.
        active_scene.render(screen)
        pygame.display.flip()

        # Avança cena
        next_scene = active_scene.next_scene
        if next_scene is not active_scene:
            # Se a cena mudou, pode haver atributo para indicar cutscene
            # Por exemplo, se next_scene for uma instância de CutsceneScene, deixe fluir
            # Se a cena atual indicar que precisa tocar vídeo, faça aqui:
            active_scene = next_scene
        # Caso queira que GameScene inicie cutscene, ela mesma chamará play_cutscene_fullscreen
    pygame.quit()
