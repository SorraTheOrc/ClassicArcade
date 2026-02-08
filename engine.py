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
import atexit

import pygame


def _pygame_cleanup() -> None:
    """Clean up Pygame resources on interpreter exit."""
    pygame.quit()


atexit.register(_pygame_cleanup)
import colorsys
import hashlib
import logging
import os
from abc import ABC, abstractmethod
from typing import List, Optional, Tuple, Type

import config
from config import (
    BLACK,
    GRAY,
    KEY_DOWN,
    KEY_UP,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WHITE,
    YELLOW,
)
from utils import draw_text

# Path to a shared default icon used when a game does not provide its own.
# Expected location: <project_root>/assets/icons/default_game_icon.png (or .svg).
_DEFAULT_ICON_PATH = None
# Path to a custom Settings icon (optional).
# Expected location: <project_root>/assets/icons/settings_icon.png (or .svg).
_SETTINGS_ICON_PATH = None
_default_icon_dir = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "assets", "icons")
)
_default_png = os.path.join(_default_icon_dir, "default_game_icon.png")
_default_svg = os.path.join(_default_icon_dir, "default_game_icon.svg")
if os.path.isfile(_default_png):
    DEFAULT_ICON_PATH = _default_png
elif os.path.isfile(_default_svg):
    DEFAULT_ICON_PATH = _default_svg
# Detect optional Settings icon.
_settings_png = os.path.join(_default_icon_dir, "settings_icon.png")
_settings_svg = os.path.join(_default_icon_dir, "settings_icon.svg")
if os.path.isfile(_settings_png):
    _SETTINGS_ICON_PATH = _settings_png
elif os.path.isfile(_settings_svg):
    _SETTINGS_ICON_PATH = _settings_svg


def _hue_offset_from_name(name: str) -> float:
    """Deterministically compute a hue offset in the range [0, 1) from a name.
    Uses SHA‑256 to get a stable integer across runs.
    """
    digest = hashlib.sha256(name.encode("utf-8")).hexdigest()
    # Use first 8 hex digits (32 bits) for the offset
    int_val = int(digest[:8], 16)
    return (int_val % 360) / 360.0


def _apply_hue_shift(surface: pygame.Surface, name: str) -> pygame.Surface:
    """Shift the hue of *surface* by a deterministic amount based on *name*.
    Returns the same surface (modified in‑place) for convenience.
    """
    hue_offset = _hue_offset_from_name(name)
    w, h = surface.get_size()
    # Iterate over each pixel; skip fully transparent pixels.
    for x in range(w):
        for y in range(h):
            r, g, b, a = surface.get_at((x, y))
            if a == 0:
                continue
            # Convert RGB (0‑255) to HSV (0‑1)
            h0, s0, v0 = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
            # Apply hue offset and wrap around
            h1 = (h0 + hue_offset) % 1.0
            r1, g1, b1 = colorsys.hsv_to_rgb(h1, s0, v0)
            surface.set_at((x, y), (int(r1 * 255), int(g1 * 255), int(b1 * 255), a))
    return surface


logger = logging.getLogger(__name__)


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

    def __init__(self, menu_items: List[Tuple[str, object, str | None]]) -> None:
        """Initialize the menu state with a list of (display_name, launch_target) tuples.

        A launch_target is either a State subclass (preferred) or a callable ``run`` function.
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
        # Last rendered mute text (for tests)
        self._last_mute_text: str | None = None

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle user input events for menu navigation and selection."""
        if event.type == pygame.KEYDOWN:
            if event.key == KEY_UP:
                self.selected = (self.selected - 1) % len(self.menu_items)
            elif event.key == KEY_DOWN:
                self.selected = (self.selected + 1) % len(self.menu_items)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                # Transition to the selected game state or run callable
                _, launch_target, _ = self.menu_items[self.selected]
                if isinstance(launch_target, type) and issubclass(launch_target, State):
                    self.request_transition(launch_target())
                elif callable(launch_target):
                    try:
                        launch_target()
                    except Exception:
                        logger.exception("Failed to launch game %s", launch_target)
                else:
                    logger.warning(
                        "Menu item %s has unrecognized launch target",
                        self.menu_items[self.selected][0],
                    )
            elif event.key == pygame.K_m:
                # Allow toggling mute from the menu as well
                try:
                    import audio

                    audio.toggle_mute()
                except Exception:
                    pass
            elif event.key == pygame.K_s:
                # Open settings UI
                from games.settings import SettingsState

                self.request_transition(SettingsState())
                return
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
        # Title - draw at the very top
        draw_text(
            screen,
            "Arcade Suite",
            self.title_font_size,
            WHITE,
            SCREEN_WIDTH // 2,
            30,  # small top margin
            center=True,
        )
        # Mute status indicator
        # Optionally draw a small visible indicator in test/headless runs
        if os.getenv("PYTEST_CURRENT_TEST") or os.getenv("SHOW_TEST_INDICATOR"):
            try:
                pygame.draw.rect(screen, YELLOW, pygame.Rect(8, 8, 6, 6))
            except Exception:
                pass
        # Draw status text slightly to the right so the small indicator doesn't overlap the first char
        text = "Muted" if config.MUTE else "Sound On"
        draw_text(screen, text, self.title_font_size // 2, YELLOW, 30, 10, center=False)
        # Expose last rendered text for tests
        self._last_mute_text = text
        # Menu items - display each game as a square box in a grid layout
        num_items = len(self.menu_items)
        if num_items == 0:
            # Nothing to draw
            return
        # Define box size (square). 40 characters approximated as 200 pixels.
        BOX_SIZE = 160  # pixel size of each square box
        # Spacing between boxes (both horizontally and vertically)
        H_SPACING = 20
        V_SPACING = 20
        # Determine how many columns fit horizontally
        columns = max(1, SCREEN_WIDTH // (BOX_SIZE + H_SPACING))
        # Compute horizontal offset to center the grid
        total_grid_width = columns * (BOX_SIZE + H_SPACING) - H_SPACING
        start_x = (SCREEN_WIDTH - total_grid_width) // 2
        # Determine vertical start position (just below the title)
        margin_top = self.title_font_size + 20  # space below title
        start_y = margin_top
        # Prepare font for menu items
        font = pygame.font.Font(None, self.item_font_size)
        for idx, (name, _, icon_path) in enumerate(self.menu_items):
            # Determine column and row for this item
            col = idx % columns
            row = idx // columns
            box_x = start_x + col * (BOX_SIZE + H_SPACING)
            box_y = start_y + row * (BOX_SIZE + V_SPACING)
            # Render the text surface first (to know its height)
            if name == "Settings":
                base_color = GRAY
            else:
                base_color = WHITE
            color = YELLOW if idx == self.selected else base_color
            text_surface = font.render(name, True, color)

            # Compute max icon size to fill the square box while preserving a margin for the game name text
            max_icon_dim = max(
                16, BOX_SIZE - text_surface.get_height() - 10
            )  # 5px margin above and below

            # Determine icon surface (scaled to fit within the computed size)
            if icon_path:
                try:
                    icon_img = pygame.image.load(icon_path).convert_alpha()
                    # Scale icon to fit within max_icon_dim (maintaining square shape)
                    icon_surface = pygame.transform.smoothscale(
                        icon_img, (max_icon_dim, max_icon_dim)
                    )
                    # No hue shift applied for game-specific icons
                except Exception:
                    icon_surface = None
            else:
                icon_surface = None
            if icon_surface is None:
                # Try to load shared default icon if available
                if DEFAULT_ICON_PATH and name != "Settings":
                    try:
                        default_img = pygame.image.load(
                            DEFAULT_ICON_PATH
                        ).convert_alpha()
                        icon_surface = pygame.transform.smoothscale(
                            default_img, (max_icon_dim, max_icon_dim)
                        )
                        # Apply deterministic hue shift based on game name
                        icon_surface = _apply_hue_shift(icon_surface, name)
                    except Exception:
                        icon_surface = None
                # Try Settings-specific icon if available
                # Try Settings-specific icon if available
                if icon_surface is None and name == "Settings" and _SETTINGS_ICON_PATH:
                    try:
                        settings_img = pygame.image.load(
                            _SETTINGS_ICON_PATH
                        ).convert_alpha()
                        icon_surface = pygame.transform.smoothscale(
                            settings_img, (max_icon_dim, max_icon_dim)
                        )
                        # No hue shift applied for Settings icon
                    except Exception:
                        icon_surface = None
                # Final fallback: gray placeholder
                if icon_surface is None:
                    icon_surface = pygame.Surface(
                        (max_icon_dim, max_icon_dim), pygame.SRCALPHA
                    )
                    icon_surface.fill(GRAY)
            # Compute positions inside the box
            # Center icon horizontally at the top of the box with a small margin
            icon_x = box_x + (BOX_SIZE - icon_surface.get_width()) // 2
            icon_y = box_y + 5
            # Position text below the icon with a small margin
            text_x = box_x + (BOX_SIZE - text_surface.get_width()) // 2
            text_y = icon_y + icon_surface.get_height() + 5
            # If this is the selected item, draw a highlight rectangle around the whole box
            if idx == self.selected:
                self.highlight_rect = pygame.Rect(
                    box_x, box_y, BOX_SIZE, BOX_SIZE
                ).inflate(self.highlight_padding * 2, self.highlight_padding * 2)
                pygame.draw.rect(
                    screen,
                    self.highlight_color,
                    self.highlight_rect,
                    width=self.highlight_border_width,
                )
            # Draw icon and text
            screen.blit(icon_surface, (icon_x, icon_y))
            screen.blit(text_surface, (text_x, text_y))
        # After drawing all boxes, check if grid extends beyond screen bottom
        rows = (num_items + columns - 1) // columns
        grid_bottom = start_y + rows * (BOX_SIZE + V_SPACING) - V_SPACING
        if grid_bottom > SCREEN_HEIGHT - 10:
            # Draw a small indicator at bottom center to show more items exist
            draw_text(
                screen,
                "▼",
                self.item_font_size // 2,
                YELLOW,
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT - 10,
                center=True,
            )


# Clean up imported decorator
del abstractmethod
