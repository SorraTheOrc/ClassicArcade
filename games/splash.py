# games/splash.py
"""Splash screen state for the arcade suite.

Displays a simple title with a fade‑in effect, holds briefly, then transitions to the main menu.
"""

import pygame

from config import BLACK, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE
from engine import MenuState, State
from menu_items import get_menu_items


class SplashState(State):
    """State that shows a splash screen with fade‑in.

    The splash fades in over ``FADE_DURATION`` seconds, holds for ``HOLD_DURATION`` seconds,
    then automatically transitions to the main menu.
    """

    FADE_DURATION = 1.0  # seconds for fade‑in
    HOLD_DURATION = 1.0  # seconds to hold after fully visible

    def __init__(self) -> None:
        super().__init__()
        self.elapsed: float = 0.0
        self.alpha: int = 0  # 0‑255 opacity of the title text
        # Prepare a font for the splash title – size chosen to be readable
        # Ensure the font module is initialized before creating a Font object
        pygame.font.init()
        self._font = pygame.font.Font(None, 48)
        # Pre‑render the text surface (without alpha) – we will apply alpha each frame
        self._text_surface = self._font.render("Arcade Suite", True, WHITE)
        self._text_rect = self._text_surface.get_rect(
            center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        )

    def handle_event(self, event: pygame.event.Event) -> None:
        """Ignore input during the splash.

        The splash is purely visual – user input does not affect it.
        """
        # No interaction needed – keep method for interface compatibility.
        pass

    def update(self, dt: float) -> None:
        """Advance the timer and handle the fade‑in / transition logic.

        ``dt`` – time delta in seconds since the last frame.
        """
        self.elapsed += dt
        # Fade‑in phase
        if self.elapsed < self.FADE_DURATION:
            # Linear interpolation of alpha from 0 to 255
            self.alpha = int(255 * (self.elapsed / self.FADE_DURATION))
        else:
            # Fully visible after fade duration
            self.alpha = 255
        # Transition after hold period
        if self.elapsed >= self.FADE_DURATION + self.HOLD_DURATION:
            # Request transition to the menu state
            self.request_transition(MenuState(get_menu_items()))

    def draw(self, screen: pygame.Surface) -> None:
        """Render the splash screen.

        The background is black; the title text fades in using the current ``alpha`` value.
        """
        screen.fill(BLACK)
        # Apply current alpha to the pre‑rendered text surface
        text_surface = self._text_surface.copy()
        text_surface.set_alpha(self.alpha)
        screen.blit(text_surface, self._text_rect)


__all__ = ["SplashState"]
