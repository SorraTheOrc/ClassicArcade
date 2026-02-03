"""Configuration module for the arcade suite.

Centralises screen dimensions, default FPS, colour definitions, and key bindings.
"""

import pygame

# Screen dimensions
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480

# Default FPS for the engine
FPS = 60

# Colour definitions (RGB tuples)
COLORS = {
    "WHITE": (255, 255, 255),
    "BLACK": (0, 0, 0),
    "RED": (255, 0, 0),
    "GREEN": (0, 255, 0),
    "BLUE": (0, 0, 255),
    "YELLOW": (255, 255, 0),
    "CYAN": (0, 255, 255),
    "MAGENTA": (255, 0, 255),
    "GRAY": (128, 128, 128),
}

# Individual colour constants for convenience (re-exported)
WHITE = COLORS["WHITE"]
BLACK = COLORS["BLACK"]
RED = COLORS["RED"]
GREEN = COLORS["GREEN"]
BLUE = COLORS["BLUE"]
YELLOW = COLORS["YELLOW"]
CYAN = COLORS["CYAN"]
MAGENTA = COLORS["MAGENTA"]
GRAY = COLORS["GRAY"]

# Key bindings (using pygame key constants)
KEY_QUIT = pygame.K_ESCAPE
KEY_PAUSE = pygame.K_p
KEY_RESTART = pygame.K_r
KEY_UP = pygame.K_UP
KEY_DOWN = pygame.K_DOWN
KEY_LEFT = pygame.K_LEFT
KEY_RIGHT = pygame.K_RIGHT
