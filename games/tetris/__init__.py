"""Tetris game package.

Exports:
- ``TetrisState`` – the game state class.
- ``run()`` – convenience function to launch the game.
"""

from .tetris import TetrisState
from games.run_helper import run_game

__all__ = ["TetrisState", "run"]


def run():
    """Run the Tetris game using the default engine FPS."""
    run_game(TetrisState)
