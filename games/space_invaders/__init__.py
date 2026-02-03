"""Space Invaders game package.

Exports:
- ``SpaceInvadersState`` – the game state class.
- ``run()`` – convenience function to launch the game.
"""

from .space_invaders import *  # re-export all module symbols for tests

from games.run_helper import run_game

__all__ = [name for name in globals().keys() if not name.startswith("_")]


def run():
    """Run Space Invaders using the default engine FPS."""
    run_game(SpaceInvadersState)
