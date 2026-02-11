# games/run_helper.py
"""Helper module to run a game state using the Engine.

Provides a single entry point for the standalone execution of game modules.
The helper abstracts the repetitive boilerplate of creating the state,
instantiating the :class:`engine.Engine`, and starting the main loop.

Usage::

    from games.run_helper import run_game
    from games.pong import PongState

    # Run Pong with the default engine FPS (60)
    run_game(PongState)

    # Run Snake with a custom FPS (its own speed constant)
    from games.snake import SNAKE_SPEED, SnakeState
    run_game(SnakeState, fps=SNAKE_SPEED)
"""

from typing import Optional, Type

from classic_arcade.engine import Engine, State


def run_game(state_cls: Type[State], fps: Optional[int] = None) -> None:
    """Instantiate and run a game state using the :class:`engine.Engine`.

    Args:
        state_cls: The game state class (subclass of ``Game`` or ``State``).
        fps: Optional frames‑per‑second override. If omitted the Engine's default
            of 60 FPS is used.
    """
    # Instantiate the state
    state = state_cls()
    # Create the engine, passing fps if supplied
    engine = Engine(state, fps=fps) if fps is not None else Engine(state)
    # Run the main loop – this will block until the user quits or the state exits
    engine.run()


__all__ = ["run_game"]
