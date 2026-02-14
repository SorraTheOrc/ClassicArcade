"""Space Invaders Redux game package.

This package provides a moddable version of Space Invaders that allows
users to create and share custom alien types through mods.

Exports:
    - ``SpaceInvadersReduxState``: The game state class
    - ``run()``: Convenience function to launch the game
    - ``get_mod_loader()``: Get the global mod loader instance
    - ``load_alien_types()``: Load all alien types from mods

Usage:
    To launch the game directly:
        from games.space_invaders_redux import run
        run()

    To use the modding system:
        from games.space_invaders_redux import get_mod_loader, load_alien_types
        loader = get_mod_loader()
        loader.discover_mods()
        alien_types = load_alien_types()
"""

from games.run_helper import run_game

from .alien_loader import get_mod_loader, load_alien_types
from .space_invaders_redux import SpaceInvadersReduxState

__all__ = [
    "SpaceInvadersReduxState",
    "run",
    "get_mod_loader",
    "load_alien_types",
]


def run() -> None:
    """Run Space Invaders Redux using the default engine FPS."""
    run_game(SpaceInvadersReduxState)
