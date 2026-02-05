# games/breakout.py
"""Simple Breakout game implementation using Pygame.

Controls:
    Left/Right arrow keys - move the paddle.
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
    BLUE,
    YELLOW,
    CYAN,
    KEY_LEFT,
    KEY_RIGHT,
)
from utils import draw_text
from datetime import datetime
from games.highscore import add_score
from games.game_base import Game
from typing import List, Tuple

# Game constants
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 10
PADDLE_SPEED = 6
BALL_RADIUS = 8
BALL_SPEED = 5
BRICK_ROWS = 5
BRICK_COLS = 10
BRICK_WIDTH = (SCREEN_WIDTH - (BRICK_COLS + 1) * 5) // BRICK_COLS
BRICK_HEIGHT = 20
BRICK_SPACING = 5
FONT_SIZE = 24


class BreakoutState(Game):
    """State for the Breakout game, compatible with the engine loop."""

    def __init__(self) -> None:
        """Initialize Breakout game state, setting up paddle, ball, bricks, and scores."""
        super().__init__()
        # Initialize paddle
        self.paddle = pygame.Rect(
            (SCREEN_WIDTH - PADDLE_WIDTH) // 2,
            SCREEN_HEIGHT - PADDLE_HEIGHT - 30,
            PADDLE_WIDTH,
            PADDLE_HEIGHT,
        )
        # Ball starts above paddle
        self.ball = pygame.Rect(
            self.paddle.centerx - BALL_RADIUS,
            self.paddle.top - 2 * BALL_RADIUS,
            BALL_RADIUS * 2,
            BALL_RADIUS * 2,
        )
        self.ball_vel = [random.choice([-BALL_SPEED, BALL_SPEED]), -BALL_SPEED]
        self.bricks = create_bricks()
        self.score = 0
        self.game_over = False
        self.win = False
        # High‑score tracking flags
        self.highscore_recorded = False
        self.highscores = []

    def update(self, dt: float) -> None:
        """Update the game state: handle paddle movement, ball physics, collisions, scoring, and win/lose conditions."""
        if self.game_over or self.win or self.paused:
            return
        keys = pygame.key.get_pressed()
        # Paddle movement
        if keys[KEY_LEFT] and self.paddle.left > 0:
            self.paddle.move_ip(-PADDLE_SPEED, 0)
        if keys[KEY_RIGHT] and self.paddle.right < SCREEN_WIDTH:
            self.paddle.move_ip(PADDLE_SPEED, 0)
        # Ball movement
        self.ball.move_ip(*self.ball_vel)
        # Collisions with walls
        if self.ball.left <= 0 or self.ball.right >= SCREEN_WIDTH:
            self.ball_vel[0] = -self.ball_vel[0]
        if self.ball.top <= 0:
            self.ball_vel[1] = -self.ball_vel[1]
        # Collision with paddle
        if self.ball.colliderect(self.paddle) and self.ball_vel[1] > 0:
            self.ball_vel[1] = -self.ball_vel[1]
            offset = (self.ball.centerx - self.paddle.centerx) / (PADDLE_WIDTH / 2)
            self.ball_vel[0] = int(BALL_SPEED * offset)
        # Collision with bricks
        hit_index = self.ball.collidelist([br[0] for br in self.bricks])
        if hit_index != -1:
            brick_rect, brick_color = self.bricks.pop(hit_index)
            self.score += 1
            self.ball_vel[1] = -self.ball_vel[1]
        # Check win
        if not self.bricks:
            self.win = True
        # Check lose
        if self.ball.bottom >= SCREEN_HEIGHT:
            self.game_over = True

    def draw(self, screen: pygame.Surface) -> None:
        """Render the breakout game elements and UI onto the screen."""
        screen.fill(BLACK)
        # Draw paddle
        pygame.draw.rect(screen, WHITE, self.paddle)
        # Draw ball
        pygame.draw.ellipse(screen, GREEN, self.ball)
        # Draw bricks
        for rect, color in self.bricks:
            pygame.draw.rect(screen, color, rect)
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
            # Record high score once
            if not getattr(self, "highscore_recorded", False):
                self.highscores = add_score("breakout", self.score)
                self.highscore_recorded = True
            # Show heading and top 5 scores below the game‑over text
            start_y = SCREEN_HEIGHT // 2 + FONT_SIZE + 10
            # Heading
            draw_text(
                screen,
                "High Scores:",
                FONT_SIZE,
                WHITE,
                SCREEN_WIDTH // 2,
                start_y - (FONT_SIZE + 5),
                center=True,
            )
            for idx, entry in enumerate(self.highscores[:5], start=1):
                # Format timestamp to DD-MMM-YYYY
                try:
                    date_str = datetime.fromisoformat(entry["timestamp"]).strftime(
                        "%d-%b-%Y"
                    )
                except Exception:
                    date_str = entry["timestamp"]
                draw_text(
                    screen,
                    f"{idx}. {entry['score']} ({date_str})",
                    FONT_SIZE,
                    WHITE,
                    SCREEN_WIDTH // 2,
                    start_y + (idx - 1) * (FONT_SIZE + 5),
                    center=True,
                )
        if self.win:
            draw_text(
                screen,
                "You Win! Press R to restart or ESC to menu",
                FONT_SIZE,
                YELLOW,
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2,
                center=True,
            )
        # Draw pause overlay if paused
        if self.paused:
            self.draw_pause_overlay(screen)


def create_bricks() -> List[Tuple[pygame.Rect, Tuple[int, int, int]]]:
    """Create and return a list of brick (rect, color) tuples."""
    bricks = []
    colors = [RED, GREEN, BLUE, YELLOW, CYAN]
    for row in range(BRICK_ROWS):
        for col in range(BRICK_COLS):
            x = BRICK_SPACING + col * (BRICK_WIDTH + BRICK_SPACING)
            y = (
                BRICK_SPACING + row * (BRICK_HEIGHT + BRICK_SPACING) + 50
            )  # offset from top
            rect = pygame.Rect(x, y, BRICK_WIDTH, BRICK_HEIGHT)
            color = colors[row % len(colors)]
            bricks.append((rect, color))
    return bricks


def run() -> None:
    """Run Breakout using the shared run helper."""
    from games.run_helper import run_game

    run_game(BreakoutState)


if __name__ == "__main__":
    run()
