"""Breakout game package.

Exports:
- ``BreakoutState`` – the game state class.
- ``run()`` – convenience function to launch the game.
"""

from .breakout import BreakoutState
from games.run_helper import run_game

__all__ = ["BreakoutState", "run"]


def run():
    """Run the Breakout game using the default engine FPS."""
    run_game(BreakoutState)
