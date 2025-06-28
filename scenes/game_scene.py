# scenes/game_scene.py
import pygame, os, random
from core.config import WIDTH, HEIGHT
from entities.dona_neide import DonaNeide
from entities.item import Item
from ui.hud import draw_hud
from assets.loader import load_image, load_sound, load_music
from entities.entregador_temporal import EntregadorTemporal
from entities.CaixaMissil import CaixaMissil

class GameScene:
    def __init__(self, level=1):
        self.next_scene = self

        # Background fixo
        bg_path = os.path.join("assets", "images", "fundos", "cozinha.png")
        if os.path.exists(bg_path):
            self.background = load_image(bg_path, (WIDTH, HEIGHT))
        else:
            self.background = pygame.Surface((WIDTH, HEIGHT))
            self.background.fill((135, 206, 250))

        # Carrega Dona Neide e escudo
        neide_path = os.path.join("assets", "images", "personagens", "neide_img.png")
        shield_path = os.path.join("assets", "images", "efeitos", "veia_panescudo.png")
        neide_img = load_image(neide_path, (64, 64)) if os.path.exists(neide_path) else self.placeholder_surface((64, 64), (255, 200, 200))
        shield_img = load_image(shield_path, (64, 64)) if os.path.exists(shield_path) else None
        self.player = DonaNeide(neide_img, shield_img)
        self.player_group = pygame.sprite.GroupSingle(self.player)

        # Definição de itens
        self.item_definitions = {
            "meia":   {"filename": "item_0.png",  "valor": 1,  "size": (100, 100), "efeito": None},
            "cubo":   {"filename": "item_1.png",  "valor": 10, "size": (100, 100), "efeito": None},
            "caneca": {"filename": "item_2.png",  "valor": 5,  "size": (68,  68),  "efeito": None},
            "banana": {"filename": "banana.png",  "valor": -1, "size": (40,  40),  "efeito": "escorregar"},
            "toalha": {"filename": "item_3.png",  "valor": 0,  "size": (38,  38),  "efeito": "boost"},
        }
        self.item_images = {}
        for tipo, data in self.item_definitions.items():
            path = os.path.join("assets", "images", "itens", data["filename"])
            img = load_image(path, data["size"]) if os.path.exists(path) else self.placeholder_surface(data["size"], (255,255,0))
            self.item_images[tipo] = {"image": img, "valor": data["valor"], "efeito": data["efeito"]}

        # Configurações de nível
        self.level = level
        self.max_level = 8
        self.points_to_next = {1:10,2:20,3:25,4:140,5:200,6:270,7:350}
        self.level_configs = {
            1:{"spawn_interval":3.0, "max_items":4, "speed_multiplier":1.0},
            2:{"spawn_interval":2.5, "max_items":5, "speed_multiplier":1.2},
            3:{"spawn_interval":2.0, "max_items":6, "speed_multiplier":1.3},
            4:{"spawn_interval":1.5, "max_items":6, "speed_multiplier":1.4},
            5:{"spawn_interval":1.2, "max_items":7, "speed_multiplier":1.5},
            6:{"spawn_interval":1.0, "max_items":7, "speed_multiplier":1.6},
            7:{"spawn_interval":0.8, "max_items":8, "speed_multiplier":1.7},
            8:{"spawn_interval":0.8, "max_items":8, "speed_multiplier":1.8},
        }

        # Sons
        audio_folder = os.path.join("assets","audio")
        self.sfx_collect   = load_sound(os.path.join(audio_folder,"catch.wav")) or load_sound(os.path.join(audio_folder,"catch.flac"))
        self.sfx_explosion = load_sound(os.path.join(audio_folder,"explosions.wav"))
        self.sfx_hit       = load_sound(os.path.join(audio_folder,"hit.wav"))
        self.sfx_lose_life = load_sound(os.path.join(audio_folder,"lose_life.wav"))
        self.sfx_missile   = load_sound(os.path.join(audio_folder,"missile_launch.wav"))
        self.sfx_shield    = load_sound(os.path.join(audio_folder,"shield.wav"))
        self.sfx_shot      = load_sound(os.path.join(audio_folder,"shot.wav"))
        self.sfx_levelup   = load_sound(os.path.join(audio_folder,"levelup.wav"))
        for snd in [self.sfx_collect,self.sfx_explosion,self.sfx_hit,self.sfx_lose_life,self.sfx_missile,self.sfx_shield,self.sfx_shot,self.sfx_levelup]:
            if snd: snd.set_volume(0.7)
        if self.sfx_lose_life: self.sfx_lose_life.set_volume(0.8)
        if self.sfx_missile:   self.sfx_missile.set_volume(0.6)

        # Inicialização
        self.items = pygame.sprite.Group()
        self.load_level(self.level)
        self.play_level_music(self.level)
        self.in_transition = True
        self.transition_timer = 0.0
        self.transition_duration = 2.0

    def placeholder_surface(self,size,color):
        surf = pygame.Surface(size); surf.fill(color); return surf

    def load_level(self,level_num):
        cfg = self.level_configs.get(level_num,{})
        self.spawn_interval = cfg.get("spawn_interval",2.5)
        self.max_items      = cfg.get("max_items",5)
        self.speed_multiplier = cfg.get("speed_multiplier",1.0)
        self.spawn_timer    = 0.0
        self.items.empty()
        # Chefão nível 4
        if level_num==4:
            boss_img    = load_image("assets/images/chefes/entregador_temporal.png",(100,80))
            missile_img = load_image("assets/images/efeitos/caixa_missil.png",(40,40))
            self.boss     = EntregadorTemporal(boss_img,missile_img,pygame.Rect(0,0,WIDTH,HEIGHT),target=self.player)
            self.missiles = pygame.sprite.Group()
        else:
            self.boss     = None
            self.missiles = None

    def play_level_music(self,level):
        audio_folder = os.path.join("assets","audio")
        music_file = "boss_music.wav" if level==4 else "background_music.mp3"
        path = os.path.join(audio_folder,music_file)
        try: pygame.mixer.music.fadeout(500)
        except: pass
        if load_music(path): pygame.mixer.music.set_volume(0.5); pygame.mixer.music.play(-1)
        else: pygame.mixer.music.stop()

    def start_level_transition(self,new_level):
        if self.sfx_levelup: self.sfx_levelup.play()
        self.play_level_music(new_level)
        from core.video_player import play_cutscene_fullscreen
        video = os.path.join("assets","cutscenes",f"nivel_{self.level}_to_{new_level}.mp4")
        if os.path.exists(video): play_cutscene_fullscreen(video,(WIDTH,HEIGHT))
        self.level=new_level; self.load_level(new_level)
        self.in_transition=True; self.transition_timer=0.0
        self.play_level_music(new_level)
        self.player.rect.midbottom=(WIDTH//2,HEIGHT-10)

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
            self.boss.update(dt); self.missiles.update(dt)
            if self.boss.ready_to_fire():
                m = self.boss.fire_missile(); self.missiles.add(m)
                if self.sfx_missile: self.sfx_missile.play()
            # Colisões com escudo
            if self.player.shield_active:
                hits = pygame.sprite.spritecollide(self.player, self.missiles, True)
                if hits:
                    self.boss.register_hit()
                    if self.sfx_shield: self.sfx_shield.play()
                    if self.boss.dead:
                        if self.sfx_explosion: self.sfx_explosion.play()
                        self.start_level_transition(5)
            return

        # Spawn de itens
        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_interval and len(self.items) < self.max_items:
            self.spawn_timer = 0
            tipos = (["meia","cubo","caneca"] if self.level <= 1
                     else (["meia","cubo","caneca","banana"] if self.level == 2
                           else ["meia","cubo","caneca","banana","toalha"]))
            tipo = random.choice(tipos); d = self.item_images[tipo]
            base = (150,250); mult = self.speed_multiplier
            speed_range = (int(base[0]*mult), int(base[1]*mult))
            it = Item(image=d["image"], tipo=tipo, valor=d["valor"], efeito=d["efeito"], speed_range=speed_range)
            self.items.add(it)

        # Colisões itens
        hits = pygame.sprite.spritecollide(self.player, self.items, True)
        for item in hits:
            if item.efeito == "escorregar":
                self.player.escorregar()
            elif item.efeito == "boost":
                self.player.boost_speed()
            elif item.valor > 0:
                self.player.pontos += item.valor
            else:
                if not self.player.shield_active:
                    self.player.vida -= abs(item.valor)

        # Avanço de nível
        if self.level < self.max_level:
            need = self.points_to_next.get(self.level)
            if need and self.player.pontos >= need:
                self.start_level_transition(self.level+1)

    def render(self, screen):
        screen.blit(self.background, (0,0))
        if not self.in_transition:
            self.items.draw(screen)
            self.player.draw(screen)
            # Chefão nível 4
            if self.level == 4 and self.boss and not self.boss.dead:
                screen.blit(self.boss.image, self.boss.rect)
                self.missiles.draw(screen)
                pygame.draw.rect(screen, (200,0,0), (WIDTH//2-100, 30, 200, 20))
                v = 1 - self.boss.hits_taken / self.boss.max_hits
                pygame.draw.rect(screen, (0,200,0), (WIDTH//2-100, 30, int(200*v), 20))
            # HUD com indicador de escudo pronto
            shield_ready = (self.player.cooldown_timer <= 0.0)
            draw_hud(screen, self.player.pontos, self.player.vida, shield_ready)
        else:
            overlay = pygame.Surface((WIDTH,HEIGHT)); overlay.set_alpha(180); overlay.fill((0,0,0)); screen.blit(overlay,(0,0))
            font = pygame.font.SysFont(None,72)
            text = font.render(f"Nível {self.level}", True, (255,255,255))
            rect = text.get_rect(center=(WIDTH//2, HEIGHT//2)); screen.blit(text, rect)