# games/snake.py
"""Simple Snake game implementation using Pygame.

Controls:
    Arrow keys - change direction of the snake.
    R - restart after game over.
    ESC - return to main menu.
"""

import pygame
import random
from config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    WHITE,
    BLACK,
    RED,
    GREEN,
    YELLOW,
    KEY_UP,
    KEY_DOWN,
    KEY_LEFT,
    KEY_RIGHT,
)
from utils import draw_text
from datetime import datetime
from games.highscore import add_score
from games.game_base import Game
from engine import Engine
import audio

# Game constants
BLOCK_SIZE = 20
SNAKE_SPEED = 10  # frames per second


class SnakeState(Game):
    """State for the Snake game, compatible with the engine loop."""

    def __init__(self) -> None:
        """Initialize Snake game state, setting up the snake, direction, food, and game variables."""
        super().__init__()
        # Initialize game state
        self.snake = [(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)]
        self.direction = (0, 0)
        self.food = (
            random.randrange(0, SCREEN_WIDTH // BLOCK_SIZE) * BLOCK_SIZE,
            random.randrange(0, SCREEN_HEIGHT // BLOCK_SIZE) * BLOCK_SIZE,
        )
        self.score = 0
        self.font_size = 24
        self.game_over = False
        # High‑score tracking flags
        self.highscore_recorded = False
        self.highscores = []
        self._time_acc = 0.0

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle key events for the Snake game.

        Updates the snake's direction based on arrow key presses. Delegates other events (ESC, pause, restart) to the base ``Game`` class.
        """
        if event.type == pygame.KEYDOWN:
            if not self.game_over:
                if event.key == KEY_UP:
                    self.direction = (0, -BLOCK_SIZE)
                elif event.key == KEY_DOWN:
                    self.direction = (0, BLOCK_SIZE)
                elif event.key == KEY_LEFT:
                    self.direction = (-BLOCK_SIZE, 0)
                elif event.key == KEY_RIGHT:
                    self.direction = (BLOCK_SIZE, 0)
        # Delegate remaining keys (ESC, P, R) and other events to base class
        super().handle_event(event)

    def update(self, dt: float) -> None:
        """Update the Snake game state.

        Handles timing, moves the snake, processes food consumption, and checks for collisions with walls or self.
        """
        if self.game_over or self.paused:
            return
        # Accumulate time and move snake at the defined speed
        self._time_acc += dt
        interval = 1.0 / SNAKE_SPEED
        while self._time_acc >= interval:
            self._time_acc -= interval
            if self.direction != (0, 0):
                new_head = (
                    self.snake[0][0] + self.direction[0],
                    self.snake[0][1] + self.direction[1],
                )
                # Check wall collision
                if (
                    new_head[0] < 0
                    or new_head[0] >= SCREEN_WIDTH
                    or new_head[1] < 0
                    or new_head[1] >= SCREEN_HEIGHT
                ):
                    self.game_over = True
                    # Play crash/game-over sound
                    try:
                        audio.play_effect("crash.wav")
                    except Exception:
                        pass
                else:
                    self.snake.insert(0, new_head)
                    # Food collision
                    if new_head == self.food:
                        self.score += 1
                        # Play food-eat sound effect
                        try:
                            audio.play_effect("eat.wav")
                        except Exception:
                            pass
                        # Place new food not on the snake
                        while True:
                            self.food = (
                                random.randrange(0, SCREEN_WIDTH // BLOCK_SIZE)
                                * BLOCK_SIZE,
                                random.randrange(0, SCREEN_HEIGHT // BLOCK_SIZE)
                                * BLOCK_SIZE,
                            )
                            if self.food not in self.snake:
                                break
                    else:
                        self.snake.pop()
                    # Self collision
                    if new_head in self.snake[1:]:
                        self.game_over = True

    def draw(self, screen: pygame.Surface) -> None:
        """Render the Snake game elements and UI onto the screen.

        Draws the background, food, snake segments, and the current score. If the game is over, displays a game‑over message.
        """
        # Clear background
        screen.fill(BLACK)
        # Draw food
        pygame.draw.rect(screen, RED, (*self.food, BLOCK_SIZE, BLOCK_SIZE))
        # Draw snake
        for segment in self.snake:
            pygame.draw.rect(screen, GREEN, (*segment, BLOCK_SIZE, BLOCK_SIZE))
        # Draw score
        draw_text(
            screen, f"Score: {self.score}", self.font_size, WHITE, 60, 20, center=False
        )
        if self.game_over:
            # Record high score (snake length is score) once
            if not getattr(self, "highscore_recorded", False):
                self.highscores = add_score("snake", self.score)
                self.highscore_recorded = True
            # Layout positions
            heading_y = int(SCREEN_HEIGHT * 0.20)
            instr_y = int(SCREEN_HEIGHT * 0.80)
            # Heading
            draw_text(
                screen,
                "High Scores:",
                24,
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
                score_y = heading_y + 24 + 5 + (idx - 1) * (24 + 5)
                draw_text(
                    screen,
                    f"{idx}. {entry['score']} ({date_str})",
                    24,
                    WHITE,
                    SCREEN_WIDTH // 2,
                    score_y,
                    center=True,
                )
            # Instruction line at bottom
            draw_text(
                screen,
                "Game Over! Press R to restart or ESC to menu",
                24,
                YELLOW,
                SCREEN_WIDTH // 2,
                instr_y,
                center=True,
            )
        # Draw pause overlay if paused
        if self.paused:
            self.draw_pause_overlay(screen)
        # Draw mute overlay (Muted or Sound On)
        self.draw_mute_overlay(screen)


# Run function removed; use package-level run()
