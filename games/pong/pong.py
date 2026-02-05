# games/pong.py
"""Simple Pong game implementation using Pygame.

Controls:
    Up/Down arrow keys - move the left paddle (player).
    R - restart after game over.
    ESC - return to main menu.
"""

import pygame
from config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    WHITE,
    BLACK,
    GREEN,
    RED,
    BLUE,
    KEY_UP,
    KEY_DOWN,
)
from utils import draw_text
from typing import Optional
from games.game_base import Game

# Game constants
PADDLE_WIDTH = 10
PADDLE_HEIGHT = 100
BALL_SIZE = 10
MAX_SCORE = 10
PADDLE_SPEED = 5
BALL_SPEED_X = 4
BALL_SPEED_Y = 4
FONT_SIZE = 24


class PongState(Game):
    """Game class for Pong, inherits from ``Game`` and compatible with the engine loop."""

    def __init__(self) -> None:
        """Initialize Pong game state, setting up paddles, ball, and scores."""
        super().__init__()
        # Initialize paddles
        self.left_paddle = pygame.Rect(
            20, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT
        )
        self.right_paddle = pygame.Rect(
            SCREEN_WIDTH - 20 - PADDLE_WIDTH,
            SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2,
            PADDLE_WIDTH,
            PADDLE_HEIGHT,
        )
        # Initialize ball
        self.ball = pygame.Rect(
            SCREEN_WIDTH // 2 - BALL_SIZE // 2,
            SCREEN_HEIGHT // 2 - BALL_SIZE // 2,
            BALL_SIZE,
            BALL_SIZE,
        )
        self.ball_vel = [BALL_SPEED_X, BALL_SPEED_Y]
        # Scores
        self.left_score = 0
        self.right_score = 0
        self.game_over = False
        self.winner: Optional[str] = None

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle key events for Pong.

        Delegates ESC, pause, and restart handling to the base ``Game`` class.
        No additional event handling is required for Pong.
        """
        # Let Game base handle ESC, pause, restart
        super().handle_event(event)
        # No additional handling needed for Pong

    def update(self, dt: float) -> None:
        """Update the Pong game state.

        Handles paddle movement, simple AI for the right paddle, ball movement, collisions, scoring, and win condition.
        """
        if self.game_over or self.paused:
            return
        keys = pygame.key.get_pressed()
        # Player paddle movement
        if keys[KEY_UP] and self.left_paddle.top > 0:
            self.left_paddle.move_ip(0, -PADDLE_SPEED)
        if keys[KEY_DOWN] and self.left_paddle.bottom < SCREEN_HEIGHT:
            self.left_paddle.move_ip(0, PADDLE_SPEED)
        # Simple AI for right paddle: follow ball Y position
        if self.ball.centery < self.right_paddle.centery and self.right_paddle.top > 0:
            self.right_paddle.move_ip(0, -PADDLE_SPEED)
        elif (
            self.ball.centery > self.right_paddle.centery
            and self.right_paddle.bottom < SCREEN_HEIGHT
        ):
            self.right_paddle.move_ip(0, PADDLE_SPEED)
        # Ball movement
        self.ball.move_ip(*self.ball_vel)
        # Collisions with top/bottom
        if self.ball.top <= 0 or self.ball.bottom >= SCREEN_HEIGHT:
            self.ball_vel[1] = -self.ball_vel[1]
        # Collisions with paddles
        if self.ball.colliderect(self.left_paddle) and self.ball_vel[0] < 0:
            self.ball_vel[0] = -self.ball_vel[0]
        if self.ball.colliderect(self.right_paddle) and self.ball_vel[0] > 0:
            self.ball_vel[0] = -self.ball_vel[0]
        # Scoring
        if self.ball.left <= 0:
            self.right_score += 1
            self.ball.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
            self.ball_vel = [BALL_SPEED_X, BALL_SPEED_Y]
        if self.ball.right >= SCREEN_WIDTH:
            self.left_score += 1
            self.ball.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
            self.ball_vel = [-BALL_SPEED_X, -BALL_SPEED_Y]
        # Win condition
        if self.left_score >= MAX_SCORE:
            self.game_over = True
            self.winner = "Player"
        elif self.right_score >= MAX_SCORE:
            self.game_over = True
            self.winner = "AI"

    def draw(self, screen: pygame.Surface) -> None:
        """Render the Pong game elements and UI onto the screen.

        Draws the paddles, ball, and current scores. If the game is over, displays the winner.
        """
        screen.fill(BLACK)
        # Draw paddles and ball
        pygame.draw.rect(screen, WHITE, self.left_paddle)
        pygame.draw.rect(screen, WHITE, self.right_paddle)
        pygame.draw.ellipse(screen, GREEN, self.ball)
        # Draw scores
        draw_text(
            screen,
            f"{self.left_score}",
            FONT_SIZE,
            WHITE,
            SCREEN_WIDTH // 4,
            30,
            center=True,
        )
        draw_text(
            screen,
            f"{self.right_score}",
            FONT_SIZE,
            WHITE,
            SCREEN_WIDTH * 3 // 4,
            30,
            center=True,
        )
        if self.game_over:
            draw_text(
                screen,
                f"{self.winner} wins! Press R to restart or ESC to menu",
                FONT_SIZE,
                RED,
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2,
                center=True,
            )


def run() -> None:
    """Run Pong using the shared run helper."""
    from games.run_helper import run_game

    run_game(PongState)


if __name__ == "__main__":
    run()
