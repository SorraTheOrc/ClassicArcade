"""Snake game package.

Exports:
- ``SnakeState`` – the game state class.
- ``SNAKE_SPEED`` – FPS used for the snake game.
- ``run()`` – convenience function to launch the game.
"""

from .snake import SnakeState, SNAKE_SPEED
from games.run_helper import run_game

__all__ = ["SnakeState", "SNAKE_SPEED", "run"]


def run():
    """Run the Snake game using its default speed as FPS."""
    run_game(SnakeState, fps=SNAKE_SPEED)
