# utils.py
"""Utility functions and constants for the Pygame arcade suite.
Provides screen dimensions, color definitions, and a helper function for drawing text.
"""

# Added imports for asset path resolution
import os
import sys
from typing import List, Tuple

import pygame

from classic_arcade.config import (
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


def resolve_asset_path(relative_path: str) -> str | None:
    """Resolve an asset path, handling PyInstaller bundles.

    Args:
        relative_path: Path relative to the project root ``assets`` directory.

    Returns:
        The absolute path to the asset if it exists, otherwise ``None``.
    """
    # When running from a PyInstaller bundle, ``sys._MEIPASS`` points to the
    # temporary extraction directory containing bundled data files.
    if hasattr(sys, "_MEIPASS"):
        base_dir = sys._MEIPASS
    else:
        # For normal execution, assets are located relative to the project root.
        # ``classic_arcade`` package resides one level below the repository root.
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    candidate = os.path.join(base_dir, relative_path)
    return candidate if os.path.exists(candidate) else None


def wrap_text(
    font: pygame.font.Font,
    text: str,
    max_width: int,
    color: Tuple[int, int, int] = (255, 255, 255),
) -> List[Tuple[pygame.Surface, int]]:
    """Wrap text to fit within a maximum width.

    Args:
        font: Pygame font object.
        text: Text to wrap.
        max_width: Maximum line width in pixels.
        color: RGB color tuple for the text.

    Returns:
        List of (surface, height) tuples for each line.
    """
    lines = text.split("\n")
    result: List[Tuple[pygame.Surface, int]] = []

    for line in lines:
        words = line.split(" ")
        current_line = ""
        current_width = 0

        for word in words:
            word_surface = font.render(word + " ", True, color)
            word_width = word_surface.get_width()

            if current_width + word_width <= max_width or not current_line:
                current_line += word + " "
                current_width += word_width
            else:
                if current_line:
                    surface = font.render(current_line.strip(), True, color)
                    result.append((surface, font.get_height()))
                current_line = word + " "
                current_width = word_width

        if current_line:
            surface = font.render(current_line.strip(), True, color)
            result.append((surface, font.get_height()))

    return result


def draw_text(
    surface: pygame.Surface,
    text: str,
    size: int,
    color: Tuple[int, int, int],
    x: int,
    y: int,
    center: bool = True,
    max_width: int | None = None,
) -> int:
    """Draw text on a surface.

    Args:
        surface: Surface to draw on.
        text: Text to display.
        size: Font size.
        color: RGB color tuple.
        x: X coordinate.
        y: Y coordinate.
        center: If True, (x, y) is the center of the text; otherwise top-left.
        max_width: Maximum line width for wrapping (optional).

    Returns:
        Total height of rendered text in pixels.
    """
    if not pygame.font.get_init():
        pygame.font.init()
    font = pygame.font.Font(None, size)

    if max_width:
        lines = wrap_text(font, text, max_width, color)
        total_height = sum(h for _, h in lines)

        if center:
            start_y = y - total_height // 2
        else:
            start_y = y

        for i, (line_surface, line_height) in enumerate(lines):
            line_rect = line_surface.get_rect()
            if center:
                line_rect.center = (x, start_y + i * line_height)
            else:
                line_rect.topleft = (x, start_y + i * line_height)
            line_surface.fill(color, special_flags=pygame.BLEND_RGBA_MULT)
            surface.blit(line_surface, line_rect)

        return total_height
    else:
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        if center:
            text_rect.center = (x, y)
        else:
            text_rect.topleft = (x, y)
        surface.blit(text_surface, text_rect)
        return font.get_height()


__all__ = ["draw_text", "wrap_text", "resolve_asset_path"]
