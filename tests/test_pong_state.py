import unittest

import pygame

from classic_arcade.engine import MenuState
from games.pong import PongState


class TestPongEscKey(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.state = PongState()

    def tearDown(self):
        pygame.quit()

    def test_esc_key_transitions_to_menu(self):
        # Simulate ESC key press event
        esc_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
        self.state.handle_event(esc_event)
        # Verify that a transition to MenuState was requested
        self.assertIsInstance(self.state.next_state, MenuState)


if __name__ == "__main__":
    unittest.main()
