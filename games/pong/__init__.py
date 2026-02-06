"""Pong game package.

Exports:
- ``PongState`` – the game state class.
- ``run()`` – convenience function to launch the game.
"""

from .pong import PongState, PongSinglePlayerState, PongMultiplayerState
from games.run_helper import run_game

__all__ = ["PongState", "PongSinglePlayerState", "PongMultiplayerState", "run"]


def run() -> None:
    """Run the Pong game using the default engine FPS."""
    run_game(PongState)
