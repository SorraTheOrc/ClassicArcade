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
from abc import abstractmethod as _abstractmethod
from utils import draw_text, WHITE, SCREEN_WIDTH, SCREEN_HEIGHT
from engine import State, MenuState
import audio
# import get_menu_items lazily in handle_event


class Game(State):
    """Base class for all games.

    Subclasses should implement ``update`` and ``draw``. The constructor creates a pygame
    screen and clock, and the ``handle_event`` method provides common shortcuts for ESC,
    pause (P) and restart (R).
    """

    def __init__(self) -> None:
        """Initialize the base game state with screen, clock and pause flag."""
        super().__init__()
        # Initialise pygame screen and clock – the engine will also call pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.paused = False
        self.next_state = None

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle common key events for all games.

        Supports:
        - ``K_ESCAPE`` – return to the main menu.
        - ``K_p`` – toggle the paused flag.
        - ``K_r`` – restart the current state by re‑initialising it.
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Return to menu (import lazily to avoid circular import)
                from menu_items import get_menu_items

                self.request_transition(MenuState(get_menu_items()))
                return
            if event.key == pygame.K_p:
                self.paused = not self.paused
                return
            if event.key == pygame.K_m:
                audio.toggle_mute()
                return
            if event.key == pygame.K_r:
                # Re‑initialise the state – subclasses can override for custom behaviour
                self.__init__()
                return
        # Subclasses can extend with additional key handling by calling super().handle_event(event)
        # (no further action needed here)

    def draw_pause_overlay(self, screen: pygame.Surface) -> None:
        """Draw a semi‑transparent overlay with "Paused" text.

        This method can be called by subclasses after drawing their normal content.
        """
        # Create a semi‑transparent surface the size of the screen
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # 50% black
        screen.blit(overlay, (0, 0))
        # Render the "Paused" text
        font = pygame.font.Font(None, 48)
        text_surface = font.render("Paused", True, WHITE)
        text_rect = text_surface.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        )
        screen.blit(text_surface, text_rect)

    def draw_mute_overlay(self, screen: pygame.Surface) -> None:
        """Draw mute status overlay (Muted or Sound On) at top-left.

        Uses a small font size and ``YELLOW`` colour for visibility.
        """
        from config import MUTE, YELLOW

        # Use a modest font size for the overlay
        font_size = 24
        # Determine text based on mute flag
        text = "Muted" if MUTE else "Sound On"
        # Draw the text at a fixed position (top-left) without centering
        from utils import draw_text

        # Draw a small visible square at (10,10) so UI tests can assert on pixels reliably.
        try:
            pygame.draw.rect(screen, YELLOW, pygame.Rect(8, 8, 6, 6))
        except Exception:
            # Ignore drawing failures in headless/test environments.
            pass
        # Draw status text slightly to the right so the small indicator doesn't overlap the first char
        draw_text(screen, text, font_size, YELLOW, 30, 10, center=False)

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
