import unittest
import pygame
import sys
import os

# Ensure project root is on sys.path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from engine import MenuState
from games.splash import SplashState


class TestSplashScreen(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.state = SplashState()

    def tearDown(self):
        pygame.quit()

    def test_fade_and_transition(self):
        # Simulate updates before fade complete
        self.state.update(0.5)  # half a second
        self.assertTrue(0 < self.state.alpha < 255)
        self.assertIsNone(self.state.next_state)
        # Simulate updates to complete fade (another 0.6 seconds => total > 1.0)
        self.state.update(0.6)
        self.assertEqual(self.state.alpha, 255)
        self.assertIsNone(self.state.next_state)
        # Simulate hold duration (1.0 sec) + a bit more to trigger transition
        self.state.update(1.1)
        self.assertIsInstance(self.state.next_state, MenuState)


if __name__ == "__main__":
    unittest.main()
