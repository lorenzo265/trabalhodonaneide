"""
Sistema robusto de carregamento de recursos para o jogo Dona Neide.
Centraliza o carregamento de imagens, sons e música com tratamento de erros.
"""
import pygame
import os

def load_image(path, size=None, convert_alpha=True):
    """
    Carrega uma imagem com tratamento de erros robusto.
    
    Args:
        path: Caminho para o arquivo de imagem
        size: Tupla (width, height) para redimensionar. None mantém tamanho original
        convert_alpha: Se True, otimiza a imagem para transparência
    
    Returns:
        Surface do pygame ou None se falhar
    """
    try:
        if not os.path.exists(path):
            print(f"Aviso: Imagem não encontrada: {path}")
            return None
            
        # Carrega a imagem
        image = pygame.image.load(path)
        
        # Otimiza para performance
        if convert_alpha:
            image = image.convert_alpha()
        else:
            image = image.convert()
            
        # Redimensiona se necessário
        if size is not None:
            image = pygame.transform.scale(image, size)
            
        return image
        
    except pygame.error as e:
        print(f"Erro ao carregar imagem {path}: {e}")
        return None
    except Exception as e:
        print(f"Erro inesperado ao carregar imagem {path}: {e}")
        return None

def load_sound(path, volume=1.0):
    """
    Carrega um arquivo de som com tratamento de erros.
    
    Args:
        path: Caminho para o arquivo de som
        volume: Volume inicial (0.0 a 1.0)
    
    Returns:
        Sound object do pygame ou None se falhar
    """
    try:
        if not os.path.exists(path):
            print(f"Aviso: Som não encontrado: {path}")
            return None
            
        sound = pygame.mixer.Sound(path)
        sound.set_volume(volume)
        return sound
        
    except pygame.error as e:
        print(f"Erro ao carregar som {path}: {e}")
        return None
    except Exception as e:
        print(f"Erro inesperado ao carregar som {path}: {e}")
        return None

def load_music(path):
    """
    Carrega música de fundo.
    
    Args:
        path: Caminho para o arquivo de música
    
    Returns:
        True se carregou com sucesso, False caso contrário
    """
    try:
        if not os.path.exists(path):
            print(f"Aviso: Música não encontrada: {path}")
            return False
            
        pygame.mixer.music.load(path)
        return True
        
    except pygame.error as e:
        print(f"Erro ao carregar música {path}: {e}")
        return False
    except Exception as e:
        print(f"Erro inesperado ao carregar música {path}: {e}")
        return False

def create_placeholder_surface(size, color=(255, 0, 255)):
    """
    Cria uma superfície placeholder quando um recurso não pode ser carregado.
    
    Args:
        size: Tupla (width, height)
        color: Cor RGB, padrão é magenta para fácil identificação
    
    Returns:
        Surface do pygame
    """
    surface = pygame.Surface(size)
    surface.fill(color)
    return surface

def preload_game_assets():
    """
    Pré-carrega todos os assets do jogo para verificar integridade.
    Útil para debugging e validação durante desenvolvimento.
    
    Returns:
        Dict com status do carregamento de cada asset
    """
    assets_status = {
        'images': {},
        'sounds': {},
        'music': {}
    }
    
    # Define todos os caminhos de assets esperados
    image_paths = {
        'background': 'assets/images/fundos/cozinha.png',
        'player': 'assets/images/personagens/neide_img.png',
        'shield': 'assets/images/efeitos/veia_panescudo.png',
        'heart': 'assets/images/efeitos/heart.png',
        'shield_icon': 'assets/images/efeitos/shield_icon.png',
        'boss': 'assets/images/chefes/entregador_temporal.png',
        'missile': 'assets/images/efeitos/caixa_missil.png',
        'item_meia': 'assets/images/itens/item_0.png',
        'item_cubo': 'assets/images/itens/item_1.png',
        'item_caneca': 'assets/images/itens/item_2.png',
        'item_toalha': 'assets/images/itens/item_3.png',
        'banana': 'assets/images/itens/banana.png'
    }
    
    sound_paths = {
        'catch': 'assets/audio/catch.wav',
        'explosion': 'assets/audio/explosions.wav',
        'hit': 'assets/audio/hit.wav',
        'lose_life': 'assets/audio/lose_life.wav',
        'missile': 'assets/audio/missile_launch.wav',
        'shield': 'assets/audio/shield.wav',
        'shot': 'assets/audio/shot.wav',
        'levelup': 'assets/audio/levelup.wav'
    }
    
    music_paths = {
        'background': 'assets/audio/background_music.mp3',
        'boss': 'assets/audio/boss_music.wav'
    }
    
    # Testa carregamento de imagens
    for name, path in image_paths.items():
        image = load_image(path)
        assets_status['images'][name] = {
            'path': path,
            'loaded': image is not None,
            'exists': os.path.exists(path)
        }
    
    # Testa carregamento de sons
    for name, path in sound_paths.items():
        sound = load_sound(path)
        assets_status['sounds'][name] = {
            'path': path,
            'loaded': sound is not None,
            'exists': os.path.exists(path)
        }
    
    # Testa carregamento de música
    for name, path in music_paths.items():
        loaded = load_music(path) if os.path.exists(path) else False
        assets_status['music'][name] = {
            'path': path,
            'loaded': loaded,
            'exists': os.path.exists(path)
        }
    
    return assets_status

def print_assets_report():
    """
    Imprime um relatório detalhado sobre o status de todos os assets.
    Útil para debugging durante desenvolvimento.
    """
    status = preload_game_assets()
    
    print("=" * 60)
    print("RELATÓRIO DE ASSETS - DONA NEIDE: MANHÃ DO CAOS")
    print("=" * 60)
    
    for category, assets in status.items():
        print(f"\n{category.upper()}:")
        print("-" * 30)
        
        for name, info in assets.items():
            status_icon = "✓" if info['loaded'] else "✗"
            exists_icon = "📁" if info['exists'] else "❌"
            print(f"{status_icon} {exists_icon} {name}: {info['path']}")
    
    print("\n" + "=" * 60)
    print("Legenda: ✓=Carregado ✗=Falha 📁=Arquivo existe ❌=Arquivo não encontrado")
    print("=" * 60)

# Inicialização automática para verificar pygame
try:
    if not pygame.get_init():
        pygame.init()
        pygame.mixer.init()
except Exception as e:
    print(f"Aviso: Erro na inicialização do pygame: {e}")