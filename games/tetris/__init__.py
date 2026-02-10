"""Tetris game package.

Exports:
- ``TetrisState`` – the game state class (single player).
- ``Tetris2PlayerState`` – the 2-player versus game state.
- ``TetrisModeSelectState`` – mode selection screen.
- ``run()`` – convenience function to launch the game.
"""

from games.run_helper import run_game

from .tetris import (
    Tetris2PlayerState,
    TetrisModeSelectState,
    TetrisState,
)

__all__ = ["TetrisState", "Tetris2PlayerState", "TetrisModeSelectState", "run"]


def run() -> None:
    """Run the Tetris game using the default engine FPS."""
    run_game(TetrisState)
