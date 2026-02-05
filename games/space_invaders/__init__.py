"""Space Invaders game package.

Exports:
- ``SpaceInvadersState`` – the game state class.
- ``run()`` – convenience function to launch the game.
"""

from .space_invaders import (
    SpaceInvadersState,
    BULLET_SPEED,
    BULLET_HEIGHT,
    BULLET_WIDTH,
    PLAYER_HEIGHT,
    PLAYER_WIDTH,
    ALIEN_ROWS,
    ALIEN_COLS,
    SHELTER_COLOR,
    SHELTER_WIDTH,
    SHELTER_HEIGHT,
    NUM_SHELTERS,
)

from games.run_helper import run_game

__all__ = [
    "SpaceInvadersState",
    "run",
    "BULLET_SPEED",
    "BULLET_HEIGHT",
    "BULLET_WIDTH",
    "PLAYER_HEIGHT",
    "PLAYER_WIDTH",
    "ALIEN_ROWS",
    "ALIEN_COLS",
    "SHELTER_COLOR",
    "SHELTER_WIDTH",
    "SHELTER_HEIGHT",
    "NUM_SHELTERS",
]


def run() -> None:
    """Run Space Invaders using the default engine FPS."""
    run_game(SpaceInvadersState)
