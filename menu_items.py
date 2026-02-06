"""Utility module providing the list of menu items for the arcade engine.

The function ``get_menu_items`` returns a list of tuples ``(display_name, state_class)``
which the ``MenuState`` uses to build the menu and transition to the appropriate game
state when the user selects an entry.
"""

# Import the state classes from each game module
from games.snake import SnakeState
from games.pong import PongState
from games.breakout import BreakoutState
from games.space_invaders import SpaceInvadersState
from games.tetris import TetrisState
from games.settings import SettingsState


from typing import List, Tuple, Type
from engine import State


def get_menu_items() -> List[Tuple[str, Type[State]]]:
    """Return menu items as ``(name, state_class)`` tuples.

    The order matches the original menu order in ``main.py``.
    """
    # Settings UI is added as the last option with a lighter colour.
    return [
        ("Snake", SnakeState),
        ("Pong", PongState),
        ("Breakout", BreakoutState),
        ("Space Invaders", SpaceInvadersState),
        ("Tetris", TetrisState),
        ("Settings", SettingsState),
    ]
