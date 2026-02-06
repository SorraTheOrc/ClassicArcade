# games/tetris.py
"""Simple Tetris game implementation using Pygame.

Controls:
    Left/Right arrow keys - move piece left/right.
    Up arrow - rotate piece.
    Down arrow - soft drop (increase descent speed).
    R - restart after game over.
    ESC - return to main menu.
"""

import pygame
import audio
import random
from config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    WHITE,
    BLACK,
    RED,
    GREEN,
    BLUE,
    YELLOW,
    CYAN,
    MAGENTA,
    GRAY,
    KEY_UP,
    KEY_DOWN,
    KEY_LEFT,
    KEY_RIGHT,
)
from utils import draw_text
from datetime import datetime
from games.highscore import add_score

from typing import List, Tuple, cast as _cast
from games.game_base import Game
import logging

logger = logging.getLogger(__name__)

# Base speed values for difficulty scaling (default values)
BASE_FALL_SPEED = 500
BASE_FAST_FALL_SPEED = 50

# Game constants (initial values, may be overridden by difficulty settings)
CELL_SIZE = 20
GRID_WIDTH = 10
GRID_HEIGHT = 20
GRID_X_OFFSET = (SCREEN_WIDTH - GRID_WIDTH * CELL_SIZE) // 2
GRID_Y_OFFSET = (SCREEN_HEIGHT - GRID_HEIGHT * CELL_SIZE) // 2
FALL_SPEED = BASE_FALL_SPEED  # milliseconds per grid step (initial)
FAST_FALL_SPEED = BASE_FAST_FALL_SPEED
FONT_SIZE = 24

# Apply difficulty‑based speed settings for Tetris


def _apply_tetris_speed_settings() -> None:
    """Set fall speed variables based on the current Tetris difficulty.

    Easy: default FALL_SPEED=500 ms, FAST_FALL_SPEED=50 ms.
    Medium: speed increased by 1.5x (i.e., interval reduced).
    Hard: speed increased by 2x (interval reduced further).
    """
    global FALL_SPEED, FAST_FALL_SPEED
    multiplier = config.difficulty_multiplier(config.TETRIS_DIFFICULTY)
    # Reduce interval for higher difficulty (faster falling)
    FALL_SPEED = int(BASE_FALL_SPEED / multiplier)
    FAST_FALL_SPEED = int(BASE_FAST_FALL_SPEED / multiplier)


import config


class TetrisState(Game):
    """State for the Tetris game, compatible with the engine loop."""

    def __init__(self) -> None:
        """Initialize the Tetris game state, setting up the grid, current piece, and game variables."""
        super().__init__()
        _apply_tetris_speed_settings()
        logger.info(
            f"Tetris game started: difficulty={config.TETRIS_DIFFICULTY}, fall_speed={FALL_SPEED}, fast_fall_speed={FAST_FALL_SPEED}"
        )
        # Initialize empty grid
        self.grid: List[List[object | None]] = [
            [None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)
        ]
        # Piece state
        self.current_shape_name = random.choice(list(self.SHAPES.keys()))
        self.current_shape = self.SHAPES[self.current_shape_name]
        self.current_color = self.SHAPE_COLORS[self.current_shape_name]
        self.shape_x = GRID_WIDTH // 2 - 2
        self.shape_y = 0
        self.shape_coords = self.current_shape
        self.fall_timer = 0.0
        self.fall_interval = FALL_SPEED
        self.game_over = False
        # High‑score tracking flags
        self.highscore_recorded = False
        self.highscores = []
        self.score = 0
        self.level = 1
        self.lines_cleared_total = 0

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle user input for piece movement and rotation, delegating generic events to base class."""
        # Let base class handle ESC, pause, restart
        super().handle_event(event)
        if event.type == pygame.KEYDOWN:
            if not self.game_over:
                if event.key == KEY_LEFT:
                    if self.valid_position(
                        self.grid, self.shape_coords, self.shape_x - 1, self.shape_y
                    ):
                        self.shape_x -= 1
                elif event.key == KEY_RIGHT:
                    if self.valid_position(
                        self.grid, self.shape_coords, self.shape_x + 1, self.shape_y
                    ):
                        self.shape_x += 1
                elif event.key == KEY_DOWN:
                    self.fall_interval = FAST_FALL_SPEED
                elif event.key == KEY_UP:
                    new_coords = self.rotate(self.shape_coords)
                    if self.valid_position(
                        self.grid, new_coords, self.shape_x, self.shape_y
                    ):
                        self.shape_coords = new_coords
                        # Play rotate sound
                        audio.play_effect("tetris", "rotate.wav")
            # No need to handle R here; base class already restarts

    def update(self, dt: float) -> None:
        """Update the game state: handle falling piece, line clears, level progression, and game over checks."""
        if self.game_over or self.paused:
            return
        # Reset fall speed after handling key press (if not holding down).
        # Some test environments may provide an unexpected return from
        # `pygame.key.get_pressed()` (e.g. an empty sequence), so guard
        # against IndexError by treating an unknown state as "not pressed".
        keys = pygame.key.get_pressed()
        try:
            down_is_pressed = bool(keys[KEY_DOWN])
        except Exception:
            down_is_pressed = False
        if not down_is_pressed:
            self.fall_interval = FALL_SPEED
        # Update fall timer
        self.fall_timer += dt * 1000  # dt is seconds, convert to ms
        if self.fall_timer >= self.fall_interval:
            self.fall_timer = 0.0
            # Attempt to move piece down
            if self.valid_position(
                self.grid, self.shape_coords, self.shape_x, self.shape_y + 1
            ):
                self.shape_y += 1
            else:
                # Lock piece
                self.lock_piece(
                    self.grid,
                    self.shape_coords,
                    self.shape_x,
                    self.shape_y,
                    self.current_color,
                )
                # Play a block-placed sound whenever a piece is locked into place.
                # This gives immediate feedback even when no lines are cleared.
                audio.play_effect("tetris", "place.wav")
                # Clear lines
                lines = self.clear_lines(self.grid)
                if lines:
                    self.lines_cleared_total += lines
                    self.score += (lines**2) * 100
                    # Play line clear sound once per cleared line.
                    # This should happen regardless of whether the level
                    # increased — moving playback out of the level-up block
                    # ensures the player always receives audio feedback.
                    for _ in range(lines):
                        audio.play_effect("tetris", "line_clear.wav")
                    # Increase level every 5 lines cleared
                    if self.lines_cleared_total // 5 > (self.level - 1):
                        self.level += 1
                        self.fall_interval = max(50, FALL_SPEED - (self.level - 1) * 50)
                # Spawn new piece
                self.current_shape_name = random.choice(list(self.SHAPES.keys()))
                self.current_shape = self.SHAPES[self.current_shape_name]
                self.current_color = self.SHAPE_COLORS[self.current_shape_name]
                self.shape_coords = self.current_shape
                self.shape_x = GRID_WIDTH // 2 - 2
                self.shape_y = 0
                # Check immediate collision
                if not self.valid_position(
                    self.grid, self.shape_coords, self.shape_x, self.shape_y
                ):
                    self.game_over = True

    def draw(self, screen: pygame.Surface) -> None:
        """Render the game grid, current piece, and score onto the screen."""
        screen.fill(BLACK)
        # Draw grid cells
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                cell_color = self.grid[y][x]
                if cell_color:
                    rect = pygame.Rect(
                        GRID_X_OFFSET + x * CELL_SIZE,
                        GRID_Y_OFFSET + y * CELL_SIZE,
                        CELL_SIZE,
                        CELL_SIZE,
                    )
                    pygame.draw.rect(
                        screen, _cast(Tuple[int, int, int], cell_color), rect
                    )
        # Draw current falling piece
        for x_offset, y_offset in self.shape_coords:
            gx = self.shape_x + x_offset
            gy = self.shape_y + y_offset
            if 0 <= gx < GRID_WIDTH and 0 <= gy < GRID_HEIGHT:
                rect = pygame.Rect(
                    GRID_X_OFFSET + gx * CELL_SIZE,
                    GRID_Y_OFFSET + gy * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE,
                )
                pygame.draw.rect(screen, self.current_color, rect)
        # Draw score
        draw_text(
            screen, f"Score: {self.score}", FONT_SIZE, WHITE, 60, 20, center=False
        )
        if self.game_over:
            # Record high score once (score is self.score)
            if not getattr(self, "highscore_recorded", False):
                self.highscores = add_score("tetris", self.score)
                self.highscore_recorded = True
            # Layout positions
            heading_y = int(SCREEN_HEIGHT * 0.20)
            instr_y = int(SCREEN_HEIGHT * 0.80)
            # Heading
            draw_text(
                screen,
                "High Scores:",
                FONT_SIZE,
                WHITE,
                SCREEN_WIDTH // 2,
                heading_y,
                center=True,
            )
            # Scores
            for idx, entry in enumerate(self.highscores[:5], start=1):
                try:
                    date_str = datetime.fromisoformat(entry["timestamp"]).strftime(
                        "%d-%b-%Y"
                    )
                except Exception:
                    date_str = entry["timestamp"]
                score_y = heading_y + FONT_SIZE + 5 + (idx - 1) * (FONT_SIZE + 5)
                draw_text(
                    screen,
                    f"{idx}. {entry['score']} ({date_str})",
                    FONT_SIZE,
                    WHITE,
                    SCREEN_WIDTH // 2,
                    score_y,
                    center=True,
                )
            # Instruction line at bottom
            draw_text(
                screen,
                "Game Over! Press R to restart or ESC to menu",
                FONT_SIZE,
                RED,
                SCREEN_WIDTH // 2,
                instr_y,
                center=True,
            )
        # Draw pause overlay if paused
        if self.paused:
            self.draw_pause_overlay(screen)
        # Draw mute overlay (Muted or Sound On)
        self.draw_mute_overlay(screen)

    # Tetromino shapes (list of (x, y) offsets within a 4x4 matrix)
    SHAPES = {
        "I": [(0, 1), (1, 1), (2, 1), (3, 1)],
        "O": [(0, 0), (1, 0), (0, 1), (1, 1)],
        "T": [(1, 0), (0, 1), (1, 1), (2, 1)],
        "S": [(1, 0), (2, 0), (0, 1), (1, 1)],
        "Z": [(0, 0), (1, 0), (1, 1), (2, 1)],
        "J": [(0, 0), (0, 1), (1, 1), (2, 1)],
        "L": [(2, 0), (0, 1), (1, 1), (2, 1)],
    }

    SHAPE_COLORS = {
        "I": CYAN,
        "O": YELLOW,
        "T": MAGENTA,
        "S": GREEN,
        "Z": RED,
        "J": BLUE,
        "L": WHITE,
    }

    @staticmethod
    def rotate(shape_coords: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Rotate shape 90 degrees clockwise around the (1,1) pivot.
        Returns a new list of (x, y) tuples.
        """
        rotated = []
        for x, y in shape_coords:
            # Translate to pivot
            tx, ty = x - 1, y - 1
            # Rotate clockwise: (x, y) -> (y, -x)
            rx, ry = ty, -tx
            # Translate back
            nx, ny = rx + 1, ry + 1
            rotated.append((nx, ny))
        return rotated

    @staticmethod
    def valid_position(
        grid: List[List[object | None]],
        shape_coords: List[Tuple[int, int]],
        offset_x: int,
        offset_y: int,
    ) -> bool:
        """Check if the shape at the given offset is within bounds and not colliding."""
        for x, y in shape_coords:
            gx = x + offset_x
            gy = y + offset_y
            if gx < 0 or gx >= GRID_WIDTH or gy < 0 or gy >= GRID_HEIGHT:
                return False
            if grid[gy][gx] is not None:
                return False
        return True

    @staticmethod
    def lock_piece(
        grid: List[List[object | None]],
        shape_coords: List[Tuple[int, int]],
        offset_x: int,
        offset_y: int,
        color: Tuple[int, int, int],
    ) -> None:
        """Lock the piece into the grid at the given offset with the specified color."""
        for x, y in shape_coords:
            gx = x + offset_x
            gy = y + offset_y
            grid[gy][gx] = color

    @staticmethod
    def clear_lines(grid: List[List[object | None]]) -> int:
        """Clear completed lines from the grid.

        Returns the number of lines cleared. The grid is updated in‑place with empty rows added at the top.
        """
        lines_cleared = 0
        new_grid = [row for row in grid if any(cell is None for cell in row)]
        lines_cleared = GRID_HEIGHT - len(new_grid)
        # Add empty rows on top
        for _ in range(lines_cleared):
            new_grid.insert(0, _cast(List[object | None], [None] * GRID_WIDTH))
        # Replace grid content
        for y in range(GRID_HEIGHT):
            grid[y] = new_grid[y]
        return lines_cleared


def run() -> None:
    """Run Tetris using the shared run helper."""
    from games.run_helper import run_game

    run_game(TetrisState)


if __name__ == "__main__":
    run()
