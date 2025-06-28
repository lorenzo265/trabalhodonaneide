import pygame, sys, os

try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

def play_cutscene_fullscreen(video_path, window_size):
    """
    Reproduz vídeo MP4 em fullscreen e retorna ao jogo ao final ou ao pressionar tecla.
    """
    if not MOVIEPY_AVAILABLE:
        print("MoviePy não está instalado. Pulando cutscene.")
        return

    if not os.path.exists(video_path):
        print(f"Cutscene não encontrada: {video_path}")
        return

    try:
        clip = VideoFileClip(video_path)
    except Exception as e:
        print(f"Erro ao carregar vídeo {video_path}: {e}")
        return

    # Alternar para fullscreen temporariamente
    try:
        screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    except:
        info = pygame.display.Info()
        screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.FULLSCREEN)

    clock = pygame.time.Clock()
    fps = clip.fps or 30

    for frame in clip.iter_frames(fps=fps, dtype="uint8"):
        surf = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        screen.blit(pygame.transform.scale(surf, screen.get_size()), (0, 0))
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                clip.close()
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                clip.close()
                pygame.display.set_mode(window_size)
                return

        clock.tick(fps)

    clip.close()
    pygame.display.set_mode(window_size)