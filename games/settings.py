# games/settings.py
"""Settings UI for difficulty selection and other options.

This state provides a simple UI that allows the player to adjust the difficulty
(level) for each game in the arcade suite. The UI is reachable from the main
menu by pressing the **S** key (handled in ``engine.MenuState``).

Controls:
    ↑ / ↓   - Move selection between game entries.
    ← / →   - Cycle the selected game's difficulty (Easy → Medium → Hard → Easy).
    ESC     - Return to the main menu (handled by ``Game.handle_event``).
    M       - Toggle mute (inherited from ``Game``).
"""

import logging

import pygame

import config

logger = logging.getLogger(__name__)
from games.game_base import Game
from utils import BLACK, SCREEN_HEIGHT, SCREEN_WIDTH, WHITE, YELLOW, draw_text


class SettingsState(Game):
    """UI screen for adjusting per‑game difficulty settings.

    The state displays a list of games with their current difficulty. The user can
    navigate with the arrow keys and change the difficulty, which is persisted via
    ``config.set_difficulty`` (writes to ``settings.json``).
    """

    def __init__(self) -> None:
        """Initialise the settings UI.

        Sets up the list of games, the currently selected entry, and UI constants
        such as font sizes and highlight styling.
        """
        super().__init__()
        logger.info("Settings UI initialized")
        self._games = [
            ("snake", "Snake"),
            ("pong", "Pong"),
            ("breakout", "Breakout"),
            ("space_invaders", "Space Invaders"),
            ("tetris", "Tetris"),
        ]
        # Flag to avoid spamming the display log
        self._displayed_logged = False
        self.selected = 0
        self.title_font_size = 48
        self.item_font_size = 32
        self.highlight_color = config.GRAY
        self.highlight_width = 2
        self.highlight_padding = 8

    # ---------------------------------------------------------------------
    # Helper methods for reading and writing difficulty values
    # ---------------------------------------------------------------------
    def _get_difficulty(self, key: str) -> str:
        """Return the stored difficulty for *key*.

        ``key`` is one of the identifiers used in ``config`` (e.g. ``"snake"``).
        """
        if key == "snake":
            return config.SNAKE_DIFFICULTY
        if key == "pong":
            return config.PONG_DIFFICULTY
        if key == "breakout":
            return config.BREAKOUT_DIFFICULTY
        if key == "space_invaders":
            return config.SPACE_INVADERS_DIFFICULTY
        if key == "tetris":
            return config.TETRIS_DIFFICULTY
        return config.DIFFICULTY_MEDIUM

    def _set_difficulty(self, key: str, level: str) -> None:
        """Persist a new difficulty level for *key* using ``config.set_difficulty``."""
        config.set_difficulty(key, level)

    # ---------------------------------------------------------------------
    # Event handling
    # ---------------------------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        """Process key events for the settings UI.

        Delegates ESC, mute and pause handling to ``Game.handle_event``. Handles the
        navigation and difficulty‑cycling keys:

        * ↑ / ↓ – move the selection cursor.
        * ← / → – change the selected game's difficulty (cycles through Easy, Medium,
          Hard). The new difficulty is persisted via ``config.set_difficulty``.
        """
        super().handle_event(event)
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_UP:
            self.selected = (self.selected - 1) % len(self._games)
        elif event.key == pygame.K_DOWN:
            self.selected = (self.selected + 1) % len(self._games)
        elif event.key == pygame.K_LEFT:
            key, _ = self._games[self.selected]
            current = self._get_difficulty(key)
            levels = [
                config.DIFFICULTY_EASY,
                config.DIFFICULTY_MEDIUM,
                config.DIFFICULTY_HARD,
            ]
            idx = levels.index(current)
            new_level = levels[(idx - 1) % len(levels)]
            self._set_difficulty(key, new_level)
        elif event.key == pygame.K_RIGHT:
            key, _ = self._games[self.selected]
            current = self._get_difficulty(key)
            levels = [
                config.DIFFICULTY_EASY,
                config.DIFFICULTY_MEDIUM,
                config.DIFFICULTY_HARD,
            ]
            idx = levels.index(current)
            new_level = levels[(idx + 1) % len(levels)]
            self._set_difficulty(key, new_level)
        elif event.key == pygame.K_ESCAPE:
            # ESC handled by Game.handle_event which will request transition back to menu
            logger.info("Settings UI closed (return to menu via ESC)")

    # ---------------------------------------------------------------------
    # Update (no time‑dependent logic needed)
    # ---------------------------------------------------------------------
    def update(self, dt: float) -> None:
        """Update the settings UI (no time‑dependent logic)."""
        # No animation or state changes are required per frame.
        pass

    # ---------------------------------------------------------------------
    # Rendering
    # ---------------------------------------------------------------------
    def draw(self, screen: pygame.Surface) -> None:
        """Render the settings UI.

        Shows the title, a short instruction line, and a list of games with their
        current difficulty. The selected entry is highlighted with a rectangle.
        """
        screen.fill(BLACK)
        # Title
        draw_text(
            screen,
            "Settings",
            self.title_font_size,
            WHITE,
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 6,
            center=True,
        )
        # Instructions
        draw_text(
            screen,
            "↑/↓ select • ←/→ change difficulty • ESC back",
            self.item_font_size - 4,
            YELLOW,
            SCREEN_WIDTH // 2,
            int(SCREEN_HEIGHT * 0.8),
            center=True,
        )
        # List of games
        start_y = SCREEN_HEIGHT // 4
        font = pygame.font.Font(None, self.item_font_size)
        for idx, (key, name) in enumerate(self._games):
            diff = self._get_difficulty(key).capitalize()
            line = f"{name}: {diff}"
            color = YELLOW if idx == self.selected else WHITE
            text_surface = font.render(line, True, color)
            text_rect = text_surface.get_rect()
            text_rect.center = (SCREEN_WIDTH // 2, start_y + idx * 50)
            if idx == self.selected:
                highlight_rect = text_rect.inflate(
                    self.highlight_padding * 2, self.highlight_padding * 2
                )
                pygame.draw.rect(
                    screen, self.highlight_color, highlight_rect, self.highlight_width
                )
            screen.blit(text_surface, text_rect)
        # Log that the settings UI was rendered (once per session)
        if not getattr(self, "_displayed_logged", False):
            logger.info("Settings UI displayed")
            self._displayed_logged = True
        if self.paused:
            self.draw_pause_overlay(screen)
        self.draw_mute_overlay(screen)
