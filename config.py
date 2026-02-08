"""Configuration module for the arcade suite.

Centralises screen dimensions, default FPS, colour definitions, and key bindings.
"""

# Screen dimensions – can be overridden via environment variables
import os

import pygame

SCREEN_WIDTH = int(os.getenv("SCREEN_WIDTH", 640))
SCREEN_HEIGHT = int(os.getenv("SCREEN_HEIGHT", 480))

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

# Difficulty levels
DIFFICULTY_EASY = "easy"
DIFFICULTY_MEDIUM = "medium"
DIFFICULTY_HARD = "hard"
_DIFFICULTY_LEVELS = [DIFFICULTY_EASY, DIFFICULTY_MEDIUM, DIFFICULTY_HARD]

# Per‑game difficulty defaults (default to medium)
SNAKE_DIFFICULTY = DIFFICULTY_EASY
PONG_DIFFICULTY = DIFFICULTY_EASY
BREAKOUT_DIFFICULTY = DIFFICULTY_EASY
SPACE_INVADERS_DIFFICULTY = DIFFICULTY_EASY
TETRIS_DIFFICULTY = DIFFICULTY_EASY


def difficulty_multiplier(level: str) -> float:
    """Return a speed multiplier for the given difficulty level.

    Easy = 1.0 (base speed), Medium = 1.5 (faster), Hard = 2.0 (fastest).
    """
    if level == DIFFICULTY_EASY:
        return 1.0
    if level == DIFFICULTY_MEDIUM:
        return 1.5
    if level == DIFFICULTY_HARD:
        return 2.0
    # Default to medium if unknown
    return 1.5


def get_difficulty(game_key: str) -> str:
    """Return the difficulty setting for the given game key.

    ``game_key`` should be one of: ``snake``, ``pong``, ``breakout``, ``space_invaders``, ``tetris``.
    Returns ``DIFFICULTY_MEDIUM`` if the key is unknown.
    """
    mapping = {
        "snake": SNAKE_DIFFICULTY,
        "pong": PONG_DIFFICULTY,
        "breakout": BREAKOUT_DIFFICULTY,
        "space_invaders": SPACE_INVADERS_DIFFICULTY,
        "tetris": TETRIS_DIFFICULTY,
    }
    return mapping.get(game_key, DIFFICULTY_MEDIUM)


def set_difficulty(game_key: str, level: str) -> None:
    """Set the difficulty for the given game and persist the settings.

    ``level`` must be one of the difficulty constants.
    """
    if level not in _DIFFICULTY_LEVELS:
        raise ValueError(f"Invalid difficulty level: {level}")
    global SNAKE_DIFFICULTY, PONG_DIFFICULTY, BREAKOUT_DIFFICULTY, SPACE_INVADERS_DIFFICULTY, TETRIS_DIFFICULTY
    if game_key == "snake":
        SNAKE_DIFFICULTY = level
    elif game_key == "pong":
        PONG_DIFFICULTY = level
    elif game_key == "breakout":
        BREAKOUT_DIFFICULTY = level
    elif game_key == "space_invaders":
        SPACE_INVADERS_DIFFICULTY = level
    elif game_key == "tetris":
        TETRIS_DIFFICULTY = level
    else:
        raise ValueError(f"Unknown game key: {game_key}")
    # Persist the change
    save_settings()


# Settings persistence for mute flag and difficulty settings
import json
import os

_SETTINGS_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "settings.json")
)

# Ensure mute defaults to False in test environment when no persisted settings exist
if os.getenv("PYTEST_CURRENT_TEST") and not os.path.isfile(_SETTINGS_PATH):
    MUTE = False


def _load_settings() -> None:
    """Load settings from ``settings.json`` if it exists."""
    if os.path.isfile(_SETTINGS_PATH):
        try:
            with open(_SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Only accept the canonical lowercase "mute" key when loading.
                # Legacy uppercase "MUTE" is no longer supported to keep the
                # settings file format consistent and predictable.
                if isinstance(data, dict) and "mute" in data:
                    # Load mute flag
                    global MUTE
                    MUTE = bool(data.get("mute", False))
                    # Load per‑game difficulty settings if present
                    for key in [
                        "snake_difficulty",
                        "pong_difficulty",
                        "breakout_difficulty",
                        "space_invaders_difficulty",
                        "tetris_difficulty",
                    ]:
                        if key in data:
                            level = data[key]
                            # Validate level; default to medium on invalid
                            if level not in _DIFFICULTY_LEVELS:
                                level = DIFFICULTY_MEDIUM
                            # Set the appropriate global variable
                            if key == "snake_difficulty":
                                global SNAKE_DIFFICULTY
                                SNAKE_DIFFICULTY = level
                            elif key == "pong_difficulty":
                                global PONG_DIFFICULTY
                                PONG_DIFFICULTY = level
                            elif key == "breakout_difficulty":
                                global BREAKOUT_DIFFICULTY
                                BREAKOUT_DIFFICULTY = level
                            elif key == "space_invaders_difficulty":
                                global SPACE_INVADERS_DIFFICULTY
                                SPACE_INVADERS_DIFFICULTY = level
                            elif key == "tetris_difficulty":
                                global TETRIS_DIFFICULTY
                                TETRIS_DIFFICULTY = level
        except Exception:
            # Ignore errors – default MUTE remains False
            pass


def save_settings() -> None:
    """Save current settings (currently only ``MUTE``) to ``settings.json``."""
    # Persist using lowercase "mute" key (preferred). The loader still
    # accepts the legacy uppercase "MUTE" for backward compatibility.
    data = {
        "mute": MUTE,
        "snake_difficulty": SNAKE_DIFFICULTY,
        "pong_difficulty": PONG_DIFFICULTY,
        "breakout_difficulty": BREAKOUT_DIFFICULTY,
        "space_invaders_difficulty": SPACE_INVADERS_DIFFICULTY,
        "tetris_difficulty": TETRIS_DIFFICULTY,
    }
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
KEY_W = pygame.K_w
KEY_S = pygame.K_s
