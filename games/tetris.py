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
import random
from utils import (
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
    draw_text,
)
from engine import State

# Game constants
CELL_SIZE = 20
GRID_WIDTH = 10
GRID_HEIGHT = 20
GRID_X_OFFSET = (SCREEN_WIDTH - GRID_WIDTH * CELL_SIZE) // 2
GRID_Y_OFFSET = (SCREEN_HEIGHT - GRID_HEIGHT * CELL_SIZE) // 2
FALL_SPEED = 500  # milliseconds per grid step (initial)
FAST_FALL_SPEED = 50
FONT_SIZE = 24

# State implementation for the engine
from engine import State
from utils import (
    draw_text,
    WHITE,
    BLACK,
    RED,
    GREEN,
    BLUE,
    YELLOW,
    CYAN,
    MAGENTA,
    GRAY,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
)
import pygame
import random


class TetrisState(State):
    """State for the Tetris game, compatible with the engine loop."""

    def __init__(self):
        super().__init__()
        # Initialize empty grid
        self.grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        # Piece state
        self.current_shape_name = random.choice(list(SHAPES.keys()))
        self.current_shape = SHAPES[self.current_shape_name]
        self.current_color = SHAPE_COLORS[self.current_shape_name]
        self.shape_x = GRID_WIDTH // 2 - 2
        self.shape_y = 0
        self.shape_coords = self.current_shape
        self.fall_timer = 0
        self.fall_interval = FALL_SPEED
        self.game_over = False
        self.score = 0
        self.level = 1
        self.lines_cleared_total = 0

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if not self.game_over:
                if event.key == pygame.K_LEFT:
                    if valid_position(
                        self.grid, self.shape_coords, self.shape_x - 1, self.shape_y
                    ):
                        self.shape_x -= 1
                elif event.key == pygame.K_RIGHT:
                    if valid_position(
                        self.grid, self.shape_coords, self.shape_x + 1, self.shape_y
                    ):
                        self.shape_x += 1
                elif event.key == pygame.K_DOWN:
                    self.fall_interval = FAST_FALL_SPEED
                elif event.key == pygame.K_UP:
                    new_coords = rotate(self.shape_coords)
                    if valid_position(
                        self.grid, new_coords, self.shape_x, self.shape_y
                    ):
                        self.shape_coords = new_coords
            else:
                if event.key == pygame.K_r:
                    self.__init__()
                elif event.key == pygame.K_ESCAPE:
                    from menu_items import get_menu_items
                    from engine import MenuState

                    self.request_transition(MenuState(get_menu_items()))

    def update(self, dt: float) -> None:
        if self.game_over:
            return
        # Reset fall speed after handling key press (if not holding down)
        keys = pygame.key.get_pressed()
        if not keys[pygame.K_DOWN]:
            self.fall_interval = FALL_SPEED
        # Update fall timer
        self.fall_timer += dt * 1000  # dt is seconds, convert to ms
        if self.fall_timer >= self.fall_interval:
            self.fall_timer = 0
            # Attempt to move piece down
            if valid_position(
                self.grid, self.shape_coords, self.shape_x, self.shape_y + 1
            ):
                self.shape_y += 1
            else:
                # Lock piece
                lock_piece(
                    self.grid,
                    self.shape_coords,
                    self.shape_x,
                    self.shape_y,
                    self.current_color,
                )
                # Clear lines
                lines = clear_lines(self.grid)
                if lines:
                    self.lines_cleared_total += lines
                    self.score += (lines**2) * 100
                    # Increase level every 5 lines cleared
                    if self.lines_cleared_total // 5 > (self.level - 1):
                        self.level += 1
                        self.fall_interval = max(50, FALL_SPEED - (self.level - 1) * 50)
                # Spawn new piece
                self.current_shape_name = random.choice(list(SHAPES.keys()))
                self.current_shape = SHAPES[self.current_shape_name]
                self.current_color = SHAPE_COLORS[self.current_shape_name]
                self.shape_coords = self.current_shape
                self.shape_x = GRID_WIDTH // 2 - 2
                self.shape_y = 0
                # Check immediate collision
                if not valid_position(
                    self.grid, self.shape_coords, self.shape_x, self.shape_y
                ):
                    self.game_over = True

    def draw(self, screen: pygame.Surface) -> None:
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
                    pygame.draw.rect(screen, cell_color, rect)
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
            draw_text(
                screen,
                "Game Over! Press R to restart or ESC to menu",
                FONT_SIZE,
                RED,
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2,
                center=True,
            )


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


def rotate(shape_coords):
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


def valid_position(grid, shape_coords, offset_x, offset_y):
    """Check if the shape at the given offset is within bounds and not colliding."""
    for x, y in shape_coords:
        gx = x + offset_x
        gy = y + offset_y
        if gx < 0 or gx >= GRID_WIDTH or gy < 0 or gy >= GRID_HEIGHT:
            return False
        if grid[gy][gx] is not None:
            return False
    return True


def lock_piece(grid, shape_coords, offset_x, offset_y, color):
    for x, y in shape_coords:
        gx = x + offset_x
        gy = y + offset_y
        grid[gy][gx] = color


def clear_lines(grid):
    lines_cleared = 0
    new_grid = [row for row in grid if any(cell is None for cell in row)]
    lines_cleared = GRID_HEIGHT - len(new_grid)
    # Add empty rows on top
    for _ in range(lines_cleared):
        new_grid.insert(0, [None] * GRID_WIDTH)
    # Replace grid content
    for y in range(GRID_HEIGHT):
        grid[y] = new_grid[y]
    return lines_cleared


def run():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Tetris")
    clock = pygame.time.Clock()

    # Initialize empty grid (None for empty, otherwise a color tuple)
    grid = [[None for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]

    # Piece state
    current_shape_name = random.choice(list(SHAPES.keys()))
    current_shape = SHAPES[current_shape_name]
    current_color = SHAPE_COLORS[current_shape_name]
    shape_x = GRID_WIDTH // 2 - 2  # start near middle
    shape_y = 0
    shape_coords = current_shape
    fall_timer = 0
    fall_interval = FALL_SPEED
    game_over = False
    score = 0
    level = 1
    lines_cleared_total = 0

    while True:
        dt = clock.tick(60)
        fall_timer += dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.KEYDOWN:
                if not game_over:
                    if event.key == pygame.K_LEFT:
                        if valid_position(grid, shape_coords, shape_x - 1, shape_y):
                            shape_x -= 1
                    elif event.key == pygame.K_RIGHT:
                        if valid_position(grid, shape_coords, shape_x + 1, shape_y):
                            shape_x += 1
                    elif event.key == pygame.K_DOWN:
                        # Soft drop: accelerate fall
                        fall_interval = FAST_FALL_SPEED
                    elif event.key == pygame.K_UP:
                        # Rotate clockwise
                        new_coords = rotate(shape_coords)
                        if valid_position(grid, new_coords, shape_x, shape_y):
                            shape_coords = new_coords
                else:
                    if event.key == pygame.K_r:
                        return run()
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        return
        # Reset fall speed after handling key press (if not holding down)
        keys = pygame.key.get_pressed()
        if not keys[pygame.K_DOWN]:
            fall_interval = FALL_SPEED

        if not game_over and fall_timer >= fall_interval:
            fall_timer = 0
            # Attempt to move piece down
            if valid_position(grid, shape_coords, shape_x, shape_y + 1):
                shape_y += 1
            else:
                # Lock piece
                lock_piece(grid, shape_coords, shape_x, shape_y, current_color)
                # Clear lines
                lines = clear_lines(grid)
                if lines:
                    lines_cleared_total += lines
                    score += (lines**2) * 100
                    # Increase level every 5 lines cleared
                    if lines_cleared_total // 5 > (level - 1):
                        level += 1
                        fall_interval = max(50, FALL_SPEED - (level - 1) * 50)
                # Spawn new piece
                current_shape_name = random.choice(list(SHAPES.keys()))
                current_shape = SHAPES[current_shape_name]
                current_color = SHAPE_COLORS[current_shape_name]
                shape_coords = current_shape
                shape_x = GRID_WIDTH // 2 - 2
                shape_y = 0
                # Check if new piece collides immediately -> game over
                if not valid_position(grid, shape_coords, shape_x, shape_y):
                    game_over = True
        # Drawing
        screen.fill(BLACK)
        # Draw grid cells
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                cell_color = grid[y][x]
                if cell_color:
                    rect = pygame.Rect(
                        GRID_X_OFFSET + x * CELL_SIZE,
                        GRID_Y_OFFSET + y * CELL_SIZE,
                        CELL_SIZE,
                        CELL_SIZE,
                    )
                    pygame.draw.rect(screen, cell_color, rect)
                    # Optional: draw cell border
                    pygame.draw.rect(screen, GRAY, rect, 1)
        # Draw current falling piece
        if not game_over:
            for x_offset, y_offset in shape_coords:
                gx = shape_x + x_offset
                gy = shape_y + y_offset
                if gy >= 0:
                    rect = pygame.Rect(
                        GRID_X_OFFSET + gx * CELL_SIZE,
                        GRID_Y_OFFSET + gy * CELL_SIZE,
                        CELL_SIZE,
                        CELL_SIZE,
                    )
                    pygame.draw.rect(screen, current_color, rect)
                    pygame.draw.rect(screen, GRAY, rect, 1)
        # Draw score and level
        draw_text(screen, f"Score: {score}", FONT_SIZE, WHITE, 60, 20, center=False)
        draw_text(
            screen,
            f"Level: {level}",
            FONT_SIZE,
            WHITE,
            SCREEN_WIDTH - 100,
            20,
            center=False,
        )
        if game_over:
            draw_text(
                screen,
                "Game Over! Press R to restart or ESC to menu",
                FONT_SIZE,
                RED,
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2,
                center=True,
            )
        pygame.display.flip()


if __name__ == "__main__":
    run()
