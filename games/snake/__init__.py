"""Snake game package.

Exports:
- ``SnakeState`` – the game state class (single player).
- ``Snake2PlayerState`` – the 2-player split-screen game state.
- ``SnakeModeSelectState`` – mode selection screen.
- ``SNAKE_SPEED`` – FPS used for the snake game.
- ``run()`` – convenience function to launch the game.
"""

from games.run_helper import run_game

from .snake import (
    Snake2PlayerState,
    SnakeModeSelectState,
    SnakeState,
    get_snake_speed,
)

__all__ = ["SnakeState", "Snake2PlayerState", "SnakeModeSelectState", "run"]


def run() -> None:
    """Run the Snake game with mode selection."""
    run_game(SnakeModeSelectState)
