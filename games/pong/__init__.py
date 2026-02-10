"""Pong game package.

Exports:
- ``PongState`` – the game state class.
- ``run()`` – convenience function to launch the game.
"""

from games.run_helper import run_game

from .pong import (
    PongModeSelectState,
    PongMultiplayerState,
    PongSinglePlayerState,
    PongState,
)

__all__ = [
    "PongState",
    "PongSinglePlayerState",
    "PongMultiplayerState",
    "PongModeSelectState",
    "run",
]


def run() -> None:
    """Run Pong with mode selection screen."""
    run_game(PongModeSelectState)
