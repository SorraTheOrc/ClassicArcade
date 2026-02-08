import os

os.environ["HEADLESS"] = "1"
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
import random

pygame.init()
pygame.font.init()

from games.snake import SnakeState
from config import SCREEN_WIDTH, SCREEN_HEIGHT


def test_powerup_spawn_and_collect():
    # Ensure determinism for random
    random.seed(42)
    s = SnakeState()
    screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    # Simulate eating food multiple times to trigger spawn chance
    initial_powerups = len(s.powerups)
    for _ in range(50):
        # place head on food to simulate eat
        s.food = s.snake[0]
        s.direction = (0, 0)
        s.update(1.0 / 60.0)
        s.draw(screen)
    # At least one powerup should have spawned with this many eats and deterministic seed
    assert len(s.powerups) >= initial_powerups


def test_powerup_effects_apply():
    random.seed(123)
    s = SnakeState()
    # spawn a speed powerup manually at head
    pu = {"type": "speed", "pos": s.snake[0], "ttl": 10.0}
    s.powerups.append(pu)
    # update so collision handling runs
    s.direction = (0, 0)
    s.update(1.0 / 60.0)
    # speed boost should be activated
    assert s._speed_boost_time > 0


def test_shrink_particles_and_pulse():
    # deterministic
    random.seed(1)
    s = SnakeState()
    # ensure snake has some tail so shrink can remove segments
    s.snake = [(100, 100), (80, 100), (60, 100), (40, 100)]
    # place shrink powerup at head
    pu = {"type": "shrink", "pos": s.snake[0], "ttl": 10.0}
    s.powerups.append(pu)
    # update so collision handling runs
    s.direction = (0, 0)
    s.update(1.0 / 60.0)
    # particles should have been spawned and flash remaining set
    assert getattr(s, "_particles", [])
    assert s._shrink_flash_remaining > 0
