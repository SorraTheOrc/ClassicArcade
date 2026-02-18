# games/tetris.py
"""Simple Tetris game implementation using Pygame.

Controls:
    Left/Right arrow keys - move piece left/right.
    Up arrow - rotate piece.
    Down arrow - soft drop (increase descent speed).
    R - restart after game over.
    ESC - return to main menu.
"""

import logging
import random
from datetime import datetime
from typing import List, Tuple
from typing import cast as _cast

import pygame

from classic_arcade import audio
from classic_arcade.config import (
    BLACK,
    BLUE,
    CYAN,
    FONT_SIZE_LARGE,
    FONT_SIZE_MEDIUM,
    FONT_SIZE_SMALL,
    GRAY,
    GREEN,
    KEY_DOWN,
    KEY_LEFT,
    KEY_RIGHT,
    KEY_UP,
    MAGENTA,
    RED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WHITE,
    YELLOW,
)
from classic_arcade.constants import COUNTDOWN_SECONDS
from classic_arcade.difficulty import apply_difficulty_divisor
from classic_arcade.engine import State
from classic_arcade.utils import draw_text
from games.game_base import Game
from games.highscore import draw_highscore_screen, record_highscore

logger = logging.getLogger(__name__)

# Base speed values for difficulty scaling (default values)
BASE_FALL_SPEED = 500
BASE_FAST_FALL_SPEED = 50
LINES_PER_LEVEL = 5
SCORE_CALCULATION = 100

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
    """Set fall speed variables based on the current Tetris difficulty."""
    global FALL_SPEED, FAST_FALL_SPEED
    FALL_SPEED = apply_difficulty_divisor(BASE_FALL_SPEED, "tetris")
    FAST_FALL_SPEED = apply_difficulty_divisor(BASE_FAST_FALL_SPEED, "tetris")


from classic_arcade import config


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
        # Handle countdown
        if self.countdown_active:
            self.countdown_remaining -= dt
            if self.countdown_remaining <= 0:
                # Start new level (keep current state but with increased speed)
                self.countdown_active = False
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
                    self.score += (lines**2) * SCORE_CALCULATION
                    # Play line clear sound once per cleared line.
                    # This should happen regardless of whether the level
                    # increased — moving playback out of the level-up block
                    # ensures the player always receives audio feedback.
                    for _ in range(lines):
                        audio.play_effect("tetris", "line_clear.wav")
                    # Increase level every LINES_PER_LEVEL lines cleared
                    if self.lines_cleared_total // LINES_PER_LEVEL > (self.level - 1):
                        self.level += 1
                        self.fall_interval = max(50, FALL_SPEED - (self.level - 1) * 50)
                        # Start level transition countdown
                        self.countdown_active = True
                        self.countdown_remaining = 3.0
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
            screen,
            f"Score: {self.score}",
            FONT_SIZE_MEDIUM,
            WHITE,
            60,
            20,
            center=False,
        )
        if self.game_over:
            record_highscore(self, "tetris", self.score)
            draw_highscore_screen(
                screen,
                self.highscores,
                instruction_text="Game Over! Press R to restart or ESC to menu",
                instruction_color=RED,
                font_size=FONT_SIZE_MEDIUM,
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

    run_game(TetrisModeSelectState)


class Tetris2PlayerState(Game):
    """Two-player Tetris game where each player competes on separate grids side-by-side.

    Player 1 uses arrow keys on the left grid.
    Player 2 uses WASD keys on the right grid.
    """

    SHAPES = TetrisState.SHAPES
    SHAPE_COLORS = TetrisState.SHAPE_COLORS
    rotate = staticmethod(TetrisState.rotate)
    valid_position = staticmethod(TetrisState.valid_position)
    lock_piece = staticmethod(TetrisState.lock_piece)
    clear_lines = staticmethod(TetrisState.clear_lines)

    def __init__(self) -> None:
        """Initialize 2-player Tetris game state."""
        super().__init__()
        _apply_tetris_speed_settings()
        logger.info(
            f"2-Player Tetris game started: difficulty={config.TETRIS_DIFFICULTY}, fall_speed={FALL_SPEED}, fast_fall_speed={FAST_FALL_SPEED}"
        )

        # Player 1 (left side)
        self.grid1: List[List[object | None]] = [
            [None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)
        ]
        self.current_shape_name1 = random.choice(list(self.SHAPES.keys()))
        self.current_shape1 = self.SHAPES[self.current_shape_name1]
        self.current_color1 = self.SHAPE_COLORS[self.current_shape_name1]
        self.shape_x1 = GRID_WIDTH // 2 - 2
        self.shape_y1 = 0
        self.shape_coords1 = self.current_shape1
        self.fall_timer1 = 0.0
        self.fall_interval1 = FALL_SPEED
        self.game_over1 = False
        self.highscore_recorded1 = False
        self.score1 = 0
        self.level1 = 1
        self.lines_cleared_total1 = 0

        # Player 2 (right side)
        self.grid2: List[List[object | None]] = [
            [None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)
        ]
        self.current_shape_name2 = random.choice(list(self.SHAPES.keys()))
        self.current_shape2 = self.SHAPES[self.current_shape_name2]
        self.current_color2 = self.SHAPE_COLORS[self.current_shape_name2]
        self.shape_x2 = GRID_WIDTH // 2 - 2
        self.shape_y2 = 0
        self.shape_coords2 = self.current_shape2
        self.fall_timer2 = 0.0
        self.fall_interval2 = FALL_SPEED
        self.game_over2 = False
        self.highscore_recorded2 = False
        self.score2 = 0
        self.level2 = 1
        self.lines_cleared_total2 = 0

        self.countdown_active = False
        self.countdown_remaining = 0.0

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle user input for piece movement and rotation for both players."""
        super().handle_event(event)
        if event.type == pygame.KEYDOWN:
            # Player 1 controls (arrow keys)
            if not self.game_over1:
                if event.key == KEY_LEFT:
                    if self.valid_position(
                        self.grid1, self.shape_coords1, self.shape_x1 - 1, self.shape_y1
                    ):
                        self.shape_x1 -= 1
                elif event.key == KEY_RIGHT:
                    if self.valid_position(
                        self.grid1, self.shape_coords1, self.shape_x1 + 1, self.shape_y1
                    ):
                        self.shape_x1 += 1
                elif event.key == KEY_DOWN:
                    self.fall_interval1 = FAST_FALL_SPEED
                elif event.key == KEY_UP:
                    new_coords = self.rotate(self.shape_coords1)
                    if self.valid_position(
                        self.grid1, new_coords, self.shape_x1, self.shape_y1
                    ):
                        self.shape_coords1 = new_coords
                        audio.play_effect("tetris", "rotate.wav")

            # Player 2 controls (WASD)
            if not self.game_over2:
                if event.key == pygame.K_a:
                    if self.valid_position(
                        self.grid2, self.shape_coords2, self.shape_x2 - 1, self.shape_y2
                    ):
                        self.shape_x2 -= 1
                elif event.key == pygame.K_d:
                    if self.valid_position(
                        self.grid2, self.shape_coords2, self.shape_x2 + 1, self.shape_y2
                    ):
                        self.shape_x2 += 1
                elif event.key == pygame.K_s:
                    self.fall_interval2 = FAST_FALL_SPEED
                elif event.key == pygame.K_w:
                    new_coords = self.rotate(self.shape_coords2)
                    if self.valid_position(
                        self.grid2, new_coords, self.shape_x2, self.shape_y2
                    ):
                        self.shape_coords2 = new_coords
                        audio.play_effect("tetris", "rotate.wav")

    def update(self, dt: float) -> None:
        """Update the 2-player Tetris game state."""
        if self.countdown_active:
            self.countdown_remaining -= dt
            if self.countdown_remaining <= 0:
                self.countdown_active = False
            return

        # Update both players
        self._update_player(
            dt,
            self.grid1,
            self.shape_coords1,
            self.shape_x1,
            self.shape_y1,
            self.current_shape_name1,
            self.current_shape1,
            self.current_color1,
            self.fall_timer1,
            self.fall_interval1,
            self.score1,
            self.level1,
            self.lines_cleared_total1,
            self.game_over1,
            1,
        )
        self._update_player(
            dt,
            self.grid2,
            self.shape_coords2,
            self.shape_x2,
            self.shape_y2,
            self.current_shape_name2,
            self.current_shape2,
            self.current_color2,
            self.fall_timer2,
            self.fall_interval2,
            self.score2,
            self.level2,
            self.lines_cleared_total2,
            self.game_over2,
            2,
        )

    def _update_player(
        self,
        dt: float,
        grid,
        shape_coords,
        shape_x,
        shape_y,
        shape_name,
        shape,
        color,
        fall_timer,
        fall_interval,
        score,
        level,
        lines_total,
        game_over,
        player_num,
    ) -> None:
        """Update a single player's Tetris state."""
        if game_over or self.paused:
            return

        keys = pygame.key.get_pressed()
        try:
            down_is_pressed = bool(
                keys[KEY_DOWN] if player_num == 1 else keys[pygame.K_s]
            )
        except Exception:
            down_is_pressed = False

        if not down_is_pressed:
            fall_interval = FALL_SPEED if player_num == 1 else FALL_SPEED

        fall_timer += dt * 1000
        if fall_timer >= fall_interval:
            fall_timer = 0.0
            if self.valid_position(grid, shape_coords, shape_x, shape_y + 1):
                shape_y += 1
            else:
                self.lock_piece(grid, shape_coords, shape_x, shape_y, color)
                audio.play_effect("tetris", "place.wav")

                lines = self.clear_lines(grid)
                if lines:
                    lines_total += lines
                    score += (lines**2) * SCORE_CALCULATION
                    for _ in range(lines):
                        audio.play_effect("tetris", "line_clear.wav")
                    if lines_total // LINES_PER_LEVEL > (level - 1):
                        level += 1
                        fall_interval = max(50, FALL_SPEED - (level - 1) * 50)
                        self.countdown_active = True
                        self.countdown_remaining = COUNTDOWN_SECONDS

                shape_name = random.choice(list(self.SHAPES.keys()))
                shape = self.SHAPES[shape_name]
                color = self.SHAPE_COLORS[shape_name]
                shape_coords = shape
                shape_x = GRID_WIDTH // 2 - 2
                shape_y = 0

                if not self.valid_position(grid, shape_coords, shape_x, shape_y):
                    game_over = True

    def draw(self, screen: pygame.Surface) -> None:
        """Render the 2-player Tetris game with split screen."""
        # Draw center divider
        pygame.draw.line(
            screen, WHITE, (SCREEN_WIDTH // 2, 0), (SCREEN_WIDTH // 2, SCREEN_HEIGHT), 2
        )

        # Draw Player 1 (left)
        self._draw_player(
            screen,
            self.grid1,
            self.shape_coords1,
            self.shape_x1,
            self.shape_y1,
            self.current_color1,
            self.score1,
            1,
            0,
            SCREEN_WIDTH // 2,
        )

        # Draw Player 2 (right)
        self._draw_player(
            screen,
            self.grid2,
            self.shape_coords2,
            self.shape_x2,
            self.shape_y2,
            self.current_color2,
            self.score2,
            2,
            SCREEN_WIDTH // 2,
            SCREEN_WIDTH,
        )

        # Game over display
        if self.game_over1 and self.game_over2:
            record_highscore(self, "tetris", max(self.score1, self.score2))

            winner = (
                "Player 1"
                if self.score1 > self.score2
                else ("Player 2" if self.score2 > self.score1 else "Tie")
            )
            draw_text(
                screen,
                f"{winner} wins!",
                FONT_SIZE_LARGE,
                YELLOW,
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2 - 50,
                center=True,
            )
            draw_text(
                screen,
                f"P1: {self.score1}  -  P2: {self.score2}",
                FONT_SIZE_MEDIUM,
                WHITE,
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2,
                center=True,
            )
            draw_text(
                screen,
                "Press R to restart or ESC to menu",
                FONT_SIZE_MEDIUM,
                CYAN,
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT - 50,
                center=True,
            )
        elif self.paused:
            self.draw_pause_overlay(screen)

    def _draw_player(
        self,
        screen,
        grid,
        shape_coords,
        shape_x,
        shape_y,
        color,
        score,
        player_num,
        x_start,
        x_end,
    ) -> None:
        """Draw a single player's Tetris grid."""
        # Calculate grid position for this player
        grid_x_offset = x_start + (SCREEN_WIDTH // 2 - GRID_WIDTH * CELL_SIZE) // 2
        grid_y_offset = (SCREEN_HEIGHT - GRID_HEIGHT * CELL_SIZE) // 2

        # Draw grid background
        screen.fill(BLACK, (x_start, 0, x_end - x_start, SCREEN_HEIGHT))
        pygame.draw.rect(screen, GRAY, (x_start, 0, x_end - x_start, SCREEN_HEIGHT), 1)

        # Draw grid cells
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                cell_color = grid[y][x]
                if cell_color:
                    rect = pygame.Rect(
                        grid_x_offset + x * CELL_SIZE,
                        grid_y_offset + y * CELL_SIZE,
                        CELL_SIZE,
                        CELL_SIZE,
                    )
                    pygame.draw.rect(
                        screen, _cast(Tuple[int, int, int], cell_color), rect
                    )

        # Draw current falling piece
        for x_offset, y_offset in shape_coords:
            gx = shape_x + x_offset
            gy = shape_y + y_offset
            if 0 <= gx < GRID_WIDTH and 0 <= gy < GRID_HEIGHT:
                rect = pygame.Rect(
                    grid_x_offset + gx * CELL_SIZE,
                    grid_y_offset + gy * CELL_SIZE,
                    CELL_SIZE,
                    CELL_SIZE,
                )
                pygame.draw.rect(screen, color, rect)

        # Draw score
        draw_text(
            screen,
            f"P{player_num}: {score}",
            FONT_SIZE_MEDIUM,
            WHITE,
            x_start + (x_end - x_start) // 2,
            20,
            center=True,
        )

    @classmethod
    def get_controls(cls) -> List[str]:
        """Return control instructions for 2-player Tetris.

        Returns:
            List of control description strings.
        """
        return [
            "Player 1: Arrow keys to move/rotate",
            "Player 2: WASD keys to move/rotate",
            "R: Restart after game over",
            "ESC: Return to main menu",
        ]


class TetrisModeSelectState(State):
    """Mode selection screen for Tetris game.

    Allows the player to choose between single-player and 2-player modes.
    """

    def __init__(self) -> None:
        """Initialize the mode selection screen."""
        super().__init__()
        self.options = ["Single Player", "2 Player (Versus)"]
        self.selected = 0
        self.title_font_size = 48
        self.item_font_size = 32

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle key events for mode selection."""
        if event.type == pygame.KEYDOWN:
            if event.key == KEY_UP:
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key == KEY_DOWN:
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.selected == 0:
                    from games.tetris import TetrisState

                    self.request_transition(TetrisState())
                elif self.selected == 1:
                    from games.tetris import Tetris2PlayerState

                    self.request_transition(Tetris2PlayerState())
            elif event.key == pygame.K_ESCAPE:
                from classic_arcade.engine import MenuState

                self.request_transition(MenuState([]))

    def update(self, dt: float) -> None:
        """Update mode selection state."""
        pass

    def draw(self, screen: pygame.Surface) -> None:
        """Render mode selection screen."""
        screen.fill(BLACK)

        # Draw title
        draw_text(
            screen,
            "Select Tetris Mode",
            self.title_font_size,
            WHITE,
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 3,
            center=True,
        )

        # Draw options
        for i, option in enumerate(self.options):
            if i == self.selected:
                text_color = GREEN
            else:
                text_color = WHITE

            draw_text(
                screen,
                option,
                self.item_font_size,
                text_color,
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2 + i * 50,
                center=True,
            )
