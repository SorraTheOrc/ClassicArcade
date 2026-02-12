# main.py
"""Main entry point for the arcade suite.
Provides a loading screen with a menu to select one of the classic arcade games.
Implemented using the new ``Engine`` and ``MenuState`` for a unified state machine.
"""

from classic_arcade import audio
from classic_arcade.engine import Engine, MenuState
from classic_arcade.menu_items import get_menu_items
from games.splash import SplashState


def main() -> None:
    """Run the arcade suite using the state machine engine.

    The ``--verbose`` flag now enables detailed startup logging while still launching the game.
    """
    # Argument parsing for optional verbose output
    import argparse
    import logging
    import os

    parser = argparse.ArgumentParser(description="Arcade Suite")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose startup logging.",
    )
    args = parser.parse_args()

    # Configure logging based on verbosity
    import sys

    log_level = logging.DEBUG if args.verbose else logging.INFO
    log_handlers = []
    log_format = "[%(levelname)s] %(message)s"

    if getattr(sys, "frozen", False):
        log_dir = os.path.dirname(sys.executable)
    else:
        log_dir = os.getcwd()
    log_path = os.path.join(log_dir, "classic-arcade.log")
    try:
        log_handlers.append(logging.FileHandler(log_path, encoding="utf-8"))
    except Exception:
        pass
    if args.verbose:
        log_handlers.append(logging.StreamHandler())

    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=log_handlers or None,
    )
    logger = logging.getLogger(__name__)
    import time

    start_time = time.perf_counter()

    def log_step(message: str) -> None:
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        logger.debug("Timing: %s (%.2fms)", message, elapsed_ms)

    # Log configuration and available games
    from classic_arcade.config import SCREEN_HEIGHT, SCREEN_WIDTH

    logger.info("Starting Arcade Suite")
    if getattr(sys, "frozen", False):
        logger.info(
            "Running frozen executable (onefile bootloader unpack time not logged)"
        )
    logger.debug("Screen size: %dx%d", SCREEN_WIDTH, SCREEN_HEIGHT)
    logger.debug("Available games:")
    for name, _, _ in get_menu_items():
        logger.debug(" - %s", name)

    # Ensure pygame quits cleanly on unexpected exit
    import atexit
    import os

    import pygame

    def _cleanup() -> None:
        pygame.quit()

    atexit.register(_cleanup)
    # Warn if DISPLAY is not set – WSL needs an X server.
    if os.name != "nt" and not os.getenv("DISPLAY"):
        logger.warning(
            "DISPLAY environment variable not set. In WSL you need to run an X server (e.g., VcXsrv) and set DISPLAY, e.g., \n"
            "    export DISPLAY=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}'):0\n"
            "or \n    export DISPLAY=:0.0"
        )
        # No display available – exit gracefully to avoid hanging in a headless environment.
        logger.info("No DISPLAY detected – exiting without launching the graphical UI.")
        return

    menu_items = get_menu_items()
    log_step("menu discovery complete")

    initial_state = SplashState()
    engine = Engine(initial_state)
    log_step("engine initialized")
    audio.init()
    log_step("audio initialized")
    engine.run()


if __name__ == "__main__":
    main()


__all__ = ["main"]
