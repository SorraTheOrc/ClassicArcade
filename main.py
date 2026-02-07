# main.py
"""Main entry point for the arcade suite.
Provides a loading screen with a menu to select one of the classic arcade games.
Implemented using the new ``Engine`` and ``MenuState`` for a unified state machine.
"""

import audio
from engine import Engine, MenuState
from games.splash import SplashState
from menu_items import get_menu_items


def main() -> None:
    """Run the arcade suite using the state machine engine.

    The ``--verbose`` flag now enables detailed startup logging while still launching the game.
    """
    # Argument parsing for optional verbose output
    import argparse
    import logging

    parser = argparse.ArgumentParser(description="Arcade Suite")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose startup logging.",
    )
    args = parser.parse_args()

    # Configure logging based on verbosity
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="[%(levelname)s] %(message)s",
    )
    logger = logging.getLogger(__name__)

    # Log configuration and available games
    from config import SCREEN_HEIGHT, SCREEN_WIDTH

    logger.info("Starting Arcade Suite")
    logger.debug("Screen size: %dx%d", SCREEN_WIDTH, SCREEN_HEIGHT)
    logger.debug("Available games:")
    for name, _ in get_menu_items():
        logger.debug(" - %s", name)

    # Ensure pygame quits cleanly on unexpected exit
    import atexit
    import os

    import pygame

    def _cleanup() -> None:
        pygame.quit()

    atexit.register(_cleanup)
    # Warn if DISPLAY is not set – WSL needs an X server.
    if not os.getenv("DISPLAY"):
        logger.warning(
            "DISPLAY environment variable not set. In WSL you need to run an X server (e.g., VcXsrv) and set DISPLAY, e.g., \n"
            "    export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0\n"
            "or \n    export DISPLAY=:0.0"
        )
        # No display available – exit gracefully to avoid hanging in a headless environment.
        logger.info("No DISPLAY detected – exiting without launching the graphical UI.")
        return
    initial_state = SplashState()
    engine = Engine(initial_state)
    audio.init()
    engine.run()


if __name__ == "__main__":
    main()
