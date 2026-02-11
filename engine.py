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

try:
    import audio
except Exception:
    # Audio is optional
    audio = None


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
    FONT_SIZE_LARGE,
    FONT_SIZE_MEDIUM,
    FONT_SIZE_SMALL,
    GRAY,
    KEY_DOWN,
    KEY_LEFT,
    KEY_RIGHT,
    KEY_UP,
    MARGIN_LEFT,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WHITE,
    YELLOW,
)
from utils import draw_text, wrap_text

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
else:
    DEFAULT_ICON_PATH = None
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

    def on_enter(self) -> None:
        """Called when this state becomes active."""
        pass

    def on_exit(self) -> None:
        """Called when this state is no longer active."""
        pass


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
            if audio is not None:
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
                # Handle music end event - play new random track
                if audio is not None and hasattr(audio, "MUSIC_END_EVENT"):
                    if event.type == audio.MUSIC_END_EVENT:
                        try:
                            audio.on_music_end()
                        except Exception:
                            pass
                self.state.handle_event(event)
            # Update and draw current state
            self.state.update(dt)
            # Clear screen (states are responsible for drawing background if needed)
            self.screen.fill(BLACK)
            self.state.draw(self.screen)
            pygame.display.flip()
            # Handle state transition if requested
            if self.state.next_state is not None:
                new_state = self.state.next_state
                if hasattr(self.state, "on_exit"):
                    self.state.on_exit()
                self.state = new_state
                if hasattr(self.state, "on_enter"):
                    self.state.on_enter()
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
        Adds attributes for highlight animation and scrolling.
        """
        super().__init__()
        self.menu_items = menu_items
        self.selected = 0
        # Font size for the menu title and items
        self.title_font_size = 48
        self.item_font_size = 32
        # Highlight animation attributes
        self.highlight_anim_phase = 0.0  # animation phase accumulator
        # animation is decoupled from selection; draw() computes border width per-frame
        self.highlight_border_width = 2  # fallback initial border width (pixels)
        self.highlight_padding = 10  # padding around text for highlight rectangle
        self.highlight_color = GRAY
        self.highlight_rect: pygame.Rect | None = None
        # Scrolling attributes
        self.scroll_offset: float = 0.0  # vertical scroll offset in pixels
        # Input repeat handling for instantaneous navigation when holding keys
        self._held_key: int | None = None
        self._hold_start_time: float | None = None
        self._last_repeat_time: float | None = None
        # Initial delay before auto-repeat (seconds) and repeat interval (seconds)
        # Default to no initial delay so a held key immediately repeats; can be tuned
        # via environment for different platforms or preferences.
        self._repeat_initial = float(os.getenv("MENU_KEY_REPEAT_INITIAL", "0.0"))
        self._repeat_interval = float(os.getenv("MENU_KEY_REPEAT_INTERVAL", "0.06"))
        # Debounce repeated keydown events (seconds)
        self._debounce = float(os.getenv("MENU_KEY_DEBOUNCE", "0.04"))
        self._last_keydown_time: float | None = None
        self._last_keydown_key: int | None = None
        # Time origin for decoupled highlight animation
        import time

        self._highlight_start = time.time()
        # Last rendered mute text (for tests)
        self._last_mute_text: str | None = None
        # Last launch message shown to the user (transient)
        self._last_launch_message: str | None = None
        self._last_launch_time: float | None = None
        self._launch_message_duration = 3.0  # seconds
        # Flag to track if we\'ve already played music on entry
        self._music_played_on_entry: bool = False

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle user input events for menu navigation and selection, including scrolling."""
        # Compute layout parameters for potential scrolling adjustments
        layout = self._layout_params()
        if event.type == pygame.KEYDOWN:
            # Debounce duplicate rapid KEYDOWN events for the same key
            try:
                import time

                now = time.time()
                if (
                    self._last_keydown_time is not None
                    and self._last_keydown_key == event.key
                    and (now - self._last_keydown_time) < self._debounce
                ):
                    return
                self._last_keydown_time = now
                self._last_keydown_key = event.key
            except Exception:
                pass

            if event.key == KEY_UP:
                # Move one item up in the grid
                layout = self._layout_params()
                columns = layout["columns"]
                if columns > 0:
                    self.selected = self.selected - columns
                    if self.selected < 0:
                        self.selected = self.selected % len(self.menu_items)
                else:
                    self.selected = (self.selected - 1) % len(self.menu_items)
                # Start hold tracking for smooth instant repeats
                try:
                    import time

                    self._held_key = KEY_UP
                    self._hold_start_time = time.time()
                    # Prevent an immediate repeat move in update() by priming last_repeat_time.
                    # If an explicit initial delay is configured, allow update() to wait by
                    # setting last_repeat_time to None; otherwise prime to now so repeats start
                    # after the interval.
                    if self._repeat_initial and self._repeat_initial > 0.0:
                        self._last_repeat_time = None
                    else:
                        self._last_repeat_time = time.time()
                except Exception:
                    self._held_key = None
                # Ensure the selected item is visible after navigation
                self._ensure_selected_visible(layout)
            elif event.key == KEY_DOWN:
                # Move one item down in the grid
                layout = self._layout_params()
                columns = layout["columns"]
                if columns > 0:
                    self.selected = (self.selected + columns) % len(self.menu_items)
                else:
                    self.selected = (self.selected + 1) % len(self.menu_items)
                try:
                    import time

                    self._held_key = KEY_DOWN
                    self._hold_start_time = time.time()
                    if self._repeat_initial and self._repeat_initial > 0.0:
                        self._last_repeat_time = None
                    else:
                        self._last_repeat_time = time.time()
                except Exception:
                    self._held_key = None
                self._ensure_selected_visible(layout)
            elif event.key == KEY_LEFT:
                # Move one item left in the grid
                layout = self._layout_params()
                columns = layout["columns"]
                if columns > 0:
                    row = self.selected // columns
                    self.selected = self.selected - 1
                    if self.selected < row * columns:
                        # Wrapped to previous row, go to end of that row
                        prev_row = row - 1
                        if prev_row >= 0:
                            self.selected = min(
                                self.selected, (prev_row + 1) * columns - 1
                            )
                        else:
                            # At top row, wrap to end
                            self.selected = len(self.menu_items) - 1
                else:
                    self.selected = (self.selected - 1) % len(self.menu_items)
                try:
                    import time

                    self._held_key = KEY_LEFT
                    self._hold_start_time = time.time()
                    if self._repeat_initial and self._repeat_initial > 0.0:
                        self._last_repeat_time = None
                    else:
                        self._last_repeat_time = time.time()
                except Exception:
                    self._held_key = None
                self._ensure_selected_visible(layout)
            elif event.key == KEY_RIGHT:
                # Move one item right in the grid
                layout = self._layout_params()
                columns = layout["columns"]
                if columns > 0:
                    row = self.selected // columns
                    self.selected = self.selected + 1
                    if self.selected >= len(self.menu_items):
                        self.selected = 0
                    elif self.selected > (row + 1) * columns - 1:
                        self.selected = (row + 1) * columns
                        if self.selected >= len(self.menu_items):
                            self.selected = 0
                else:
                    self.selected = (self.selected + 1) % len(self.menu_items)
                try:
                    import time

                    self._held_key = KEY_RIGHT
                    self._hold_start_time = time.time()
                    if self._repeat_initial and self._repeat_initial > 0.0:
                        self._last_repeat_time = None
                    else:
                        self._last_repeat_time = time.time()
                except Exception:
                    self._held_key = None
                self._ensure_selected_visible(layout)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                # Transition to the selected game state or run callable
                _, launch_target, _ = self.menu_items[self.selected]
                name = self.menu_items[self.selected][0]
                if isinstance(launch_target, type) and issubclass(launch_target, State):
                    try:
                        self.request_transition(launch_target())
                        logger.info("Launched game %s (state) successfully", name)
                        import time

                        self._last_launch_message = f"Launched {name}"
                        self._last_launch_time = time.time()
                    except Exception:
                        logger.exception("Failed to launch game state %s", name)
                        import time

                        self._last_launch_message = f"Failed to launch {name}"
                        self._last_launch_time = time.time()
                elif callable(launch_target):
                    try:
                        logger.info("Attempting to launch game %s (callable)", name)
                        launch_target()
                        logger.info("Launched game %s (callable) successfully", name)
                        import time

                        self._last_launch_message = f"Launched {name}"
                        self._last_launch_time = time.time()
                    except Exception:
                        logger.exception("Failed to launch game %s", name)
                        import time

                        self._last_launch_message = f"Failed to launch {name}"
                        self._last_launch_time = time.time()
                else:
                    # Disabled or unrecognized target – do not attempt to launch
                    logger.warning("Attempted to launch disabled menu item: %s", name)
                    import time

                    self._last_launch_message = f"{name} cannot be launched"
                    self._last_launch_time = time.time()
            elif event.key == pygame.K_m:
                # Allow toggling mute from the menu as well
                try:
                    import audio

                    audio.toggle_mute()
                except Exception:
                    pass
        elif event.type == pygame.KEYUP:
            # Stop any auto-repeat behaviour when the key is released
            if (
                event.key in (KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT)
                and self._held_key == event.key
            ):
                self._held_key = None
                self._hold_start_time = None
                self._last_repeat_time = None

    def _layout_params(self):
        """Compute layout parameters for menu grid and scrolling.

        The size of each square box and the spacing can be overridden via environment
        variables ``MENU_BOX_SIZE``, ``MENU_H_SPACING`` and ``MENU_V_SPACING``.
        """
        # Default values – can be overridden with env vars for testing
        BOX_SIZE = int(os.getenv("MENU_BOX_SIZE", "160"))
        H_SPACING = int(os.getenv("MENU_H_SPACING", "20"))
        V_SPACING = int(os.getenv("MENU_V_SPACING", "20"))
        num_items = len(self.menu_items)
        if num_items == 0:
            # No items, return defaults
            return {
                "BOX_SIZE": BOX_SIZE,
                "H_SPACING": H_SPACING,
                "V_SPACING": V_SPACING,
                "columns": 0,
                "rows": 0,
                "grid_height": 0,
                "margin_top": self.title_font_size + 20,
                "max_offset": 0,
                "total_grid_width": 0,
                "start_x": 0,
            }
        columns = max(1, SCREEN_WIDTH // (BOX_SIZE + H_SPACING))
        rows = (num_items + columns - 1) // columns
        grid_height = rows * (BOX_SIZE + V_SPACING) - V_SPACING
        margin_top = self.title_font_size + 20
        visible_height = SCREEN_HEIGHT - margin_top - 10
        max_offset = max(0, grid_height - visible_height)
        total_grid_width = columns * (BOX_SIZE + H_SPACING) - H_SPACING
        start_x = (SCREEN_WIDTH - total_grid_width) // 2
        return {
            "BOX_SIZE": BOX_SIZE,
            "H_SPACING": H_SPACING,
            "V_SPACING": V_SPACING,
            "columns": columns,
            "rows": rows,
            "grid_height": grid_height,
            "margin_top": margin_top,
            "max_offset": max_offset,
            "total_grid_width": total_grid_width,
            "start_x": start_x,
        }

    def _ensure_selected_visible(self, layout):
        """Adjust scroll_offset to ensure the selected item is within visible bounds."""
        columns = layout["columns"]
        if columns == 0:
            return
        row = self.selected // columns
        # Compute the y position of the selected box (top) before scroll offset
        box_top = layout["margin_top"] + row * (
            layout["BOX_SIZE"] + layout["V_SPACING"]
        )
        # Visible region top and bottom
        visible_top = layout["margin_top"]
        visible_bottom = SCREEN_HEIGHT - 10
        # If the box is above the visible top, scroll up
        if box_top < visible_top:
            self.scroll_offset = max(0, self.scroll_offset - (visible_top - box_top))
        # If the box is below the visible bottom, scroll down
        elif box_top + layout["BOX_SIZE"] > visible_bottom:
            self.scroll_offset = min(
                layout["max_offset"],
                self.scroll_offset + (box_top + layout["BOX_SIZE"] - visible_bottom),
            )

    def on_enter(self) -> None:
        """Called when the menu state becomes active.

        Plays random music if not already played on this entry.
        """
        try:
            if not self._music_played_on_entry:
                import audio

                audio.play_random_music(context="menu")
                self._music_played_on_entry = True
        except Exception:
            pass

    def update(self, dt: float) -> None:
        """Update menu state.

        Note: highlight visuals are computed in draw() and are decoupled from update().
        """
        # Advance the legacy highlight animation phase (kept for tests/compat)
        try:
            import math

            self.highlight_anim_phase += dt
            phase = math.sin(self.highlight_anim_phase * 2 * math.pi)
            self.highlight_border_width = int(2 + (phase + 1) / 2 * 4)
            if self.highlight_border_width < 2:
                self.highlight_border_width = 2
        except Exception:
            pass

        # Handle held key auto-repeat for instantaneous selection movement
        try:
            if self._held_key is not None:
                import time

                now = time.time()
                # If last_repeat_time is None, we have only applied the initial keydown move.
                if self._last_repeat_time is None:
                    # Wait for initial delay before starting repeated moves
                    if (
                        self._hold_start_time
                        and (now - self._hold_start_time) >= self._repeat_initial
                    ):
                        # Do the first repeated move based on the held key
                        layout = self._layout_params()
                        columns = layout["columns"]
                        if self._held_key == KEY_UP:
                            if columns > 0:
                                self.selected = self.selected - columns
                                if self.selected < 0:
                                    self.selected = self.selected % len(self.menu_items)
                            else:
                                self.selected = (self.selected - 1) % len(
                                    self.menu_items
                                )
                        elif self._held_key == KEY_DOWN:
                            if columns > 0:
                                self.selected = (self.selected + columns) % len(
                                    self.menu_items
                                )
                            else:
                                self.selected = (self.selected + 1) % len(
                                    self.menu_items
                                )
                        elif self._held_key == KEY_LEFT:
                            if columns > 0:
                                row = self.selected // columns
                                self.selected = self.selected - 1
                                if self.selected < row * columns:
                                    prev_row = row - 1
                                    if prev_row >= 0:
                                        self.selected = min(
                                            self.selected, (prev_row + 1) * columns - 1
                                        )
                                    else:
                                        self.selected = len(self.menu_items) - 1
                            else:
                                self.selected = (self.selected - 1) % len(
                                    self.menu_items
                                )
                        elif self._held_key == KEY_RIGHT:
                            if columns > 0:
                                row = self.selected // columns
                                self.selected = (self.selected + 1) % len(
                                    self.menu_items
                                )
                                if self.selected > (row + 1) * columns - 1:
                                    self.selected = (row + 1) * columns
                                    if self.selected >= len(self.menu_items):
                                        self.selected = row * columns
                            else:
                                self.selected = (self.selected + 1) % len(
                                    self.menu_items
                                )
                        self._last_repeat_time = now
                        # Ensure visibility
                        self._ensure_selected_visible(layout)
                else:
                    # Subsequent repeats at interval
                    if (now - self._last_repeat_time) >= self._repeat_interval:
                        layout = self._layout_params()
                        columns = layout["columns"]
                        if self._held_key == KEY_UP:
                            if columns > 0:
                                self.selected = self.selected - columns
                                if self.selected < 0:
                                    self.selected = self.selected % len(self.menu_items)
                            else:
                                self.selected = (self.selected - 1) % len(
                                    self.menu_items
                                )
                        elif self._held_key == KEY_DOWN:
                            if columns > 0:
                                self.selected = (self.selected + columns) % len(
                                    self.menu_items
                                )
                            else:
                                self.selected = (self.selected + 1) % len(
                                    self.menu_items
                                )
                        elif self._held_key == KEY_LEFT:
                            if columns > 0:
                                row = self.selected // columns
                                self.selected = self.selected - 1
                                if self.selected < row * columns:
                                    prev_row = row - 1
                                    if prev_row >= 0:
                                        self.selected = min(
                                            self.selected, (prev_row + 1) * columns - 1
                                        )
                                    else:
                                        self.selected = len(self.menu_items) - 1
                            else:
                                self.selected = (self.selected - 1) % len(
                                    self.menu_items
                                )
                        elif self._held_key == KEY_RIGHT:
                            if columns > 0:
                                row = self.selected // columns
                                self.selected = (self.selected + 1) % len(
                                    self.menu_items
                                )
                                if self.selected > (row + 1) * columns - 1:
                                    self.selected = (row + 1) * columns
                                    if self.selected >= len(self.menu_items):
                                        self.selected = row * columns
                            else:
                                self.selected = (self.selected + 1) % len(
                                    self.menu_items
                                )
                        self._last_repeat_time = now
                        self._ensure_selected_visible(layout)
        except Exception:
            # Protect update loop from any input handling errors
            pass

    def draw(self, screen: pygame.Surface) -> None:
        """Render the menu title and list of menu items onto the screen.

        The selected menu item is highlighted with a pulsing rectangle outline.
        """
        # Title - draw at the very top
        draw_text(
            screen,
            "Arcade Suite",
            FONT_SIZE_LARGE,
            WHITE,
            SCREEN_WIDTH // 2,
            30,
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
        draw_text(screen, text, FONT_SIZE_SMALL, YELLOW, 30, 10, center=False)
        # Expose last rendered text for tests
        self._last_mute_text = text
        # Menu items - display each game as a square box in a grid layout
        num_items = len(self.menu_items)
        if num_items == 0:
            # Nothing to draw
            return
        # Compute layout parameters (box size, spacing, columns, etc.) – this also gives us the current scroll offset
        layout = self._layout_params()
        BOX_SIZE = layout["BOX_SIZE"]
        H_SPACING = layout["H_SPACING"]
        V_SPACING = layout["V_SPACING"]
        columns = layout["columns"]
        start_x = layout["start_x"]
        # Apply vertical scroll offset (positive offset means the grid moves up)
        start_y = layout["margin_top"] - self.scroll_offset
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
                # Compute pulsing border width using time-based animation (decoupled)
                try:
                    import math
                    import time

                    elapsed = time.time() - self._highlight_start
                    phase = math.sin(elapsed * 2 * math.pi)  # -1 to 1
                    border_w = int(2 + (phase + 1) / 2 * 4)
                    if border_w < 2:
                        border_w = 2
                except Exception:
                    border_w = self.highlight_border_width

                self.highlight_rect = pygame.Rect(
                    box_x, box_y, BOX_SIZE, BOX_SIZE
                ).inflate(self.highlight_padding * 2, self.highlight_padding * 2)
                pygame.draw.rect(
                    screen,
                    self.highlight_color,
                    self.highlight_rect,
                    width=border_w,
                )
            # Draw icon and text
            screen.blit(icon_surface, (icon_x, icon_y))
            screen.blit(text_surface, (text_x, text_y))
        # After drawing all boxes, draw a scroll indicator if any vertical overflow exists
        if layout["max_offset"] > 0:
            # Draw a larger, more visible scroll indicator (a filled triangle)
            tri_height = max(self.title_font_size // 2, self.item_font_size) * 2
            tri_half = tri_height // 2
            tri_center_x = SCREEN_WIDTH // 2
            tri_top_y = SCREEN_HEIGHT - 20
            points = [
                (tri_center_x - tri_half, tri_top_y),
                (tri_center_x + tri_half, tri_top_y),
                (tri_center_x, tri_top_y + tri_height),
            ]
            pygame.draw.polygon(screen, YELLOW, points)
        # Draw transient launch message (if set and not expired)
        try:
            import time

            if self._last_launch_message and self._last_launch_time:
                if time.time() - self._last_launch_time < self._launch_message_duration:
                    draw_text(
                        screen,
                        self._last_launch_message,
                        FONT_SIZE_SMALL,
                        YELLOW,
                        SCREEN_WIDTH // 2,
                        SCREEN_HEIGHT - 40,
                        center=True,
                    )
        except Exception:
            # Drawing a transient message should not interfere with normal rendering
            pass


# Clean up imported decorator
del abstractmethod


class HelpState(State):
    """Help/controls screen for the arcade suite.

    Displays controls for all available games. The help screen is built dynamically
    by parsing the Controls section from each game's module docstring.
    """

    def __init__(self, game_class: Optional[Type[State]] = None) -> None:
        """Initialize the help screen with title and item font sizes.

        Args:
            game_class: Optional game class to show help for. If None, shows help for all games.
        """
        super().__init__()
        self.title_font_size = 48
        self.game_class = game_class
        self.item_font_size = 24
        self.section_font_size = 32
        self.margin_top = 80
        self.line_spacing = 30
        self.section_spacing = 40
        self.scroll_offset = 0
        self.scroll_speed = 40

    def handle_event(self, event: pygame.event.Event) -> None:
        """Process key events for the help screen.

        Supports:
        - ``K_h`` or ``K_ESCAPE`` – return to the main menu (if game_class not set) or game (if set).
        - ``K_UP`` / ``K_DOWN`` – scroll content.
        """
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_h, pygame.K_ESCAPE):
                if self.game_class:
                    # Return to the game that opened help
                    if hasattr(self, "_parent_game") and self._parent_game:
                        game_instance = self._parent_game
                        game_instance.paused = False  # Resume the game
                        game_instance.next_state = None  # Clear any pending transition
                        self.request_transition(game_instance)
                    else:
                        # Fallback: create a new instance
                        self.request_transition(self.game_class())
                else:
                    from menu_items import get_menu_items

                    self.request_transition(MenuState(get_menu_items()))
                return
            elif event.key == pygame.K_UP:
                self.scroll_offset = max(0, self.scroll_offset - self.scroll_speed)
            elif event.key == pygame.K_DOWN:
                controls = self._get_all_controls()
                total_height = self._calculate_content_height(controls)
                max_offset = max(0, total_height - (SCREEN_HEIGHT - 110))
                self.scroll_offset = min(
                    max_offset, self.scroll_offset + self.scroll_speed
                )

    def update(self, dt: float) -> None:
        """Update the help screen (no time-dependent logic)."""
        pass

    def _calculate_content_height(self, controls: list) -> int:
        """Calculate total height of all content."""
        y = self.margin_top
        for game_name, control_lines in controls:
            y += self.section_spacing
            for line in control_lines:
                wrapped_lines = wrap_text(
                    pygame.font.Font(None, self.item_font_size), line, SCREEN_WIDTH - 60
                )
                y += len(wrapped_lines) * self.item_font_size + self.line_spacing
            y += 10
        return y

    def draw(self, screen: pygame.Surface) -> None:
        """Render the help screen with controls for all games.

        Draws the title, then iterates through all discovered games and displays
        their controls using the draw_text helper with text wrapping.
        """
        screen.fill(BLACK)

        # Title
        draw_text(
            screen,
            "Controls",
            FONT_SIZE_LARGE,
            WHITE,
            SCREEN_WIDTH // 2,
            30,
            center=True,
        )

        # Get controls from all games
        controls = self._get_all_controls()

        # Draw controls for each game
        y = self.margin_top - self.scroll_offset
        for game_name, control_lines in controls:
            # Game name as section header
            draw_text(
                screen,
                game_name,
                FONT_SIZE_MEDIUM,
                YELLOW,
                SCREEN_WIDTH // 2,
                y,
                center=True,
            )
            y += self.section_spacing

            # Control lines with wrapping
            for line in control_lines:
                wrapped_lines = wrap_text(
                    pygame.font.Font(None, self.item_font_size), line, SCREEN_WIDTH - 60
                )
                for surface, _ in wrapped_lines:
                    surface.set_colorkey((0, 0, 0))
                    text_rect = surface.get_rect()
                    text_rect.center = (SCREEN_WIDTH // 2, y)
                    screen.blit(surface, text_rect)
                    y += self.item_font_size
                y += self.line_spacing

            # Add some spacing between sections
            y += 10

        # Footer instruction
        if self.game_class:
            footer_text = "Press H or ESC to return to game"
        else:
            footer_text = "Press H or ESC to return to menu"
        draw_text(
            screen,
            footer_text,
            FONT_SIZE_SMALL,
            GRAY,
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT - 30,
            center=True,
        )

        # Scroll indicator if content overflows
        total_height = self._calculate_content_height(controls)
        max_offset = max(0, total_height - (SCREEN_HEIGHT - 110))
        if max_offset > 0:
            # Draw scroll indicator
            tri_height = 15
            tri_half = tri_height // 2
            tri_center_x = SCREEN_WIDTH // 2
            tri_top_y = SCREEN_HEIGHT - 40
            points = [
                (tri_center_x - tri_half, tri_top_y),
                (tri_center_x + tri_half, tri_top_y),
                (tri_center_x, tri_top_y + tri_height),
            ]
            pygame.draw.polygon(screen, YELLOW, points)

    def _get_all_controls(self) -> List[Tuple[str, List[str]]]:
        """Collect controls from all discovered games, or from a specific game if game_class is set.

        Returns a list of (game_name, control_lines) tuples where control_lines
        is a list of strings describing the controls for that game.
        """
        if self.game_class:
            # Get controls for the specific game
            game_name = self.game_class.__name__.replace("State", "")
            game_controls = self._get_game_controls_for_class(self.game_class)
            if game_controls:
                return [(game_name, game_controls)]
            return []

        from menu_items import discover_games

        items = discover_games()
        controls: List[Tuple[str, List[str]]] = []

        for name, launch_target, _ in items:
            # Get controls from the launch target
            game_controls = self._get_game_controls(name, launch_target)
            if game_controls:
                controls.append((name, game_controls))

        # Sort by game name
        controls.sort(key=lambda x: x[0].lower())
        return controls

    def _get_game_controls_for_class(self, game_class: Type[State]) -> List[str] | None:
        """Extract controls for a specific game class.

        Looks for a get_controls() class method first, then falls back to
        parsing the module docstring for a "Controls:" section.

        Returns a list of control lines or None if no controls found.
        """
        # Check for get_controls class method
        if hasattr(game_class, "get_controls") and callable(
            getattr(game_class, "get_controls")
        ):
            try:
                controls = game_class.get_controls()  # type: ignore
                if controls:
                    return controls
            except Exception:
                pass

        # Fallback: try to get module docstring
        try:
            module_name = game_class.__module__
            # Import the specific module (not just the top-level package)
            module = __import__(module_name)
            # Get the specific submodule for the class
            for part in module_name.split(".")[1:]:
                module = getattr(module, part)
            doc = getattr(module, "__doc__", None)
            if doc:
                controls = self._parse_controls_from_doc(doc)
                if controls:
                    return controls
        except Exception:
            pass

        return None

    def _get_game_controls(
        self, game_name: str, launch_target: object | None
    ) -> List[str] | None:
        """Extract controls for a single game.

        Looks for a "Controls:" section in the module docstring.

        Returns a list of control lines or None if no controls found.
        """
        if not launch_target or not hasattr(launch_target, "__module__"):
            return None

        try:
            # Import the module
            module_name = launch_target.__module__
            module = __import__(module_name)

            # Check module docstring for Controls
            doc = getattr(module, "__doc__", None)
            if doc:
                controls = self._parse_controls_from_doc(doc)
                if controls:
                    return controls

            # If controls not found, try common submodule patterns
            # For packages like games.breakout, try games.breakout.breakout
            try:
                import importlib

                # Try submodule with same name as package
                submodule_name = f"{module_name}.{module_name.split('.')[-1]}"
                submodule = importlib.import_module(submodule_name)
                doc = getattr(submodule, "__doc__", None)
                if doc:
                    controls = self._parse_controls_from_doc(doc)
                    if controls:
                        return controls
            except Exception:
                pass

            # Try games.game_name.game_name pattern
            try:
                import importlib

                game_base = module_name.split(".")[-1]
                submodule_name = f"games.{game_base}.{game_base}"
                submodule = importlib.import_module(submodule_name)
                doc = getattr(submodule, "__doc__", None)
                if doc:
                    controls = self._parse_controls_from_doc(doc)
                    if controls:
                        return controls
            except Exception:
                pass

        except Exception:
            pass

        return None

    def _parse_controls_from_doc(self, doc: str | None) -> List[str] | None:
        """Parse controls from a docstring.

        Looks for a "Controls:" section and extracts the control descriptions.

        Returns a list of control lines or None if no controls found.
        """
        if not doc:
            return None

        lines = doc.split("\n")
        # Find Controls section
        in_controls = False
        control_lines: List[str] = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("Controls:"):
                in_controls = True
                continue
            if in_controls:
                # Check if this line is indented (part of controls section)
                if line and not line.startswith(" ") and not line.startswith("\t"):
                    # End of controls section (non-indented line)
                    break
                if stripped:  # Non-empty line
                    control_lines.append(stripped)
        if control_lines:
            return control_lines

        return None


__all__ = ["State", "Engine", "MenuState", "HelpState"]
