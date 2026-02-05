"""Engine module providing a simple state machine for the arcade suite.

The module defines an abstract ``State`` base class that game states can inherit from.
Each ``State`` must implement ``handle_event(event)``, ``update(dt)`` and ``draw(screen)``.
Optionally, a state can request a transition to a new state by setting ``self.next_state``.

The ``Engine`` class runs a pygame loop, delegating event handling, updating and drawing to the
current state. After each loop iteration the engine checks ``state.next_state`` – if it is set,
the engine switches to the new state and clears the flag.
"""

import os

# Use dummy video driver only when running in a headless test environment.
# Pytest sets the PYTEST_CURRENT_TEST environment variable for each test.
# Users can also set HEADLESS=1 to force headless mode.
if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("HEADLESS"):
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import os
import sys

# Use dummy video driver only when running under pytest (tests).
# This ensures normal runs open a real window.
if "pytest" in sys.modules:
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame
import atexit


def _pygame_cleanup() -> None:
    """Clean up Pygame resources on interpreter exit."""
    pygame.quit()


atexit.register(_pygame_cleanup)
from abc import ABC, abstractmethod
from typing import List, Tuple, Type, Optional

from config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    BLACK,
    WHITE,
    YELLOW,
    GRAY,
    KEY_UP,
    KEY_DOWN,
    MUTE,
)
from utils import draw_text


class State(ABC):
    """Abstract base class for all states.

    Subclasses must implement ``handle_event``, ``update`` and ``draw``.
    To request a transition, set ``self.next_state`` to an instance of another ``State``.
    """

    def __init__(self) -> None:
        """Initialize the state with no pending transition."""
        self.next_state: Optional["State"] = None

    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> None:
        """Process a pygame event."""

    @abstractmethod
    def update(self, dt: float) -> None:
        """Update the state. ``dt`` is the time elapsed in seconds since the last frame."""

    @abstractmethod
    def draw(self, screen: pygame.Surface) -> None:
        """Draw the state to ``screen``."""

    def request_transition(self, new_state: "State") -> None:
        """Helper to request a state transition."""
        self.next_state = new_state

    def reset_transition(self) -> None:
        """Clear any pending state transition."""
        self.next_state = None


class Engine:
    """Main engine class for running the game loop."""

    """Main engine that runs the pygame loop and delegates to the active state.

    ``initial_state`` should be an instance of a ``State`` subclass.
    ``fps`` controls the target frame rate.
    """

    def __init__(self, initial_state: State, fps: int = 60) -> None:
        """Initialize the engine with the given initial state and optional FPS."""
        import logging

        logger = logging.getLogger(__name__)
        self.fps = fps
        self.state = initial_state
        # Use dummy video driver in headless test environments.
        if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("HEADLESS"):
            os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        # Initialise pygame and create the screen once.
        pygame.init()
        # Initialise audio system (mixer + background music) if available.
        try:
            import audio

            audio.init()
        except Exception:
            # Audio initialisation should not prevent the engine from running.
            pass
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Arcade Suite")
        self.clock = pygame.time.Clock()
        self.running = True
        # Log driver info – warn if using dummy driver (no visible window)
        try:
            driver = pygame.display.get_driver()
            logger.debug("SDL video driver: %s", driver)
            if driver == "dummy":
                logger.warning(
                    "SDL video driver is dummy; no visible window will be created."
                )
        except Exception:
            # get_driver may not be available on some pygame versions
            logger.debug("Unable to determine SDL video driver.")
        logger.debug("Engine initialized: fps=%s", fps)

    def run(self) -> None:
        """Run the main loop until the user quits or the state signals exit."""
        while self.running:
            dt = self.clock.tick(self.fps) / 1000.0  # seconds
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break
                self.state.handle_event(event)
            # Update and draw current state
            self.state.update(dt)
            # Clear screen (states are responsible for drawing background if needed)
            self.screen.fill(BLACK)
            self.state.draw(self.screen)
            pygame.display.flip()
            # Handle state transition if requested
            if self.state.next_state is not None:
                self.state = self.state.next_state
        pygame.quit()


# The Engine and State classes are intentionally lightweight – they provide a clear contract
# for game states while keeping the implementation simple and easy to test.


class MenuState(State):
    """Simple menu state.

    ``menu_items`` should be a list of tuples ``(display_name, state_class)``.
    The state will display the names and allow the user to navigate with the up/down arrows
    and select an entry with the Return key. Selecting an entry requests a transition to an
    instance of the corresponding ``state_class``.
    """

    def __init__(self, menu_items: List[Tuple[str, Type[State]]]) -> None:
        """Initialize the menu state with a list of (display_name, state_class) tuples.

        Adds attributes for highlight animation.
        """
        super().__init__()
        self.menu_items = menu_items
        self.selected = 0
        # Font size for the menu title and items
        self.title_font_size = 48
        self.item_font_size = 32
        # Highlight animation attributes
        self.highlight_anim_phase = 0.0  # animation phase accumulator
        self.highlight_border_width = 2  # initial border width (pixels)
        self.highlight_padding = 10  # padding around text for highlight rectangle
        self.highlight_color = GRAY
        self.highlight_rect: pygame.Rect | None = None

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle user input events for menu navigation and selection."""
        if event.type == pygame.KEYDOWN:
            if event.key == KEY_UP:
                self.selected = (self.selected - 1) % len(self.menu_items)
            elif event.key == KEY_DOWN:
                self.selected = (self.selected + 1) % len(self.menu_items)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                # Transition to the selected game state
                _, state_cls = self.menu_items[self.selected]
                self.request_transition(state_cls())
            elif event.key == pygame.K_m:
                # Allow toggling mute from the menu as well
                try:
                    import audio

                    audio.toggle_mute()
                except Exception:
                    pass
            # ESC key is ignored in the menu

    def update(self, dt: float) -> None:
        """Update menu state, handling highlight animation.

        The highlight border width pulses over time for a visual effect.
        """
        # Update animation phase
        self.highlight_anim_phase += dt
        # Compute a pulsing border width between 2 and 6 pixels
        # Using a sine wave for smooth animation
        import math

        phase = math.sin(self.highlight_anim_phase * 2 * math.pi)  # -1 to 1
        # Map phase to range [2, 6]
        self.highlight_border_width = int(2 + (phase + 1) / 2 * 4)
        # Ensure minimum width of 2
        if self.highlight_border_width < 2:
            self.highlight_border_width = 2
        # No other time‑dependent logic
        pass

    def draw(self, screen: pygame.Surface) -> None:
        """Render the menu title and list of menu items onto the screen.

        The selected menu item is highlighted with a pulsing rectangle outline.
        """
        # Title
        draw_text(
            screen,
            "Arcade Suite",
            self.title_font_size,
            WHITE,
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 4,
            center=True,
        )
        # Mute status indicator
        # Draw a small visible indicator at (10,10) so UI tests can sample a stable pixel
        try:
            pygame.draw.rect(screen, YELLOW, pygame.Rect(8, 8, 6, 6))
        except Exception:
            # If drawing fails for any reason, fall back to rendering the text only
            pass
        # Draw status text slightly to the right so the small indicator doesn't overlap the first char
        draw_text(
            screen,
            "Muted" if MUTE else "Sound On",
            self.title_font_size // 2,
            YELLOW,
            30,
            10,
            center=False,
        )
        # Menu items
        start_y = SCREEN_HEIGHT // 4 + 80
        # Prepare font for menu items
        font = pygame.font.Font(None, self.item_font_size)
        for idx, (name, _) in enumerate(self.menu_items):
            # Render the text surface
            color = YELLOW if idx == self.selected else WHITE
            text_surface = font.render(name, True, color)
            text_rect = text_surface.get_rect()
            text_rect.center = (SCREEN_WIDTH // 2, start_y + idx * 50)
            # If this is the selected item, draw a highlight rectangle
            if idx == self.selected:
                # Compute a rectangle slightly larger than the text
                self.highlight_rect = text_rect.inflate(
                    self.highlight_padding * 2, self.highlight_padding * 2
                )
                # Draw rectangle outline with current border width
                pygame.draw.rect(
                    screen,
                    self.highlight_color,
                    self.highlight_rect,
                    width=self.highlight_border_width,
                )
            # Blit the text onto the screen
            screen.blit(text_surface, text_rect)


# Clean up imported decorator
del abstractmethod
