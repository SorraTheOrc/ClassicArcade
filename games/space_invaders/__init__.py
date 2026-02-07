"""Space Invaders game package.

Exports:
- ``SpaceInvadersState`` – the game state class.
- ``run()`` – convenience function to launch the game.
"""

from games.run_helper import run_game

from .space_invaders import (
    ALIEN_COLS,
    ALIEN_ROWS,
    BULLET_HEIGHT,
    BULLET_SPEED,
    BULLET_WIDTH,
    NUM_SHELTERS,
    PLAYER_HEIGHT,
    PLAYER_WIDTH,
    SHELTER_COLOR,
    SHELTER_HEIGHT,
    SHELTER_WIDTH,
    SpaceInvadersState,
)

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
