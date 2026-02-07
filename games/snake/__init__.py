"""Snake game package.

Exports:
- ``SnakeState`` – the game state class.
- ``SNAKE_SPEED`` – FPS used for the snake game.
- ``run()`` – convenience function to launch the game.
"""

from games.run_helper import run_game

from .snake import SnakeState, get_snake_speed

__all__ = ["SnakeState", "run"]


def run() -> None:
    """Run the Snake game using its default speed as FPS."""
    run_game(SnakeState, fps=get_snake_speed())
