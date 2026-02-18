"""Difficulty scaling utilities for arcade games.

Provides a shared implementation for difficulty-based speed scaling
across all classic arcade games.
"""

from classic_arcade import config


def apply_difficulty_multiplier(
    base_value: float, game_key: str, custom_multiplier: float | None = None
) -> int:
    """Apply difficulty multiplier to a base value and return as integer.

    Args:
        base_value: The base value to scale (e.g., base speed).
        game_key: The game identifier ('snake', 'pong', 'breakout',
                  'space_invaders', 'tetris').
        custom_multiplier: Optional custom multiplier to use instead of the
                           game's default difficulty multiplier.

    Returns:
        The scaled value as an integer.
    """
    if custom_multiplier is None:
        multiplier = config.difficulty_multiplier(config.get_difficulty(game_key))
    else:
        multiplier = custom_multiplier
    return int(base_value * multiplier)


def apply_difficulty_divisor(
    base_value: float, game_key: str, custom_multiplier: float | None = None
) -> int:
    """Apply difficulty divisor to a base value and return as integer.

    Use this for values that should decrease with higher difficulty
    (e.g., time intervals, cooldowns).

    Args:
        base_value: The base value to scale (e.g., base interval in ms).
        game_key: The game identifier ('snake', 'pong', 'breakout',
                  'space_invaders', 'tetris').
        custom_multiplier: Optional custom multiplier to use instead of the
                           game's default difficulty multiplier.

    Returns:
        The scaled value as an integer.
    """
    if custom_multiplier is None:
        multiplier = config.difficulty_multiplier(config.get_difficulty(game_key))
    else:
        multiplier = custom_multiplier
    return int(base_value / multiplier)
