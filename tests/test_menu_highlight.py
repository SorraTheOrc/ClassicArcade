import unittest

import pygame

from classic_arcade.config import BLACK, GRAY, SCREEN_HEIGHT, SCREEN_WIDTH
from classic_arcade.engine import MenuState
from classic_arcade.menu_items import get_menu_items


class TestMenuHighlight(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.state = MenuState(get_menu_items())
        self.surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.surface.fill(BLACK)

    def tearDown(self):
        pygame.quit()

    def test_highlight_rect_and_animation(self):
        # Initial draw should set highlight_rect and draw the rectangle
        self.state.draw(self.surface)
        self.assertIsNotNone(self.state.highlight_rect)
        # Verify that the top-left pixel of the highlight rectangle is the highlight color
        tl = self.state.highlight_rect.topleft
        self.assertEqual(self.surface.get_at(tl)[:3], GRAY)

        # Capture initial border width
        initial_width = self.state.highlight_border_width
        # Update animation phase
        self.state.update(0.5)  # advance half a second
        # Border width should change after update (pulsing effect)
        self.assertNotEqual(self.state.highlight_border_width, initial_width)

        # Draw again to apply new border width
        self.state.draw(self.surface)
        # Ensure highlight_rect remains set
        self.assertIsNotNone(self.state.highlight_rect)


if __name__ == "__main__":
    unittest.main()
