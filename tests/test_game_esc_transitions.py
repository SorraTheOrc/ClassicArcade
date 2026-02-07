import os
import sys
import unittest

import pygame

# Ensure the project root is on sys.path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine import MenuState
from games.breakout import BreakoutState
from games.pong import PongState
from games.snake import SnakeState
from games.space_invaders import SpaceInvadersState
from games.tetris import TetrisState


class TestEscKeyTransitions(unittest.TestCase):
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

    def assert_transition_to_menu(self, state):
        esc_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        state.handle_event(esc_event)
        self.assertIsInstance(state.next_state, MenuState)

    def test_snake_esc(self):
        self.assert_transition_to_menu(self.snake)

    def test_pong_esc(self):
        self.assert_transition_to_menu(self.pong)

    def test_breakout_esc(self):
        self.assert_transition_to_menu(self.breakout)

    def test_space_invaders_esc(self):
        self.assert_transition_to_menu(self.space)

    def test_tetris_esc(self):
        self.assert_transition_to_menu(self.tetris)


if __name__ == "__main__":
    unittest.main()
