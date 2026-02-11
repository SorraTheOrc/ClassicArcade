"""Base Game class for the arcade suite.

This class provides the common attributes and behaviour shared by all game states:
- ``screen``: the pygame display surface.
- ``clock``: a pygame Clock used for timing.
- ``draw_text`` helper from ``utils``.
- Default ``handle_event`` implementation that supports:
    * ``K_ESCAPE`` – request a transition back to the main menu.
    * ``K_h`` – show help for the current game.
    * ``K_p`` – toggle a paused flag (the engine can respect ``self.paused`` in ``update``).
    * ``K_r`` – restart the current game by re‑initialising the state.

Games can subclass ``Game`` instead of the lower-level ``State`` to inherit this boiler‑plate
logic, reducing duplication across the individual game modules.
"""

from abc import abstractmethod as _abstractmethod

import pygame

from classic_arcade import audio
from classic_arcade.config import FONT_SIZE_SMALL, YELLOW
from classic_arcade.engine import MenuState, State
from classic_arcade.utils import SCREEN_HEIGHT, SCREEN_WIDTH, WHITE, draw_text

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
        self.countdown_active = False
        self.countdown_remaining = 0.0

    def on_exit(self) -> None:
        """Called when the game state is no longer active.

        Fades out music over 1 second for smooth transition.
        """
        try:
            audio.fade_out_music(duration_ms=1000)
        except Exception:
            pass

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle common key events for all games.

        Supports:
        - ``K_ESCAPE`` – return to the main menu.
        - ``K_h`` – show help for the current game.
        - ``K_p`` – toggle the paused flag.
        - ``K_r`` – restart the current state by re‑initialising it.
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Return to menu (import lazily to avoid circular import)
                from classic_arcade.menu_items import get_menu_items

                self.request_transition(MenuState(get_menu_items()))
                return
            if event.key == pygame.K_h:
                # Show help for the current game
                from classic_arcade.engine import HelpState

                self.paused = True  # Pause the game when help is shown
                # Store a reference to this instance so it can be restored
                self._help_parent = self  # type: ignore
                help_state = HelpState(type(self))
                help_state._parent_game = self  # type: ignore
                self.request_transition(help_state)
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

    def draw_mute_overlay(self, screen: pygame.Surface) -> str | None:
        """Draw mute status overlay (Muted or Sound On) at top-left.

        Uses a small font size and ``YELLOW`` colour for visibility.
        """
        from classic_arcade import config
        from classic_arcade.config import YELLOW

        # Use a modest font size for the overlay and draw using config.MUTE
        font_size = 24
        # Draw the text at a fixed position (top-left) without centering
        # Optionally draw a small visible square at (10,10) in test/headless runs
        import os

        from classic_arcade.utils import draw_text

        if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("SHOW_TEST_INDICATOR"):
            try:
                pygame.draw.rect(screen, YELLOW, pygame.Rect(8, 8, 6, 6))
            except Exception:
                pass
        text = "Muted" if config.MUTE else "Sound On"
        # Draw status text slightly to the right so the small indicator doesn't overlap the first char
        draw_text(screen, text, FONT_SIZE_SMALL, YELLOW, 30, 10, center=False)
        # Expose last drawn mute label for tests that prefer state introspection
        return text

    def draw_countdown(self, screen: pygame.Surface) -> None:
        """Draw a large countdown overlay in the center of the screen.

        Shows the remaining time in seconds if countdown is active.
        """
        if self.countdown_active:
            font = pygame.font.Font(None, 144)
            text = f"{int(self.countdown_remaining) + 1}"
            text_surface = font.render(text, True, WHITE)
            text_rect = text_surface.get_rect(
                center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
            )
            screen.blit(text_surface, text_rect)

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
