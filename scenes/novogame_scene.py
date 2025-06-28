import pygame
import os
import random
import math
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from core.config import WIDTH, HEIGHT
from entities.dona_neide import DonaNeide
from entities.item import Item
from ui.hud import draw_hud
from assets.loader import load_image, load_sound, load_music, create_placeholder_surface
from entities.entregador_temporal import EntregadorTemporal
from entities.CaixaMissil import CaixaMissil

class GameState(Enum):
    """Estados possíveis do jogo para melhor controle de fluxo."""
    PLAYING = "playing"
    PAUSED = "paused"
    TRANSITIONING = "transitioning"
    BOSS_FIGHT = "boss_fight"
    GAME_OVER = "game_over"
    VICTORY = "victory"

class Particle:
    """Classe individual para uma partícula com física simples."""
    
    def __init__(self, x: float, y: float, vx: float, vy: float, 
                 color: Tuple[int, int, int], life: float, size: int = 3):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.life = life
        self.max_life = life
        self.size = size
        self.gravity = 200.0
    
    def update(self, dt: float) -> bool:
        """Atualiza a partícula. Retorna False se deve ser removida."""
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += self.gravity * dt
        self.life -= dt
        return self.life > 0
    
    def render(self, screen: pygame.Surface):
        """Renderiza a partícula com fade baseado na vida."""
        if self.life <= 0:
            return
        
        alpha = int(255 * (self.life / self.max_life))
        current_size = max(1, int(self.size * (self.life / self.max_life)))
        
        # Cria surface temporária com alpha
        temp_surf = pygame.Surface((current_size * 2, current_size * 2))
        temp_surf.set_alpha(alpha)
        temp_surf.fill(self.color)
        
        screen.blit(temp_surf, (int(self.x - current_size), int(self.y - current_size)))

class ParticleSystem:
    """Sistema avançado de partículas para efeitos visuais impressionantes."""
    
    def __init__(self):
        self.particles: List[Particle] = []
        self.max_particles = 200  # Limite para performance
    
    def add_explosion(self, pos: Tuple[int, int], color: Tuple[int, int, int] = (255, 255, 0),
                     particle_count: int = 15, intensity: float = 1.0):
        """Adiciona uma explosão de partículas com física realista."""
        for _ in range(particle_count):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(50, 150) * intensity
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - random.uniform(20, 50)  # Bias para cima
            
            life = random.uniform(0.5, 1.5)
            size = random.randint(2, 5)
            
            # Variação sutil na cor
            r = max(0, min(255, color[0] + random.randint(-30, 30)))
            g = max(0, min(255, color[1] + random.randint(-30, 30)))
            b = max(0, min(255, color[2] + random.randint(-30, 30)))
            
            particle = Particle(pos[0], pos[1], vx, vy, (r, g, b), life, size)
            self.particles.append(particle)
    
    def add_collect_effect(self, pos: Tuple[int, int], color: Tuple[int, int, int] = (0, 255, 0)):
        """Efeito especial para coleta de itens."""
        for i in range(8):
            angle = (i / 8) * 2 * math.pi
            speed = 80
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            
            particle = Particle(pos[0], pos[1], vx, vy, color, 0.8, 4)
            self.particles.append(particle)
    
    def add_trail(self, pos: Tuple[int, int], velocity: Tuple[float, float], 
                  color: Tuple[int, int, int] = (255, 255, 255)):
        """Adiciona rastro de movimento."""
        # Adiciona partícula de rastro baseada na velocidade
        vx = -velocity[0] * 0.3 + random.uniform(-20, 20)
        vy = -velocity[1] * 0.3 + random.uniform(-20, 20)
        
        particle = Particle(pos[0], pos[1], vx, vy, color, 0.3, 2)
        self.particles.append(particle)
    
    def update(self, dt: float):
        """Atualiza todas as partículas e remove as mortas."""
        self.particles = [p for p in self.particles if p.update(dt)]
        
        # Limita número de partículas para performance
        if len(self.particles) > self.max_particles:
            self.particles = self.particles[-self.max_particles:]
    
    def render(self, screen: pygame.Surface):
        """Renderiza todas as partículas ativas."""
        for particle in self.particles:
            particle.render(screen)
    
    def clear(self):
        """Limpa todas as partículas."""
        self.particles.clear()

class PowerUpManager:
    """Gerenciador de power-ups temporários para adicionar depth ao gameplay."""
    
    def __init__(self):
        self.active_powerups: Dict[str, float] = {}
        self.powerup_effects = {
            "double_points": {"duration": 10.0, "description": "Pontos Dobrados"},
            "slow_motion": {"duration": 8.0, "description": "Câmera Lenta"},
            "invincibility": {"duration": 5.0, "description": "Invencibilidade"},
            "magnet": {"duration": 12.0, "description": "Ímã de Itens"}
        }
    
    def activate_powerup(self, powerup_type: str):
        """Ativa um power-up por tempo determinado."""
        if powerup_type in self.powerup_effects:
            duration = self.powerup_effects[powerup_type]["duration"]
            self.active_powerups[powerup_type] = duration
    
    def update(self, dt: float):
        """Atualiza temporizadores dos power-ups."""
        expired = []
        for powerup, time_left in self.active_powerups.items():
            time_left -= dt
            if time_left <= 0:
                expired.append(powerup)
            else:
                self.active_powerups[powerup] = time_left
        
        for powerup in expired:
            del self.active_powerups[powerup]
    
    def is_active(self, powerup_type: str) -> bool:
        """Verifica se um power-up está ativo."""
        return powerup_type in self.active_powerups
    
    def get_time_remaining(self, powerup_type: str) -> float:
        """Retorna tempo restante de um power-up."""
        return self.active_powerups.get(powerup_type, 0.0)

class ComboSystem:
    """Sistema de combos para recompensar jogadas consecutivas."""
    
    def __init__(self):
        self.current_combo = 0
        self.max_combo = 0
        self.combo_timer = 0.0
        self.combo_timeout = 3.0  # Tempo para combo expirar
        self.multipliers = {
            5: 1.2,   # 5+ combo = 20% bonus
            10: 1.5,  # 10+ combo = 50% bonus
            20: 2.0,  # 20+ combo = 100% bonus
            50: 3.0   # 50+ combo = 200% bonus
        }
    
    def add_hit(self) -> Tuple[int, float]:
        """Adiciona um hit ao combo. Retorna (combo_atual, multiplicador)."""
        self.current_combo += 1
        self.max_combo = max(self.max_combo, self.current_combo)
        self.combo_timer = self.combo_timeout
        
        return self.current_combo, self.get_multiplier()
    
    def reset_combo(self):
        """Reseta o combo atual."""
        self.current_combo = 0
        self.combo_timer = 0.0
    
    def update(self, dt: float):
        """Atualiza timer do combo."""
        if self.current_combo > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.reset_combo()
    
    def get_multiplier(self) -> float:
        """Retorna o multiplicador atual baseado no combo."""
        for threshold in sorted(self.multipliers.keys(), reverse=True):
            if self.current_combo >= threshold:
                return self.multipliers[threshold]
        return 1.0

@dataclass
class GameStats:
    """Estatísticas avançadas da sessão de jogo."""
    items_collected: int = 0
    items_missed: int = 0
    damage_taken: int = 0
    shields_used: int = 0
    max_combo: int = 0
    time_played: float = 0.0
    levels_completed: int = 0
    bosses_defeated: int = 0
    
    def accuracy(self) -> float:
        """Calcula precisão de coleta."""
        total = self.items_collected + self.items_missed
        return (self.items_collected / total * 100) if total > 0 else 0.0

class GameScene:
    """
    Cena principal do jogo massivamente expandida e otimizada.
    Inclui sistemas avançados de partículas, combos, power-ups e estatísticas.
    """
    
    def __init__(self, level=1):
        """
        Inicializa uma nova cena de jogo com sistemas avançados.
        
        Args:
            level: Nível inicial do jogo (padrão: 1)
        """
        self.next_scene = self
        self.game_state = GameState.TRANSITIONING
        
        # Sistemas avançados
        self.particle_system = ParticleSystem()
        self.powerup_manager = PowerUpManager()
        self.combo_system = ComboSystem()
        self.stats = GameStats()
        
        # Carrega background com variações por nível
        self._initialize_backgrounds()
        
        # Inicializa personagem principal com tratamento de erro robusto
        self._initialize_player()
        
        # Configura sistema de itens expandido
        self._initialize_enhanced_item_system()
        
        # Configura áudio com mixagem profissional
        self._initialize_enhanced_audio()
        
        # Configurações de progressão e dificuldade adaptativa
        self.level = level
        self.max_level = 12  # Expandido para mais conteúdo
        self.points_to_next = {
            1: 10, 2: 25, 3: 50, 4: 140, 5: 200, 
            6: 280, 7: 380, 8: 500, 9: 650, 
            10: 820, 11: 1000, 12: 1200
        }
        self._setup_enhanced_level_configurations()
        
        # Inicializa estado do jogo com grupos organizados
        self.items = pygame.sprite.Group()
        self.special_effects = pygame.sprite.Group()
        self.ui_elements = pygame.sprite.Group()
        
        # Sistema de câmera e efeitos visuais
        self.camera_shake = 0.0
        self.time_scale = 1.0  # Para efeito de slow motion
        self.screen_flash = 0.0
        
        # Carrega configurações do nível
        self.load_level(self.level)
        self.play_level_music(self.level)
        
        # Sistema de transição melhorado
        self.in_transition = True
        self.transition_timer = 0.0
        self.transition_duration = 2.5
        self.transition_type = "fade_in"
        
        # Controle de dificuldade adaptativa
        self.difficulty_scaling = 1.0
        self.performance_tracker = []
        
        # Debug e estatísticas expandidas
        self.frame_count = 0
        self.total_items_spawned = 0
        self.fps_counter = 0
        self.fps_timer = 0.0
        
        # Sistema de pause melhorado
        self.pause_overlay = None
        self.pause_menu_selection = 0
        
        # Sistema de checkpoints e save
        self.checkpoint_data = {}
        self.auto_save_timer = 0.0
        self.auto_save_interval = 30.0  # Salva a cada 30 segundos

    def _initialize_backgrounds(self):
        """Inicializa backgrounds variados baseados no nível atual."""
        self.backgrounds = {}
        background_variants = {
            "cozinha": "fundos/cozinha.png",
            "sala": "fundos/sala.png", 
            "quintal": "fundos/quintal.png",
            "espacial": "fundos/espaco.png"
        }
        
        # Carrega todas as variações de background
        for variant, filename in background_variants.items():
            bg_path = os.path.join("assets", "images", filename)
            bg_img = load_image(bg_path, (WIDTH, HEIGHT))
            if bg_img is None:
                # Cria background procedural baseado no tema
                bg_img = self._create_procedural_background(variant)
            self.backgrounds[variant] = bg_img
        
        # Define background atual baseado no nível
        if self.level <= 3:
            self.current_bg = "cozinha"
        elif self.level <= 6:
            self.current_bg = "sala"
        elif self.level <= 9:
            self.current_bg = "quintal"
        else:
            self.current_bg = "espacial"
            
        self.background = self.backgrounds[self.current_bg]

    def _create_procedural_background(self, theme: str) -> pygame.Surface:
        """Cria background procedural quando arquivo não existe."""
        surf = pygame.Surface((WIDTH, HEIGHT))
        
        if theme == "cozinha":
            # Gradiente azul claro para branco (tema cozinha)
            for y in range(HEIGHT):
                ratio = y / HEIGHT
                r = int(135 + (255 - 135) * ratio)
                g = int(206 + (255 - 206) * ratio)
                b = int(250)
                pygame.draw.line(surf, (r, g, b), (0, y), (WIDTH, y))
                
        elif theme == "sala":
            # Gradiente marrom claro
            for y in range(HEIGHT):
                ratio = y / HEIGHT
                r = int(210 + (245 - 210) * ratio)
                g = int(180 + (220 - 180) * ratio)
                b = int(140 + (180 - 140) * ratio)
                pygame.draw.line(surf, (r, g, b), (0, y), (WIDTH, y))
                
        elif theme == "quintal":
            # Gradiente verde
            for y in range(HEIGHT):
                ratio = y / HEIGHT
                r = int(144 + (200 - 144) * ratio)
                g = int(238 + (255 - 238) * ratio)
                b = int(144 + (200 - 144) * ratio)
                pygame.draw.line(surf, (r, g, b), (0, y), (WIDTH, y))
                
        else:  # espacial
            # Gradiente escuro com estrelas
            surf.fill((20, 20, 40))
            for _ in range(50):
                x = random.randint(0, WIDTH)
                y = random.randint(0, HEIGHT)
                pygame.draw.circle(surf, (255, 255, 255), (x, y), 1)
        
        return surf

    def _initialize_player(self):
        """Inicializa o personagem principal com tratamento robusto de erros."""
        neide_path = os.path.join("assets", "images", "personagens", "neide_img.png")
        shield_path = os.path.join("assets", "images", "efeitos", "veia_panescudo.png")
        
        # Carrega imagens com fallback melhorado
        neide_img = load_image(neide_path, (64, 64))
        if neide_img is None:
            neide_img = self._create_character_placeholder((64, 64))
            
        shield_img = load_image(shield_path, (64, 64))
        if shield_img is None:
            shield_img = self._create_shield_placeholder((64, 64))
        
        self.player = DonaNeide(neide_img, shield_img)
        self.player_group = pygame.sprite.GroupSingle(self.player)

    def _create_character_placeholder(self, size: Tuple[int, int]) -> pygame.Surface:
        """Cria placeholder visual melhorado para o personagem."""
        surf = pygame.Surface(size, pygame.SRCALPHA)
        center_x, center_y = size[0] // 2, size[1] // 2
        
        # Corpo (círculo rosa)
        pygame.draw.circle(surf, (255, 200, 200), (center_x, center_y), center_x - 5)
        # Rosto (círculo menor)
        pygame.draw.circle(surf, (255, 220, 220), (center_x, center_y - 10), center_x - 15)
        # Olhos
        pygame.draw.circle(surf, (0, 0, 0), (center_x - 8, center_y - 15), 3)
        pygame.draw.circle(surf, (0, 0, 0), (center_x + 8, center_y - 15), 3)
        
        return surf

    def _create_shield_placeholder(self, size: Tuple[int, int]) -> pygame.Surface:
        """Cria placeholder visual para o escudo."""
        surf = pygame.Surface(size, pygame.SRCALPHA)
        center_x, center_y = size[0] // 2, size[1] // 2
        
        # Escudo semi-transparente azul
        pygame.draw.circle(surf, (100, 150, 255, 128), (center_x, center_y), center_x - 2)
        pygame.draw.circle(surf, (150, 200, 255, 80), (center_x, center_y), center_x - 8)
        
        return surf

    def _initialize_enhanced_item_system(self):
        """Configura sistema de itens expandido com novos tipos e mecânicas."""
        self.item_definitions = {
            "meia": {
                "filename": "item_0.png", "valor": 1, "size": (100, 100),
                "efeito": None, "weight": 35, "particles": True,
                "description": "Meia básica - 1 ponto"
            },
            "cubo": {
                "filename": "item_1.png", "valor": 10, "size": (100, 100),
                "efeito": None, "weight": 20, "particles": True,
                "description": "Cubo valioso - 10 pontos"
            },
            "caneca": {
                "filename": "item_2.png", "valor": 5, "size": (68, 68),
                "efeito": None, "weight": 25, "particles": True,
                "description": "Caneca útil - 5 pontos"
            },
            "banana": {
                "filename": "banana.png", "valor": -1, "size": (40, 40),
                "efeito": "escorregar", "weight": 12, "particles": False,
                "description": "Banana escorregadia - cuidado!"
            },
            "toalha": {
                "filename": "item_3.png", "valor": 0, "size": (38, 38),
                "efeito": "boost", "weight": 8, "particles": True,
                "description": "Toalha mágica - velocidade aumentada"
            },
            # Novos itens especiais
            "estrela": {
                "filename": "estrela.png", "valor": 20, "size": (50, 50),
                "efeito": "double_points", "weight": 3, "particles": True,
                "description": "Estrela rara - pontos dobrados!"
            },
            "relógio": {
                "filename": "relogio.png", "valor": 0, "size": (45, 45),
                "efeito": "slow_motion", "weight": 2, "particles": True,
                "description": "Relógio temporal - câmera lenta"
            },
            "coração": {
                "filename": "coracao.png", "valor": 0, "size": (40, 40),
                "efeito": "heal", "weight": 4, "particles": True,
                "description": "Coração curativo - restaura vida"
            }
        }
        
        # Carrega todas as imagens de itens com placeholders melhorados
        self.item_images = {}
        for tipo, data in self.item_definitions.items():
            path = os.path.join("assets", "images", "itens", data["filename"])
            img = load_image(path, data["size"])
            if img is None:
                img = self._create_item_placeholder(tipo, data["size"])
            
            self.item_images[tipo] = {
                "image": img,
                "valor": data["valor"],
                "efeito": data["efeito"],
                "weight": data["weight"],
                "particles": data.get("particles", False),
                "description": data.get("description", "")
            }

    def _create_item_placeholder(self, item_type: str, size: Tuple[int, int]) -> pygame.Surface:
        """Cria placeholders visuais distintos para cada tipo de item."""
        surf = pygame.Surface(size, pygame.SRCALPHA)
        center_x, center_y = size[0] // 2, size[1] // 2
        radius = min(center_x, center_y) - 5
        
        color_map = {
            "meia": (200, 200, 200),      # Cinza
            "cubo": (255, 215, 0),        # Dourado
            "caneca": (139, 69, 19),      # Marrom
            "banana": (255, 255, 0),      # Amarelo
            "toalha": (255, 255, 255),    # Branco
            "estrela": (255, 20, 147),    # Rosa choque
            "relógio": (75, 0, 130),      # Índigo
            "coração": (255, 0, 0)        # Vermelho
        }
        
        color = color_map.get(item_type, (128, 128, 128))
        
        if item_type == "estrela":
            # Desenha estrela
            points = []
            for i in range(10):
                angle = (i * math.pi) / 5
                r = radius if i % 2 == 0 else radius // 2
                x = center_x + r * math.cos(angle - math.pi/2)
                y = center_y + r * math.sin(angle - math.pi/2)
                points.append((x, y))
            pygame.draw.polygon(surf, color, points)
        elif item_type == "coração":
            # Desenha coração (aproximação com círculos)
            pygame.draw.circle(surf, color, (center_x - radius//3, center_y - radius//3), radius//2)
            pygame.draw.circle(surf, color, (center_x + radius//3, center_y - radius//3), radius//2)
            points = [(center_x - radius, center_y), (center_x, center_y + radius), (center_x + radius, center_y)]
            pygame.draw.polygon(surf, color, points)
        else:
            # Forma básica circular com borda
            pygame.draw.circle(surf, color, (center_x, center_y), radius)
            pygame.draw.circle(surf, (255, 255, 255), (center_x, center_y), radius, 3)
        
        return surf

    def _initialize_enhanced_audio(self):
        """Sistema de áudio avançado com mixagem dinâmica e efeitos espaciais."""
        audio_folder = os.path.join("assets", "audio")
        
        # Configuração avançada de sons com categorias e volumes otimizados
        sound_categories = {
            "ui": {
                "sfx_collect": ("catch.wav", 0.6),
                "sfx_levelup": ("levelup.wav", 0.8),
                "sfx_shield": ("shield.wav", 0.7),
            },
            "combat": {
                "sfx_explosion": ("explosions.wav", 0.9),
                "sfx_hit": ("hit.wav", 0.7),
                "sfx_lose_life": ("lose_life.wav", 1.0),
                "sfx_missile": ("missile_launch.wav", 0.8),
                "sfx_shot": ("shot.wav", 0.7),
            },
            "special": {
                "sfx_powerup": ("powerup.wav", 0.8),
                "sfx_combo": ("combo.wav", 0.6),
                "sfx_slow_motion": ("slow_motion.wav", 0.5),
            }
        }
        
        # Carrega todos os sons com fallback inteligente para múltiplos formatos
        self.audio_channels = {}
        for category, sounds in sound_categories.items():
            self.audio_channels[category] = {}
            for attr_name, (filename, volume) in sounds.items():
                sound = self._load_sound_with_fallback(audio_folder, filename, volume)
                setattr(self, attr_name, sound)
                self.audio_channels[category][attr_name] = sound

        # Sistema de mixagem dinâmica
        self.master_volume = 1.0
        self.sfx_volume = 1.0
        self.music_volume = 0.7
        
        # Canal dedicado para efeitos críticos
        try:
            pygame.mixer.set_reserved(1)  # Reserva canal 0 para sons importantes
        except pygame.error:
            pass

    def _load_sound_with_fallback(self, base_path: str, filename: str, volume: float) -> Optional[pygame.mixer.Sound]:
        """Carrega som com múltiplos formatos de fallback e tratamento robusto."""
        sound = None
        # Lista de formatos em ordem de preferência (qualidade vs compatibilidade)
        extensions = [".wav", ".ogg", ".flac", ".mp3"]
        
        # Tenta carregar o arquivo exato primeiro
        full_path = os.path.join(base_path, filename)
        if os.path.exists(full_path):
            try:
                sound = load_sound(full_path)
                if sound:
                    sound.set_volume(volume * self.sfx_volume * self.master_volume)
                return sound
            except pygame.error:
                pass
        
        # Fallback: tenta diferentes extensões
        base_name = os.path.splitext(filename)[0]
        for ext in extensions:
            try_path = os.path.join(base_path, base_name + ext)
            if os.path.exists(try_path):
                try:
                    sound = load_sound(try_path)
                    if sound:
                        sound.set_volume(volume * self.sfx_volume * self.master_volume)
                    return sound
                except pygame.error:
                    continue
        
        # Se não conseguiu carregar nenhum som, retorna None silenciosamente
        return None

    def _setup_enhanced_level_configurations(self):
        """Configurações avançadas de níveis com progressão adaptativa."""
        self.level_configs = {
            1: {
                "spawn_interval": 3.5, "max_items": 4, "speed_multiplier": 1.0,
                "boss": None, "background": "cozinha", "music": "background_music.mp3",
                "special_mechanics": [], "item_weights": {"meia": 50, "cubo": 25, "caneca": 25}
            },
            2: {
                "spawn_interval": 3.0, "max_items": 5, "speed_multiplier": 1.1,
                "boss": None, "background": "cozinha", "music": "background_music.mp3",
                "special_mechanics": ["banana_intro"], "item_weights": {"meia": 40, "cubo": 25, "caneca": 25, "banana": 10}
            },
            3: {
                "spawn_interval": 2.5, "max_items": 6, "speed_multiplier": 1.2,
                "boss": None, "background": "sala", "music": "background_music.mp3",
                "special_mechanics": ["toalha_intro"], "item_weights": {"meia": 35, "cubo": 25, "caneca": 20, "banana": 15, "toalha": 5}
            },
            4: {
                "spawn_interval": 2.0, "max_items": 6, "speed_multiplier": 1.3,
                "boss": "entregador_temporal", "background": "sala", "music": "boss_music.wav",
                "special_mechanics": ["boss_fight"], "item_weights": {"meia": 30, "cubo": 30, "caneca": 25, "banana": 10, "toalha": 5}
            },
            5: {
                "spawn_interval": 2.2, "max_items": 7, "speed_multiplier": 1.4,
                "boss": None, "background": "quintal", "music": "background_music.mp3",
                "special_mechanics": ["estrela_intro"], "item_weights": {"meia": 30, "cubo": 25, "caneca": 20, "banana": 15, "toalha": 8, "estrela": 2}
            },
            6: {
                "spawn_interval": 1.8, "max_items": 7, "speed_multiplier": 1.5,
                "boss": None, "background": "quintal", "music": "background_music.mp3",
                "special_mechanics": ["power_combo"], "item_weights": {"meia": 25, "cubo": 25, "caneca": 20, "banana": 15, "toalha": 10, "estrela": 3, "relógio": 2}
            },
            7: {
                "spawn_interval": 1.5, "max_items": 8, "speed_multiplier": 1.6,
                "boss": None, "background": "quintal", "music": "background_music.mp3",
                "special_mechanics": ["healing"], "item_weights": {"meia": 25, "cubo": 20, "caneca": 20, "banana": 15, "toalha": 10, "estrela": 5, "relógio": 3, "coração": 2}
            },
            8: {
                "spawn_interval": 1.2, "max_items": 8, "speed_multiplier": 1.7,
                "boss": "mega_boss", "background": "espacial", "music": "boss_music.wav",
                "special_mechanics": ["final_boss"], "item_weights": {"meia": 20, "cubo": 25, "caneca": 15, "banana": 20, "toalha": 10, "estrela": 5, "relógio": 3, "coração": 2}
            },
            9: {
                "spawn_interval": 1.0, "max_items": 9, "speed_multiplier": 1.8,
                "boss": None, "background": "espacial", "music": "space_music.mp3",
                "special_mechanics": ["space_physics"], "item_weights": {"meia": 15, "cubo": 30, "caneca": 15, "banana": 15, "toalha": 12, "estrela": 8, "relógio": 3, "coração": 2}
            },
            10: {
                "spawn_interval": 0.9, "max_items": 10, "speed_multiplier": 1.9,
                "boss": None, "background": "espacial", "music": "space_music.mp3",
                "special_mechanics": ["chaos_mode"], "item_weights": {"meia": 15, "cubo": 25, "caneca": 15, "banana": 20, "toalha": 10, "estrela": 8, "relógio": 4, "coração": 3}
            },
            11: {
                "spawn_interval": 0.8, "max_items": 11, "speed_multiplier": 2.0,
                "boss": None, "background": "espacial", "music": "intense_music.mp3",
                "special_mechanics": ["extreme_challenge"], "item_weights": {"meia": 10, "cubo": 30, "caneca": 15, "banana": 25, "toalha": 8, "estrela": 7, "relógio": 3, "coração": 2}
            },
            12: {
                "spawn_interval": 0.7, "max_items": 12, "speed_multiplier": 2.2,
                "boss": "final_boss", "background": "espacial", "music": "final_boss_music.wav",
                "special_mechanics": ["ultimate_challenge"], "item_weights": {"meia": 10, "cubo": 25, "caneca": 10, "banana": 30, "toalha": 10, "estrela": 10, "relógio": 3, "coração": 2}
            }
        }

    def load_level(self, level_num: int):
        """Carrega configurações específicas do nível com recursos avançados."""
        if level_num > self.max_level:
            level_num = self.max_level
        
        config = self.level_configs.get(level_num, self.level_configs[1])
        
        # Aplica configurações básicas
        self.spawn_interval = config["spawn_interval"]
        self.max_items = config["max_items"]
        self.speed_multiplier = config["speed_multiplier"]
        self.current_item_weights = config["item_weights"]
        
        # Configura background
        self.current_bg = config["background"]
        if self.current_bg in self.backgrounds:
            self.background = self.backgrounds[self.current_bg]
        
        # Reset do estado do jogo
        self.spawn_timer = 0.0
        self.items.empty()
        self.particle_system.clear()
        
        # Configura boss se necessário
        self._setup_boss_for_level(level_num, config)
        
        # Aplica mecânicas especiais
        self._apply_special_mechanics(config["special_mechanics"])
        
        # Reset de sistemas
        self.combo_system = ComboSystem()
        self.powerup_manager = PowerUpManager()

    def _setup_boss_for_level(self, level_num: int, config: Dict):
        """Configura boss específico para o nível."""
        boss_type = config.get("boss")
        
        if boss_type == "entregador_temporal":
            boss_img_path = os.path.join("assets", "images", "chefes", "entregador_temporal.png")
            missile_img_path = os.path.join("assets", "images", "efeitos", "caixa_missil.png")
            
            boss_img = load_image(boss_img_path, (100, 80))
            if boss_img is None:
                boss_img = self._create_boss_placeholder("entregador", (100, 80))
            
            missile_img = load_image(missile_img_path, (40, 40))
            if missile_img is None:
                missile_img = self._create_missile_placeholder((40, 40))
            
            self.boss = EntregadorTemporal(
                boss_img, missile_img, 
                pygame.Rect(0, 0, WIDTH, HEIGHT), 
                target=self.player
            )
            self.missiles = pygame.sprite.Group()
            self.game_state = GameState.BOSS_FIGHT
            
        elif boss_type in ["mega_boss", "final_boss"]:
            # Placeholder para bosses futuros
            self.boss = self._create_advanced_boss(boss_type)
            self.missiles = pygame.sprite.Group()
            self.game_state = GameState.BOSS_FIGHT
        else:
            self.boss = None
            self.missiles = None
            self.game_state = GameState.PLAYING

    def _create_boss_placeholder(self, boss_type: str, size: Tuple[int, int]) -> pygame.Surface:
        """Cria placeholder visual para bosses."""
        surf = pygame.Surface(size, pygame.SRCALPHA)
        center_x, center_y = size[0] // 2, size[1] // 2
        
        if boss_type == "entregador":
            # Boss azul com detalhes
            pygame.draw.ellipse(surf, (100, 100, 255), surf.get_rect())
            pygame.draw.ellipse(surf, (150, 150, 255), pygame.Rect(10, 10, size[0]-20, size[1]-20))
            # Olhos vermelhos
            pygame.draw.circle(surf, (255, 0, 0), (center_x - 15, center_y - 10), 5)
            pygame.draw.circle(surf, (255, 0, 0), (center_x + 15, center_y - 10), 5)
        
        return surf

    def _create_missile_placeholder(self, size: Tuple[int, int]) -> pygame.Surface:
        """Cria placeholder para mísseis."""
        surf = pygame.Surface(size, pygame.SRCALPHA)
        center_x, center_y = size[0] // 2, size[1] // 2
        
        # Míssil vermelho com ponta
        pygame.draw.rect(surf, (255, 100, 100), surf.get_rect())
        points = [(center_x, 0), (center_x - 8, 15), (center_x + 8, 15)]
        pygame.draw.polygon(surf, (255, 0, 0), points)
        
        return surf

    def _create_advanced_boss(self, boss_type: str):
        """Placeholder para bosses avançados futuros."""
        # Implementação simplificada para bosses avançados
        return None

    def _apply_special_mechanics(self, mechanics: List[str]):
        """Aplica mecânicas especiais do nível."""
        self.active_mechanics = mechanics
        
        for mechanic in mechanics:
            if mechanic == "banana_intro":
                self.show_tutorial_message("Cuidado com as bananas! Elas te fazem escorregar.")
            elif mechanic == "toalha_intro":
                self.show_tutorial_message("Toalhas te dão velocidade extra!")
            elif mechanic == "estrela_intro":
                self.show_tutorial_message("Estrelas dobram seus pontos!")
            elif mechanic == "space_physics":
                self.gravity_modifier = 0.5  # Gravidade reduzida no espaço
            elif mechanic == "chaos_mode":
                self.chaos_mode_active = True

    def show_tutorial_message(self, message: str):
        """Mostra mensagem tutorial temporária."""
        self.tutorial_message = message
        self.tutorial_timer = 3.0  # Mostra por 3 segundos

    def play_level_music(self, level_num: int):
        """Reproduz música apropriada para o nível."""
        config = self.level_configs.get(level_num, {})
        music_file = config.get("music", "background_music.mp3")
        
        audio_folder = os.path.join("assets", "audio")
        music_path = os.path.join(audio_folder, music_file)
        
        try:
            pygame.mixer.music.fadeout(500)
        except:
            pass
        
        if load_music(music_path):
            pygame.mixer.music.set_volume(self.music_volume * self.master_volume)
            pygame.mixer.music.play(-1)
        else:
            pygame.mixer.music.stop()

    def start_level_transition(self, new_level: int):
        """Inicia transição para novo nível com efeitos visuais."""
        if new_level > self.max_level:
            self.game_state = GameState.VICTORY
            return
        
        # Toca som de level up
        if self.sfx_levelup:
            self.sfx_levelup.play()
        
        # Salva estatísticas do nível
        self.stats.levels_completed += 1
        self.stats.max_combo = max(self.stats.max_combo, self.combo_system.max_combo)
        
        # Reproduz cutscene se existir
        self._play_cutscene_for_transition(self.level, new_level)
        
        # Aplica configurações do novo nível
        self.level = new_level
        self.load_level(new_level)
        self.play_level_music(new_level)
        
        # Configura transição visual
        self.in_transition = True
        self.transition_timer = 0.0
        self.transition_type = "level_up"
        
        # Reposiciona player
        self.player.rect.midbottom = (WIDTH // 2, HEIGHT - 10)
        
        # Efeito de partículas de celebração
        for _ in range(20):
            pos = (random.randint(0, WIDTH), random.randint(0, HEIGHT))
            self.particle_system.add_explosion(pos, (255, 215, 0), 8, 0.8)

    def _play_cutscene_for_transition(self, from_level: int, to_level: int):
        """Reproduz cutscene de transição se disponível."""
        try:
            from core.video_player import play_cutscene_fullscreen
            cutscene_path = os.path.join("assets", "cutscenes", f"nivel_{from_level}_to_{to_level}.mp4")
            if os.path.exists(cutscene_path):
                play_cutscene_fullscreen(cutscene_path, (WIDTH, HEIGHT))
        except ImportError:
            pass  # Módulo de vídeo não disponível

    def process_input(self, events: List[pygame.event.Event], keys: pygame.key.ScalarKeyDict):
        """Processa entrada do usuário com controles avançados."""
        self.events = events
        self.keys = keys
        
        for event in events:
            if event.type == pygame.KEYDOWN:
                self._handle_keydown(event)
            elif event.type == pygame.KEYUP:
                self._handle_keyup(event)

    def _handle_keydown(self, event: pygame.event.Event):
        """Processa teclas pressionadas."""
        if event.key == pygame.K_SPACE:
            self._activate_shield()
        elif event.key == pygame.K_p or event.key == pygame.K_ESCAPE:
            self._toggle_pause()
        elif event.key == pygame.K_r and self.game_state == GameState.GAME_OVER:
            self._restart_game()

    def _handle_keyup(self, event: pygame.event.Event):
        """Processa teclas soltas."""
        pass  # Placeholder para futuras funcionalidades

    def _activate_shield(self):
        """Ativa escudo do player com feedback audiovisual."""
        if not self.player.shield_active and self.player.cooldown_timer <= 0.0:
            if self.sfx_shield:
                self.sfx_shield.play()
            
            # Efeito visual de ativação do escudo
            pos = self.player.rect.center
            self.particle_system.add_collect_effect(pos, (100, 150, 255))
            
            # Pequeno screen shake
            self.camera_shake = 0.2

    def _toggle_pause(self):
        """Alterna estado de pause."""
        if self.game_state == GameState.PLAYING:
            self.game_state = GameState.PAUSED
            pygame.mixer.music.pause()
        elif self.game_state == GameState.PAUSED:
            self.game_state = GameState.PLAYING
            pygame.mixer.music.unpause()

    def _restart_game(self):
        """Reinicia o jogo do nível 1."""
        self.__init__(1)

    def update(self, dt: float):
        """Atualização principal do jogo com todos os sistemas."""
        # Atualiza sistemas independentes do estado
        self._update_independent_systems(dt)
        
        # Processa baseado no estado atual
        if self.game_state == GameState.TRANSITIONING or self.in_transition:
            self._update_transition(dt)
        elif self.game_state == GameState.PAUSED:
            self._update_pause(dt)
        elif self.game_state == GameState.BOSS_FIGHT:
            self._update_boss_fight(dt)
        elif self.game_state == GameState.PLAYING:
            self._update_gameplay(dt)
        elif self.game_state == GameState.GAME_OVER:
            self._update_game_over(dt)

    def _update_independent_systems(self, dt: float):
        """Atualiza sistemas que funcionam independente do estado."""
        # Sistema de partículas
        self.particle_system.update(dt)
        
        # Power-ups
        self.powerup_manager.update(dt)
        
        # Combo system
        self.combo_system.update(dt)
        
        # Estatísticas
        self.stats.time_played += dt
        
        # Efeitos visuais
        if self.camera_shake > 0:
            self.camera_shake = max(0, self.camera_shake - dt * 2)
        
        if self.screen_flash > 0:
            self.screen_flash = max(0, self.screen_flash - dt * 3)
        
        # Tutorial timer
        if hasattr(self, 'tutorial_timer') and self.tutorial_timer > 0:
            self.tutorial_timer -= dt
        
        # Auto-save
        self.auto_save_timer += dt
        if self.auto_save_timer >= self.auto_save_interval:
            self._auto_save_progress()
            self.auto_save_timer = 0.0

    def _update_transition(self, dt: float):
        """Atualiza estado de transição."""
        self.transition_timer += dt
        if self.transition_timer >= self.transition_duration:
            self.in_transition = False
            self.game_state = GameState.PLAYING if not self.boss else GameState.BOSS_FIGHT

    def _update_pause(self, dt: float):
        """Atualiza estado de pause."""
        # Pause não atualiza gameplay, apenas sistemas visuais básicos
        pass

    def _update_boss_fight(self, dt: float):
        """Atualiza lógica de luta contra boss."""
        if not self.boss:
            self.game_state = GameState.PLAYING
            return
        
        # Atualiza player
        self.player.update(self.keys, dt * self.time_scale)
        
        # Atualiza boss
        self.boss.update(dt * self.time_scale)
        
        # Atualiza mísseis
        if self.missiles:
            self.missiles.update(dt * self.time_scale)
        
        # Sistema de disparo do boss
        if self.boss.ready_to_fire():
            missile = self.boss.fire_missile()
            if missile and self.missiles:
                self.missiles.add(missile)
                if self.sfx_missile:
                    self.sfx_missile.play()
        
        # Colisões
        self._handle_boss_collisions()
        
        # Verifica se boss foi derrotado
        if self.boss.dead:
            self._handle_boss_defeat()

    def _handle_boss_collisions(self):
        """Gerencia colisões durante luta de boss."""
        if not self.missiles:
            return
        
        # Colisão mísseis vs escudo
        if self.player.shield_active:
            hits = pygame.sprite.spritecollide(self.player, self.missiles, True)
            for hit in hits:
                self.boss.register_hit()
                if self.sfx_shield:
                    self.sfx_shield.play()
                
                # Efeito visual
                pos = hit.rect.center
                self.particle_system.add_explosion(pos, (255, 100, 100), 12, 1.2)
                self.camera_shake = 0.3
                
                # Incrementa estatísticas
                self.stats.shields_used += 1
        
        # Colisão mísseis vs player (sem escudo)
        else:
            hits = pygame.sprite.spritecollide(self.player, self.missiles, True)
            for hit in hits:
                self.player.vida -= 1
                if self.sfx_hit:
                    self.sfx_hit.play()
                
                # Efeito visual de dano
                pos = self.player.rect.center
                self.particle_system.add_explosion(pos, (255, 0, 0), 8, 1.0)
                self.screen_flash = 0.3
                self.camera_shake = 0.5
                
                # Incrementa estatísticas
                self.stats.damage_taken += 1
                
                # Verifica game over
                if self.player.vida <= 0:
                    self.game_state = GameState.GAME_OVER

    def _handle_boss_defeat(self):
        """Processa derrota do boss."""
        if self.sfx_explosion:
            self.sfx_explosion.play()
        
        # Efeito visual de explosão massiva
        boss_center = self.boss.rect.center
        for _ in range(30):
            offset_x = random.randint(-50, 50)
            offset_y = random.randint(-50, 50)
            pos = (boss_center[0] + offset_x, boss_center[1] + offset_y)
            self.particle_system.add_explosion(pos, (255, 150, 0), 15, 1.5)
        
        # Camera shake intenso
        self.camera_shake = 1.0
        
        # Adiciona pontos bonus
        bonus_points = 100 * self.level
        self.player.pontos += bonus_points
        
        # Incrementa estatísticas
        self.stats.bosses_defeated += 1
        
        # Avança para próximo nível
        self.start_level_transition(self.level + 1)

    def _update_gameplay(self, dt: float):
        """Atualiza lógica principal do gameplay."""
        # Aplica escala de tempo (slow motion)
        effective_dt = dt * self.time_scale
        
        # Atualiza player
        self.player.update(self.keys, effective_dt)
        
        # Atualiza itens
        self.items.update(effective_dt)
        
        # Sistema de spawn de itens
        self._update_item_spawning(effective_dt)
        
        # Colisões
        self._handle_item_collisions()
        
        # Verifica condições de avanço de nível
        self._check_level_progression()
        
        # Verifica game over
        if self.player.vida <= 0:
            self.game_state = GameState.GAME_OVER

    def _update_item_spawning(self, dt: float):
        """Sistema avançado de spawn de itens."""
        self.spawn_timer += dt
        
        # Verifica se deve spawnar novo item
        should_spawn = (
            self.spawn_timer >= self.spawn_interval and 
            len(self.items) < self.max_items
        )
        
        if should_spawn:
            self.spawn_timer = 0.0
            self._spawn_item()

    def _spawn_item(self):
        """Spawna um item baseado nos pesos configurados."""
        # Seleciona tipo baseado nos pesos
        item_type = self._weighted_item_selection()
        
        if item_type not in self.item_images:
            return
        
        item_data = self.item_images[item_type]
        
        # Calcula velocidade baseada no multiplicador do nível
        base_speed = (150, 250)
        multiplier = self.speed_multiplier
        
        # Adiciona variação baseada na dificuldade adaptativa
        multiplier *= self.difficulty_scaling
        
        speed_range = (
            int(base_speed[0] * multiplier),
            int(base_speed[1] * multiplier)
        )
        
        # Cria item
        item = Item(
            image=item_data["image"],
            tipo=item_type,
            valor=item_data["valor"],
            efeito=item_data["efeito"],
            speed_range=speed_range
        )
        
        self.items.add(item)
        self.total_items_spawned += 1

    def _weighted_item_selection(self) -> str:
        """Seleciona item baseado nos pesos configurados."""
        weights = self.current_item_weights
        total_weight = sum(weights.values())
        
        if total_weight == 0:
            return "meia"  # Fallback
        
        rand_value = random.randint(1, total_weight)
        current_weight = 0
        
        for item_type, weight in weights.items():
            current_weight += weight
            if rand_value <= current_weight:
                return item_type
        
        return list(weights.keys())[0]  # Fallback

    def _handle_item_collisions(self):
        """Processa colisões com itens de forma avançada."""
        hits = pygame.sprite.spritecollide(self.player, self.items, True)
        
        for item in hits:
            self._process_item_collection(item)

    def _process_item_collection(self, item):
        """Processa coleta de um item específico."""
        # Efeito visual baseado no tipo de item
        pos = item.rect.center
        
        if item.valor > 0:
            # Item positivo - efeito verde/dourado
            color = (0, 255, 0) if item.valor < 10 else (255, 215, 0)
            self.particle_system.add_collect_effect(pos, color)
            def process_input(self, events, keys):
        self.events = events
        self.keys = keys
        # Som de escudo
        for e in events:
            if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                if not self.player.shield_active and self.player.cooldown_timer <= 0.0:
                    if self.sfx_shield:
                        self.sfx_shield.play()

    def update(self, dt):
        if self.in_transition:
            self.transition_timer += dt
            if self.transition_timer >= self.transition_duration:
                self.in_transition = False
            return

        # Atualiza player e itens
        self.player.update(self.keys, dt)
        self.items.update(dt)

        # Lógica boss nível 4
        if self.level == 4 and self.boss and not self.boss.dead:
            self.boss.update(dt)
            self.missiles.update(dt)
            
            if self.boss.ready_to_fire():
                m = self.boss.fire_missile()
                self.missiles.add(m)
                if self.sfx_missile:
                    self.sfx_missile.play()
            
            # Colisões com escudo
            if self.player.shield_active:
                hits = pygame.sprite.spritecollide(self.player, self.missiles, True)
                if hits:
                    self.boss.register_hit()
                    if self.sfx_shield:
                        self.sfx_shield.play()
                    if self.boss.dead:
                        if self.sfx_explosion:
                            self.sfx_explosion.play()
                        self.start_level_transition(5)
            else:
                # Se não tem escudo ativo, mísseis causam dano
                hits = pygame.sprite.spritecollide(self.player, self.missiles, True)
                if hits:
                    self.player.vida -= 1
                    if self.sfx_hit:
                        self.sfx_hit.play()
                    if self.player.vida <= 0:
                        self.handle_game_over()
            return

        # Spawn de itens regulares
        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval and len(self.items) < self.max_items:
            self.spawn_timer = 0
            tipos = (["meia", "cubo", "caneca"] if self.level <= 1
                     else (["meia", "cubo", "caneca", "banana"] if self.level == 2
                           else ["meia", "cubo", "caneca", "banana", "toalha"]))
            tipo = random.choice(tipos)
            d = self.item_images[tipo]
            base = (150, 250)
            mult = self.speed_multiplier
            speed_range = (int(base[0] * mult), int(base[1] * mult))
            it = Item(image=d["image"], tipo=tipo, valor=d["valor"], efeito=d["efeito"], speed_range=speed_range)
            self.items.add(it)

        # Colisões com itens
        hits = pygame.sprite.spritecollide(self.player, self.items, True)
        for item in hits:
            if self.sfx_collect:
                self.sfx_collect.play()
                
            if item.efeito == "escorregar":
                self.player.escorregar()
                if self.sfx_hit:
                    self.sfx_hit.play()
            elif item.efeito == "boost":
                self.player.boost_speed()
            elif item.valor > 0:
                self.player.pontos += item.valor
            else:
                if not self.player.shield_active:
                    self.player.vida -= abs(item.valor)
                    if self.sfx_lose_life:
                        self.sfx_lose_life.play()
                    if self.player.vida <= 0:
                        self.handle_game_over()

        # Remover itens que saíram da tela
        for item in list(self.items):
            if item.rect.top > HEIGHT:
                self.items.remove(item)

        # Avanço de nível
        if self.level < self.max_level:
            need = self.points_to_next.get(self.level)
            if need and self.player.pontos >= need:
                self.start_level_transition(self.level + 1)

        # Verificar condição de vitória (último nível)
        if self.level == self.max_level:
            final_points = self.points_to_next.get(self.max_level - 1, 500)
            if self.player.pontos >= final_points * 2:  # Dobro dos pontos para vitória
                self.handle_victory()

    def handle_game_over(self):
        """Lida com o fim de jogo quando o player morre"""
        try:
            pygame.mixer.music.fadeout(1000)
        except:
            pass
        
        # Toca som de game over se disponível
        audio_folder = os.path.join("assets", "audio")
        game_over_sound = load_sound(os.path.join(audio_folder, "game_over.wav"))
        if game_over_sound:
            game_over_sound.play()
        
        # Importa e muda para tela de game over
        from scenes.game_over_scene import GameOverScene
        self.next_scene = GameOverScene(self.player.pontos, self.level)

    def handle_victory(self):
        """Lida com a vitória do jogo"""
        try:
            pygame.mixer.music.fadeout(1000)
        except:
            pass
        
        # Toca som de vitória se disponível
        audio_folder = os.path.join("assets", "audio")
        victory_sound = load_sound(os.path.join(audio_folder, "victory.wav"))
        if victory_sound:
            victory_sound.play()
        
        # Importa e muda para tela de vitória
        from scenes.victory_scene import VictoryScene
        self.next_scene = VictoryScene(self.player.pontos)

    def render(self, screen):
        # Desenha o background
        screen.blit(self.background, (0, 0))
        
        if not self.in_transition:
            # Desenha todos os itens
            self.items.draw(screen)
            
            # Desenha o player
            self.player.draw(screen)
            
            # Chefão nível 4 - Boss battle
            if self.level == 4 and self.boss and not self.boss.dead:
                # Desenha o boss
                screen.blit(self.boss.image, self.boss.rect)
                
                # Desenha os mísseis
                self.missiles.draw(screen)
                
                # Barra de vida do boss (fundo vermelho)
                boss_health_bg = pygame.Rect(WIDTH//2 - 100, 30, 200, 20)
                pygame.draw.rect(screen, (200, 0, 0), boss_health_bg)
                
                # Barra de vida do boss (vida atual em verde)
                health_percentage = 1 - (self.boss.hits_taken / self.boss.max_hits)
                health_width = int(200 * health_percentage)
                boss_health_fg = pygame.Rect(WIDTH//2 - 100, 30, health_width, 20)
                pygame.draw.rect(screen, (0, 200, 0), boss_health_fg)
                
                # Borda da barra de vida do boss
                pygame.draw.rect(screen, (255, 255, 255), boss_health_bg, 2)
                
                # Nome do boss
                font_boss = pygame.font.SysFont(None, 36)
                boss_text = font_boss.render("Entregador Temporal", True, (255, 255, 255))
                boss_text_rect = boss_text.get_rect(center=(WIDTH//2, 15))
                screen.blit(boss_text, boss_text_rect)
            
            # Desenha o HUD com indicador de escudo pronto
            shield_ready = (self.player.cooldown_timer <= 0.0)
            draw_hud(screen, self.player.pontos, self.player.vida, shield_ready)
            
            # Indicador visual de nível atual (canto superior direito)
            font_level = pygame.font.SysFont(None, 28)
            level_text = font_level.render(f"Nível {self.level}", True, (255, 255, 255))
            level_rect = level_text.get_rect(topright=(WIDTH - 10, 10))
            
            # Fundo semi-transparente para o texto do nível
            level_bg = pygame.Surface((level_text.get_width() + 10, level_text.get_height() + 6))
            level_bg.set_alpha(128)
            level_bg.fill((0, 0, 0))
            level_bg_rect = level_bg.get_rect(topright=(WIDTH - 5, 7))
            screen.blit(level_bg, level_bg_rect)
            screen.blit(level_text, level_rect)
            
            # Indicador de próximo nível (se não estiver no último nível)
            if self.level < self.max_level:
                points_needed = self.points_to_next.get(self.level, 0)
                if points_needed > 0:
                    progress = min(self.player.pontos / points_needed, 1.0)
                    
                    # Barra de progresso para próximo nível
                    progress_bg = pygame.Rect(10, HEIGHT - 30, 200, 15)
                    pygame.draw.rect(screen, (100, 100, 100), progress_bg)
                    
                    progress_fg = pygame.Rect(10, HEIGHT - 30, int(200 * progress), 15)
                    pygame.draw.rect(screen, (255, 215, 0), progress_fg)  # Dourado
                    
                    pygame.draw.rect(screen, (255, 255, 255), progress_bg, 2)
                    
                    # Texto da barra de progresso
                    font_progress = pygame.font.SysFont(None, 24)
                    progress_text = font_progress.render(f"Próximo nível: {self.player.pontos}/{points_needed}", True, (255, 255, 255))
                    progress_text_rect = progress_text.get_rect(topleft=(10, HEIGHT - 50))
                    screen.blit(progress_text, progress_text_rect)
        
        else:
            # Tela de transição entre níveis
            # Overlay escuro semi-transparente
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))
            
            # Texto principal do nível
            font_main = pygame.font.SysFont(None, 72)
            main_text = font_main.render(f"Nível {self.level}", True, (255, 255, 255))
            main_rect = main_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 30))
            screen.blit(main_text, main_rect)
            
            # Texto secundário com dica ou informação
            font_sub = pygame.font.SysFont(None, 36)
            if self.level == 4:
                sub_text = font_sub.render("Boss Battle!", True, (255, 100, 100))
            elif self.level == self.max_level:
                sub_text = font_sub.render("Nível Final!", True, (255, 215, 0))
            else:
                sub_text = font_sub.render("Prepare-se!", True, (200, 200, 200))
            
            sub_rect = sub_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 20))
            screen.blit(sub_text, sub_rect)
            
            # Barra de carregamento da transição
            transition_progress = min(self.transition_timer / self.transition_duration, 1.0)
            loading_bg = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 60, 200, 10)
            pygame.draw.rect(screen, (100, 100, 100), loading_bg)
            
            loading_fg = pygame.Rect(WIDTH//2 - 100, HEIGHT//2 + 60, int(200 * transition_progress), 10)
            pygame.draw.rect(screen, (0, 255, 0), loading_fg)
            
            pygame.draw.rect(screen, (255, 255, 255), loading_bg, 2)
        
        # Efeitos visuais adicionais para feedback
        # Piscar da tela quando o player toma dano (se implementado)
        if hasattr(self.player, 'damage_flash_timer') and self.player.damage_flash_timer > 0:
            flash_overlay = pygame.Surface((WIDTH, HEIGHT))
            flash_alpha = int(128 * (self.player.damage_flash_timer / 0.2))  # Assumindo 0.2s de flash
            flash_overlay.set_alpha(flash_alpha)
            flash_overlay.fill((255, 0, 0))
            screen.blit(flash_overlay, (0, 0))