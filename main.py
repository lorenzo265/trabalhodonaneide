import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.game import run_game
from scenes.game_scene import GameScene

if __name__ == "__main__":
    run_game(800, 600, 60, lambda: GameScene(level=1))
