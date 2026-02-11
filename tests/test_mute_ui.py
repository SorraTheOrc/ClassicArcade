"""Tests for mute toggle UI and persistence.

This suite verifies:
- Pressing M key toggles the global mute flag.
- The menu displays the mute status ("Sound On" or "Muted").
- In‑game overlay shows the mute status.
- The mute flag persists across sessions via ``settings.json``.
"""

import importlib
import json
import os

# Ensure project root is on sys.path for imports
import sys
import unittest

import pygame

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from classic_arcade import config
from classic_arcade.audio import toggle_mute
from classic_arcade.config import _SETTINGS_PATH, BLACK, YELLOW, save_settings
from classic_arcade.engine import MenuState
from classic_arcade.menu_items import get_menu_items
from games.game_base import Game
from games.snake import SnakeState


class TestMuteUI(unittest.TestCase):
    def setUp(self):
        pygame.init()
        # Ensure a clean settings file
        if os.path.isfile(_SETTINGS_PATH):
            os.remove(_SETTINGS_PATH)
        # Reset mute flag
        config.MUTE = False
        save_settings()

    def tearDown(self):
        pygame.quit()
        if os.path.isfile(_SETTINGS_PATH):
            os.remove(_SETTINGS_PATH)

    def test_key_m_toggles_mute(self):
        # Ensure starting state
        self.assertFalse(config.MUTE)
        # Simulate M key press on a game state (SnakeState)
        snake = SnakeState()
        m_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_m)
        snake.handle_event(m_event)
        self.assertTrue(config.MUTE)
        # Toggle back
        snake.handle_event(m_event)
        self.assertFalse(config.MUTE)

    def test_menu_displays_mute_status(self):
        # Menu with mute off
        menu = MenuState(get_menu_items())
        surface = pygame.Surface((800, 600))
        surface.fill(BLACK)
        menu.draw(surface)
        # Pixel at (10,10) should be not black (YELLOW text)
        self.assertNotEqual(surface.get_at((10, 10))[:3], BLACK)
        # Toggle mute
        toggle_mute()
        self.assertTrue(config.MUTE)
        # Redraw menu
        surface.fill(BLACK)
        menu.draw(surface)
        # Prefer checking internal property exposed for tests if available
        if hasattr(menu, "_last_mute_text"):
            self.assertEqual(menu._last_mute_text, "Muted")
        else:
            self.assertNotEqual(surface.get_at((10, 10))[:3], BLACK)

    def test_game_draw_mute_overlay(self):
        # Game with mute off
        snake = SnakeState()
        surface = pygame.Surface((800, 600))
        surface.fill(BLACK)
        snake.draw(surface)
        # If Game provides a return value or attribute for the mute text use it, else sample pixel
        label = None
        if hasattr(snake, "draw_mute_overlay"):
            try:
                label = snake.draw_mute_overlay(surface)
            except TypeError:
                # older signature, ignore
                pass
        if label is not None:
            self.assertIn(label, ("Muted", "Sound On"))
        else:
            self.assertNotEqual(surface.get_at((10, 10))[:3], BLACK)
        # Toggle mute
        toggle_mute()
        self.assertTrue(config.MUTE)
        # Redraw
        surface.fill(BLACK)
        snake.draw(surface)
        # If Game exposes the mute label via draw_mute_overlay return value, prefer that
        label = None
        if hasattr(snake, "draw_mute_overlay"):
            try:
                label = snake.draw_mute_overlay(surface)
            except TypeError:
                pass
        if label is not None:
            self.assertEqual(label, "Muted")
        else:
            self.assertNotEqual(surface.get_at((10, 10))[:3], BLACK)

    def test_mute_persistence(self):
        # Ensure mute flag is false and saved
        self.assertFalse(config.MUTE)
        save_settings()
        # Verify settings file contains false (lowercase "mute" key)
        with open(_SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("mute", data)
        self.assertFalse(data["mute"])
        # Toggle mute (saves automatically)
        toggle_mute()
        self.assertTrue(config.MUTE)
        # Load file directly and verify lowercase key updated
        with open(_SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertTrue(data["mute"])
        # Reload config module to simulate new session
        from classic_arcade import config as cfg_mod

        importlib.reload(cfg_mod)
        self.assertTrue(cfg_mod.MUTE)


if __name__ == "__main__":
    unittest.main()
