# games/pong/pong.py
"""Simple Pong game implementation using Pygame.

Controls:
    W/S keys - move the left paddle (player) in single-player and multiplayer.
    Up/Down arrow keys - move the right paddle (player in multiplayer) or also control left paddle in single-player.
    R - restart after game over.
    ESC - return to main menu.
"""

import logging
from datetime import datetime
from typing import List, Optional

import pygame

import config
from config import (
    BLACK,
    BLUE,
    GREEN,
    KEY_DOWN,
    KEY_S,
    KEY_UP,
    KEY_W,
    RED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WHITE,
)
from games.game_base import Game
from games.highscore import add_score
from utils import draw_text

logger = logging.getLogger(__name__)

# Game constants
PADDLE_WIDTH = 10
PADDLE_HEIGHT = 60
BALL_SIZE = 10
MAX_SCORE = 10
# Base speed values
BASE_PADDLE_SPEED = 5
BASE_BALL_SPEED_X = 4
BASE_BALL_SPEED_Y = 4


def _apply_pong_speed_settings() -> None:
    """Set global speed variables based on the current PONG_DIFFICULTY."""
    global PADDLE_SPEED, BALL_SPEED_X, BALL_SPEED_Y, AI_PADDLE_SPEED
    if config.PONG_DIFFICULTY == config.DIFFICULTY_EASY:
        PADDLE_SPEED = BASE_PADDLE_SPEED
        BALL_SPEED_X = BASE_BALL_SPEED_X
        BALL_SPEED_Y = BASE_BALL_SPEED_Y
        AI_PADDLE_SPEED = BASE_PADDLE_SPEED
    elif config.PONG_DIFFICULTY == config.DIFFICULTY_MEDIUM:
        PADDLE_SPEED = int(BASE_PADDLE_SPEED * 1.2)
        BALL_SPEED_X = int(BASE_BALL_SPEED_X * 1.5)
        BALL_SPEED_Y = int(BASE_BALL_SPEED_Y * 1.5)
        AI_PADDLE_SPEED = int(BASE_PADDLE_SPEED * 1.2)
    else:
        # Hard difficulty
        PADDLE_SPEED = int(BASE_PADDLE_SPEED * 1.5)
        BALL_SPEED_X = int(BASE_BALL_SPEED_X * 2)
        BALL_SPEED_Y = int(BASE_BALL_SPEED_Y * 2)
        AI_PADDLE_SPEED = int(BASE_PADDLE_SPEED * 1.5)


FONT_SIZE = 24


class PongState(Game):
    """Game class for Pong, inherits from ``Game`` and compatible with the engine loop."""

    # Class attribute to indicate multiplayer mode (False for single‑player AI)
    MULTIPLAYER = False

    def __init__(self) -> None:
        """Initialize Pong game state, setting up paddles, ball, and scores."""
        super().__init__()
        _apply_pong_speed_settings()
        logger.info(
            f"Pong game started: difficulty={config.PONG_DIFFICULTY}, paddle_speed={PADDLE_SPEED}, ball_speed_x={BALL_SPEED_X}, ball_speed_y={BALL_SPEED_Y}, ai_paddle_speed={AI_PADDLE_SPEED}"
        )
        self.left_paddle = pygame.Rect(
            20, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT
        )
        self.right_paddle = pygame.Rect(
            SCREEN_WIDTH - 20 - PADDLE_WIDTH,
            SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2,
            PADDLE_WIDTH,
            PADDLE_HEIGHT,
        )
        self.ball = pygame.Rect(
            SCREEN_WIDTH // 2 - BALL_SIZE // 2,
            SCREEN_HEIGHT // 2 - BALL_SIZE // 2,
            BALL_SIZE,
            BALL_SIZE,
        )
        self.ball_vel = [BALL_SPEED_X, BALL_SPEED_Y]
        self.left_score = 0
        self.right_score = 0
        self.game_over = False
        self.highscore_recorded = False
        self.highscores = []
        self.winner: Optional[str] = None
        self.ai_target_center_y: Optional[int] = None
        self.ai_delay_timer: float = 0.0
        self.multiplayer = getattr(self, "MULTIPLAYER", False)

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle key events for Pong.

        Delegates ESC, pause, and restart handling to the base ``Game`` class.
        No additional event handling is required for Pong.
        """
        super().handle_event(event)

    def update(self, dt: float) -> None:
        """Update the Pong game state.

        Handles paddle movement, AI or multiplayer control for the right paddle, ball movement,
        collisions, scoring, and win condition.
        """
        if self.game_over or self.paused:
            return
        keys = pygame.key.get_pressed()
        # Player paddle (left) movement: W/A always control left paddle; in single-player mode, also allow UP/DOWN
        move_up = (
            keys[KEY_W] or (not self.multiplayer and keys[KEY_UP])
        ) and self.left_paddle.top > 0
        move_down = (
            keys[KEY_S] or (not self.multiplayer and keys[KEY_DOWN])
        ) and self.left_paddle.bottom < SCREEN_HEIGHT
        if move_up:
            self.left_paddle.move_ip(0, -PADDLE_SPEED)
        if move_down:
            self.left_paddle.move_ip(0, PADDLE_SPEED)
        # Right paddle control
        if self.multiplayer:
            # Human control: UP/DOWN keys move the right paddle
            if keys[KEY_UP] and self.right_paddle.top > 0:
                self.right_paddle.move_ip(0, -AI_PADDLE_SPEED)
            if keys[KEY_DOWN] and self.right_paddle.bottom < SCREEN_HEIGHT:
                self.right_paddle.move_ip(0, AI_PADDLE_SPEED)
        else:
            # AI control with predictive movement and a single random error per ball approach
            import random

            if self.ball_vel[0] > 0:
                # Compute a new target only when we don't have one for the current ball approach
                if self.ai_target_center_y is None:
                    distance = self.right_paddle.left - self.ball.right
                    steps = distance // self.ball_vel[0] if distance > 0 else 0
                    pred_y = self.ball.top
                    pred_vy = self.ball_vel[1]
                    for _ in range(int(steps)):
                        pred_y += pred_vy
                        if pred_y <= 0:
                            pred_y = -pred_y
                            pred_vy = -pred_vy
                        elif pred_y + BALL_SIZE >= SCREEN_HEIGHT:
                            pred_y = 2 * (SCREEN_HEIGHT - BALL_SIZE) - pred_y
                            pred_vy = -pred_vy
                    # error up to 50% of paddle height
                    error_range = int(PADDLE_HEIGHT * 0.8)
                    error = random.randint(-error_range, error_range)
                    # Store the target with the random error applied once per approach
                    self.ai_target_center_y = pred_y + BALL_SIZE // 2 + error
                    # Random response delay based on difficulty (up to 1 sec for Easy)
                    # Random response delay based on difficulty
                    if config.PONG_DIFFICULTY == config.DIFFICULTY_EASY:
                        max_delay = 1.0
                    elif config.PONG_DIFFICULTY == config.DIFFICULTY_MEDIUM:
                        max_delay = 0.5
                    else:
                        max_delay = 0.25
                    self.ai_delay_timer = random.uniform(0, max_delay)

                # Apply delay before moving
                if self.ai_delay_timer > 0:
                    self.ai_delay_timer -= dt
                if self.ai_delay_timer <= 0:
                    target_center_y = self.ai_target_center_y
                    if (
                        self.right_paddle.centery < target_center_y
                        and self.right_paddle.bottom < SCREEN_HEIGHT
                    ):
                        self.right_paddle.move_ip(0, AI_PADDLE_SPEED)
                    elif (
                        self.right_paddle.centery > target_center_y
                        and self.right_paddle.top > 0
                    ):
                        self.right_paddle.move_ip(0, -AI_PADDLE_SPEED)
            else:
                # Ball moving away – reset target and delay, simple tracking
                self.ai_target_center_y = None
                self.ai_delay_timer = 0.0
                if (
                    self.ball.centery < self.right_paddle.centery
                    and self.right_paddle.top > 0
                ):
                    self.right_paddle.move_ip(0, -AI_PADDLE_SPEED)
                elif (
                    self.ball.centery > self.right_paddle.centery
                    and self.right_paddle.bottom < SCREEN_HEIGHT
                ):
                    self.right_paddle.move_ip(0, AI_PADDLE_SPEED)
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
        """Render Pong UI."""
        screen.fill(BLACK)
        pygame.draw.rect(screen, WHITE, self.left_paddle)
        pygame.draw.rect(screen, WHITE, self.right_paddle)
        pygame.draw.ellipse(screen, GREEN, self.ball)
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
                f"{self.winner} wins!",
                FONT_SIZE,
                RED,
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2,
                center=True,
            )
        if self.paused:
            self.draw_pause_overlay(screen)
        self.draw_mute_overlay(screen)


class PongSinglePlayerState(PongState):
    """Single-player Pong (default AI)."""

    MULTIPLAYER = False

    @classmethod
    def get_controls(cls) -> List[str]:
        """Return control instructions for Pong single-player.

        Returns:
            List of control description strings.
        """
        return [
            "W/S or Up/Down: Move paddle",
            "R: Restart after game over",
            "ESC: Return to main menu",
        ]


class PongMultiplayerState(PongState):
    """Two-player Pong where both paddles are human-controlled."""

    MULTIPLAYER = True

    @classmethod
    def get_controls(cls) -> List[str]:
        """Return control instructions for Pong multiplayer.

        Returns:
            List of control description strings.
        """
        return [
            "W/S: Left paddle (Player 1)",
            "Up/Down: Right paddle (Player 2)",
            "R: Restart after game over",
            "ESC: Return to main menu",
        ]


def run() -> None:
    """Run Pong using the shared run helper."""
    from games.run_helper import run_game

    run_game(PongState)


if __name__ == "__main__":
    run()
