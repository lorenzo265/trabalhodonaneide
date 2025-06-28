import pygame, os
from assets.loader import load_image, load_sound
from core.config import WIDTH, HEIGHT
from scenes.game_scene import GameScene  # para voltar ao jogo

class CutsceneScene:
    def __init__(self, level, next_level):
        self.next_scene = self
        # Pasta de frames: assets/cutscenes/level{level}/
        folder = os.path.join("assets","cutscenes",f"level{level}")
        # Carregar frames
        self.frames = []
        if os.path.isdir(folder):
            for f in sorted(os.listdir(folder)):
                if f.lower().endswith((".png",".jpg","bmp")):
                    path = os.path.join(folder, f)
                    img = load_image(path, (WIDTH, HEIGHT))
                    self.frames.append(img)
        # Carregar áudio da cutscene
        audio_path = os.path.join("assets","cutscenes",f"level{level}", "audio.wav")
        if os.path.exists(audio_path):
            self.cutscene_sound = load_sound(audio_path)
            if self.cutscene_sound:
                self.cutscene_sound.play()
        else:
            self.cutscene_sound = None
        self.index = 0
        self.timer = 0.0
        self.frame_rate = 1/30  # 30 FPS; ajuste se necessário
        self.next_level = next_level
        # Permitir pular cutscene
        self.skip = False

    def process_input(self, events, keys):
        for ev in events:
            if ev.type == pygame.KEYDOWN:
                # Tecla qualquer pula cutscene
                self.skip = True

    def update(self, dt):
        if self.skip:
            # parar áudio e ir para o próximo nível
            if self.cutscene_sound: self.cutscene_sound.stop()
            self.next_scene = GameScene(self.next_level)
            return
        if not self.frames:
            # sem frames, pula direto
            self.next_scene = GameScene(self.next_level)
            return
        self.timer += dt
        if self.timer >= self.frame_rate:
            self.timer -= self.frame_rate
            self.index += 1
            if self.index >= len(self.frames):
                # fim da cutscene
                if self.cutscene_sound: self.cutscene_sound.stop()
                self.next_scene = GameScene(self.next_level)

    def render(self, screen):
        if self.frames and self.index < len(self.frames):
            screen.blit(self.frames[self.index], (0, 0))
        else:
            # tela preta se nada para mostrar
            screen.fill((0,0,0))
