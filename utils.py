# utils.py
"""Utility functions and constants for the Pygame arcade suite.
Provides screen dimensions, color definitions, and a helper function for drawing text.
"""

from typing import Tuple

import pygame

from config import (
    BLACK,
    BLUE,
    CYAN,
    GRAY,
    GREEN,
    MAGENTA,
    RED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WHITE,
    YELLOW,
)


def draw_text(
    surface: pygame.Surface,
    text: str,
    size: int,
    color: Tuple[int, int, int],
    x: int,
    y: int,
    center: bool = True,
) -> None:
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
    if not pygame.font.get_init():
        pygame.font.init()
    font = pygame.font.Font(None, size)
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    if center:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
    surface.blit(text_surface, text_rect)
