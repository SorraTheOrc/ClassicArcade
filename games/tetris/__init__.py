"""Tetris game package.

Exports:
- ``TetrisState`` – the game state class.
- ``run()`` – convenience function to launch the game.
"""

from games.run_helper import run_game

from .tetris import TetrisState

__all__ = ["TetrisState", "run"]


def run() -> None:
    """Run the Tetris game using the default engine FPS."""
    run_game(TetrisState)
