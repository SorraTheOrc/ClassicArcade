# main.py
"""Main entry point for the arcade suite.
Provides a loading screen with a menu to select one of the classic arcade games.
Implemented using the new ``Engine`` and ``MenuState`` for a unified state machine.
"""

from engine import Engine, MenuState
from menu_items import get_menu_items


def main():
    """Run the arcade suite using the state machine engine."""
    initial_state = MenuState(get_menu_items())
    engine = Engine(initial_state)
    engine.run()


if __name__ == "__main__":
    main()
