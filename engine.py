"""Engine module providing a simple state machine for the arcade suite.

The module defines an abstract ``State`` base class that game states can inherit from.
Each ``State`` must implement ``handle_event(event)``, ``update(dt)`` and ``draw(screen)``.
Optionally, a state can request a transition to a new state by setting ``self.next_state``.

The ``Engine`` class runs a pygame loop, delegating event handling, updating and drawing to the
current state. After each loop iteration the engine checks ``state.next_state`` – if it is set,
the engine switches to the new state and clears the flag.
"""

import pygame
from abc import ABC, abstractmethod
from typing import Optional

from config import SCREEN_WIDTH, SCREEN_HEIGHT, BLACK, WHITE, YELLOW, KEY_UP, KEY_DOWN
from utils import draw_text


class State(ABC):
    """Abstract base class for all states.

    Subclasses must implement ``handle_event``, ``update`` and ``draw``.
    To request a transition, set ``self.next_state`` to an instance of another ``State``.
    """

    def __init__(self):
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
        self.next_state = None


class Engine:
    """Main engine that runs the pygame loop and delegates to the active state.

    ``initial_state`` should be an instance of a ``State`` subclass.
    ``fps`` controls the target frame rate.
    """

    def __init__(self, initial_state: State, fps: int = 60):
        self.fps = fps
        self.state = initial_state
        # Initialise pygame and create the screen once.
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Arcade Suite")
        self.clock = pygame.time.Clock()
        self.running = True

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

    def __init__(self, menu_items):
        super().__init__()
        self.menu_items = menu_items
        self.selected = 0
        # Font size for the menu title and items
        self.title_font_size = 48
        self.item_font_size = 32

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == KEY_UP:
                self.selected = (self.selected - 1) % len(self.menu_items)
            elif event.key == KEY_DOWN:
                self.selected = (self.selected + 1) % len(self.menu_items)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                # Transition to the selected game state
                _, state_cls = self.menu_items[self.selected]
                self.request_transition(state_cls())
            # ESC key is ignored in the menu

    def update(self, dt: float) -> None:
        # No time‑dependent logic for the menu
        pass

    def draw(self, screen: pygame.Surface) -> None:
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
        # Menu items
        start_y = SCREEN_HEIGHT // 4 + 80
        for idx, (name, _) in enumerate(self.menu_items):
            color = YELLOW if idx == self.selected else WHITE
            draw_text(
                screen,
                name,
                self.item_font_size,
                color,
                SCREEN_WIDTH // 2,
                start_y + idx * 50,
                center=True,
            )
