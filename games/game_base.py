"""Base Game class for the arcade suite.

This class provides the common attributes and behaviour shared by all game states:
- ``screen``: the pygame display surface.
- ``clock``: a pygame Clock used for timing.
- ``draw_text`` helper from ``utils``.
- Default ``handle_event`` implementation that supports:
    * ``K_ESCAPE`` – request a transition back to the main menu.
    * ``K_p`` – toggle a paused flag (the engine can respect ``self.paused`` in ``update``).
    * ``K_r`` – restart the current game by re‑initialising the state.

Games can subclass ``Game`` instead of the lower‑level ``State`` to inherit this boiler‑plate
logic, reducing duplication across the individual game modules.
"""

import os

# Use dummy video driver only when running in a headless test environment.
# Pytest sets the PYTEST_CURRENT_TEST environment variable for each test.
# Users can also set HEADLESS=1 to force headless mode.
if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("HEADLESS"):
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame
from abc import ABC, abstractmethod as _abstractmethod
from config import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, KEY_QUIT, KEY_PAUSE, KEY_RESTART
from utils import draw_text
from engine import State, MenuState


class Game(State):
    """Base class for all games.

    Subclasses should implement ``update`` and ``draw``. The constructor creates a pygame
    screen and clock, and the ``handle_event`` method provides common shortcuts for ESC,
    pause (P) and restart (R).
    """

    def __init__(self) -> None:
        """Initialize the base game state with pygame screen, clock, and default flags."""
        super().__init__()
        # Initialise pygame screen and clock – the engine will also call pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.paused = False
        self.next_state = None

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle common key events for all games.

        Supports:
        - ``KEY_QUIT`` (ESC) to transition back to the main menu.
        - ``KEY_PAUSE`` (P) to toggle the paused flag.
        - ``KEY_RESTART`` (R) to restart the current state by re‑initialising it.
        Subclasses can extend this method and should call ``super().handle_event(event)`` to retain this behaviour.
        """
        if event.type == pygame.KEYDOWN:
            if event.key == KEY_QUIT:
                # Return to menu (import lazily to avoid circular import)
                from menu_items import get_menu_items

                self.request_transition(MenuState(get_menu_items()))
                return
            if event.key == KEY_PAUSE:
                self.paused = not self.paused
                return
            if event.key == KEY_RESTART:
                # Re‑initialise the state – subclasses can override for custom behaviour
                self.__init__()  # type: ignore[misc]
                return
        # Subclasses can extend with additional key handling by calling super().handle_event(event)
        # (no further action needed here)

    @_abstractmethod
    def update(self, dt: float) -> None:
        """Update the game logic. ``dt`` is the time delta in seconds.
        Subclasses should respect ``self.paused`` if they implement time‑dependent updates.
        """
        pass

    @_abstractmethod
    def draw(self, screen: pygame.Surface) -> None:
        """Draw the game to ``screen``. ``screen`` is provided by the engine.
        Subclasses typically clear the background and render their objects.
        """
        pass
