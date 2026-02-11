import os
import sys
import unittest

import pygame

# Ensure the project root is on sys.path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from classic_arcade.config import KEY_PAUSE
from games.breakout import BreakoutState
from games.pong import PongState
from games.snake import SnakeState
from games.space_invaders import SpaceInvadersState
from games.tetris import TetrisState


class TestPauseFunctionality(unittest.TestCase):
    def setUp(self):
        pygame.init()
        # instantiate each state
        self.snake = SnakeState()
        self.pong = PongState()
        self.breakout = BreakoutState()
        self.space = SpaceInvadersState()
        self.tetris = TetrisState()

    def tearDown(self):
        pygame.quit()

    def assert_pause_toggle(self, state):
        # Initially not paused
        self.assertFalse(state.paused)
        # Send pause key event
        pause_event = pygame.event.Event(pygame.KEYDOWN, key=KEY_PAUSE)
        state.handle_event(pause_event)
        self.assertTrue(state.paused)
        # Send pause again to resume
        state.handle_event(pause_event)
        self.assertFalse(state.paused)

    def test_snake_pause(self):
        self.assert_pause_toggle(self.snake)

    def test_pong_pause(self):
        self.assert_pause_toggle(self.pong)

    def test_breakout_pause(self):
        self.assert_pause_toggle(self.breakout)

    def test_space_invaders_pause(self):
        self.assert_pause_toggle(self.space)

    def test_tetris_pause(self):
        self.assert_pause_toggle(self.tetris)

    def test_update_paused_no_change(self):
        # Use Snake as representative; pause it and ensure update does not change state
        self.snake.handle_event(pygame.event.Event(pygame.KEYDOWN, key=KEY_PAUSE))
        self.assertTrue(self.snake.paused)
        # Capture current snake positions
        original_snake = list(self.snake.snake)
        # Call update with some delta time
        self.snake.update(0.5)
        # Positions should be unchanged
        self.assertEqual(original_snake, self.snake.snake)


if __name__ == "__main__":
    unittest.main()
