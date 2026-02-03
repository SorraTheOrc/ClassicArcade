"""Space Invaders game package.

Exports:
- ``SpaceInvadersState`` – the game state class.
- ``run()`` – convenience function to launch the game.
"""

from .space_invaders import SpaceInvadersState
from games.run_helper import run_game

__all__ = ["SpaceInvadersState", "run"]


def run():
    """Run Space Invaders using the default engine FPS."""
    run_game(SpaceInvadersState)
