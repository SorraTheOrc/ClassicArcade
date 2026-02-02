# utils.py
"""Utility functions and constants for the Pygame arcade suite.
Provides screen dimensions, color definitions, and a helper function for drawing text.
"""

import pygame

# Screen dimensions
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480

# Colors (R, G, B)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
GRAY = (128, 128, 128)


def draw_text(surface, text, size, color, x, y, center=True):
    """Draw text on a surface.

    Args:
        surface (pygame.Surface): Surface to draw on.
        text (str): Text to display.
        size (int): Font size.
        color (tuple): RGB color tuple.
        x (int): X coordinate.
        y (int): Y coordinate.
        center (bool): If True, (x, y) is the center of the text; otherwise top-left.
    """
    font = pygame.font.Font(None, size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    if center:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
    surface.blit(text_surface, text_rect)
