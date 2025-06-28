import pygame, os

_image_cache = {}
def load_image(path, scale=None):
    # Carrega com alpha e faz cache
    if path not in _image_cache:
        img = pygame.image.load(path).convert_alpha()
        _image_cache[path] = img
    else:
        img = _image_cache[path]
    if scale:
        img = pygame.transform.scale(img, scale)
    return img.copy()

def load_images_from_folder(folder, scale=None):
    frames = []
    if not os.path.isdir(folder):
        return frames
    for filename in sorted(os.listdir(folder)):
        if filename.lower().endswith(('.png', '.jpg', '.bmp')):
            full = os.path.join(folder, filename)
            frames.append(load_image(full, scale))
    return frames

_sound_cache = {}

def load_sound(path):
    """
    Carrega um efeito de som (pygame.mixer.Sound) e faz cache.
    Retorna None se arquivo não existir ou houver falha.
    """
    if not os.path.exists(path):
        return None
    if path not in _sound_cache:
        try:
            _sound_cache[path] = pygame.mixer.Sound(path)
        except Exception as e:
            print(f"Warning: falha ao carregar som {path}: {e}")
            return None
    return _sound_cache[path]

def load_music(path):
    """
    Carrega música para pygame.mixer.music; retorna True se ok, False caso não exista ou falha.
    """
    if not os.path.exists(path):
        return False
    try:
        pygame.mixer.music.load(path)
        return True
    except Exception as e:
        print(f"Warning: falha ao carregar música {path}: {e}")
        return False
