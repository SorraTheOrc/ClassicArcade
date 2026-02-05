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

# Global mute flag for audio playback. Defaults to False (audio enabled).
MUTE = False

# Settings persistence for mute flag
import json
import os

_SETTINGS_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "settings.json")
)


def _load_settings() -> None:
    """Load settings from ``settings.json`` if it exists."""
    if os.path.isfile(_SETTINGS_PATH):
        try:
            with open(_SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict) and "MUTE" in data:
                    global MUTE
                    MUTE = bool(data["MUTE"])
        except Exception:
            # Ignore errors – default MUTE remains False
            pass


def save_settings() -> None:
    """Save current settings (currently only ``MUTE``) to ``settings.json``."""
    data = {"MUTE": MUTE}
    try:
        with open(_SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


# Load settings on import
_load_settings()

# Key bindings (using pygame key constants)
KEY_QUIT = pygame.K_ESCAPE
KEY_PAUSE = pygame.K_p
KEY_RESTART = pygame.K_r
KEY_UP = pygame.K_UP
KEY_DOWN = pygame.K_DOWN
KEY_LEFT = pygame.K_LEFT
KEY_RIGHT = pygame.K_RIGHT
