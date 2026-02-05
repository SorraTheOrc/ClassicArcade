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

import pygame
from abc import ABC, abstractmethod
from utils import draw_text, WHITE, SCREEN_WIDTH, SCREEN_HEIGHT
from engine import State, MenuState
# import get_menu_items lazily in handle_event


class Game(State):
    """Base class for all games.

    Subclasses should implement ``update`` and ``draw``. The constructor creates a pygame
    screen and clock, and the ``handle_event`` method provides common shortcuts for ESC,
    pause (P) and restart (R).
    """

    def __init__(self):
        super().__init__()
        # Initialise pygame screen and clock – the engine will also call pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.paused = False
        self.next_state = None

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Return to menu (import lazily to avoid circular import)
                from menu_items import get_menu_items

                self.request_transition(MenuState(get_menu_items()))
                return
            if event.key == pygame.K_p:
                self.paused = not self.paused
                return
            if event.key == pygame.K_r:
                # Re‑initialise the state – subclasses can override for custom behaviour
                self.__init__()
                return
        # Subclasses can extend with additional key handling by calling super().handle_event(event)
        # (no further action needed here)

    @abstractmethod
    def update(self, dt: float) -> None:
        """Update the game logic. ``dt`` is the time delta in seconds.
        Subclasses should respect ``self.paused`` if they implement time‑dependent updates.
        """
        pass

    @abstractmethod
    def draw(self, screen: pygame.Surface) -> None:
        """Draw the game to ``screen``. ``screen`` is provided by the engine.
        Subclasses typically clear the background and render their objects.
        """
        pass
