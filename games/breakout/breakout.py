# games/breakout.py
"""Simple Breakout game implementation using Pygame.

Controls:
    Left/Right arrow keys - move the paddle.
    R - restart after game over.
    ESC - return to main menu.
"""

import logging
import random
from datetime import datetime
from typing import List, Tuple

import pygame

from classic_arcade import audio, config
from classic_arcade.config import (
    BLACK,
    BLUE,
    CYAN,
    FONT_SIZE_MEDIUM,
    FONT_SIZE_SMALL,
    GREEN,
    KEY_LEFT,
    KEY_RIGHT,
    MAGENTA,
    RED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WHITE,
    YELLOW,
)
from classic_arcade.constants import COUNTDOWN_SECONDS
from classic_arcade.difficulty import (
    apply_difficulty_divisor,
    apply_difficulty_multiplier,
)
from classic_arcade.utils import draw_text
from games.game_base import Game
from games.highscore import draw_highscore_screen, record_highscore

logger = logging.getLogger(__name__)

# Game constants
PADDLE_WIDTH = 100
PADDLE_HEIGHT = 10
BALL_RADIUS = 8

# Base speed values
BASE_PADDLE_SPEED = 6
BASE_BALL_SPEED = 5
BASE_BRICK_ROWS = 5

PADDLE_SPEED = apply_difficulty_multiplier(BASE_PADDLE_SPEED, "breakout")
BALL_SPEED = apply_difficulty_multiplier(BASE_BALL_SPEED, "breakout")
BRICK_ROWS = apply_difficulty_multiplier(BASE_BRICK_ROWS, "breakout")
BRICK_COLS = 10
BRICK_WIDTH = (SCREEN_WIDTH - (BRICK_COLS + 1) * 5) // BRICK_COLS
BRICK_HEIGHT = 20
BRICK_SPACING = 5
FONT_SIZE = 24

# Power-up configuration
POWERUP_SPAWN_CHANCE = 0.2
POWERUP_DURATION = 5.0
PADDLE_EXPANSION = 50
# COUNTDOWN_SECONDS moved to classic_arcade.constants
POWERUP_TYPES = ["expand_paddle", "multiball", "slow_ball"]
POWERUP_SIZE = 18
# Visual cue colour for cracked bricks
CRACK_COLOR = (220, 220, 220)


# Apply difficulty‑based speed settings for Breakout
def _apply_breakout_speed_settings() -> None:
    """Set global speed and brick variables based on the current Breakout difficulty."""
    global PADDLE_SPEED, BALL_SPEED, BRICK_ROWS
    if config.BREAKOUT_DIFFICULTY == config.DIFFICULTY_EASY:
        PADDLE_SPEED = apply_difficulty_multiplier(BASE_PADDLE_SPEED, "breakout")
        BALL_SPEED = apply_difficulty_multiplier(BASE_BALL_SPEED, "breakout")
        BRICK_ROWS = apply_difficulty_multiplier(BASE_BRICK_ROWS, "breakout")
    elif config.BREAKOUT_DIFFICULTY == config.DIFFICULTY_MEDIUM:
        PADDLE_SPEED = apply_difficulty_multiplier(
            BASE_PADDLE_SPEED, "breakout", custom_multiplier=1.2
        )
        BALL_SPEED = apply_difficulty_multiplier(
            BASE_BALL_SPEED, "breakout", custom_multiplier=1.5
        )
        BRICK_ROWS = apply_difficulty_multiplier(
            BASE_BRICK_ROWS, "breakout", custom_multiplier=1.2
        )
    else:
        PADDLE_SPEED = apply_difficulty_multiplier(
            BASE_PADDLE_SPEED, "breakout", custom_multiplier=1.5
        )
        BALL_SPEED = apply_difficulty_multiplier(
            BASE_BALL_SPEED, "breakout", custom_multiplier=2
        )
        BRICK_ROWS = apply_difficulty_multiplier(
            BASE_BRICK_ROWS, "breakout", custom_multiplier=1.5
        )


class BreakoutState(Game):
    """State for the Breakout game, compatible with the engine loop."""

    def __init__(self) -> None:
        """Initialize Breakout game state, setting up paddle, ball, bricks, and scores."""
        super().__init__()
        # Apply difficulty‑based speed settings
        _apply_breakout_speed_settings()
        logger.info(
            f"Breakout game started: difficulty={config.BREAKOUT_DIFFICULTY}, paddle_speed={PADDLE_SPEED}, ball_speed={BALL_SPEED}, brick_rows={BRICK_ROWS}"
        )
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
        # Bricks are a list of (rect, color). Hit points are stored in
        # a parallel list `brick_hps` to preserve the original public API
        # where tests expect tuples of two values.
        self.bricks = create_bricks()
        # Parallel list of hit points (1 or 2) matching indices in self.bricks
        self.brick_hps: List[int] = [
            2 if col == MAGENTA else 1 for _, col in self.bricks
        ]
        # Keep a copy of initial HPs so we can show a "cracked" indicator
        # when a strong brick loses one hit (2 -> 1).
        self.brick_initial_hps = list(self.brick_hps)
        self.score = 0
        self.game_over = False
        self.win = False
        # High‑score tracking flags
        self.highscore_recorded = False
        self.highscores = []
        # Power‑up management
        # falling powerups: dicts {type, rect, speed}
        self.powerups = []
        # active timed effects: mapping -> remaining seconds
        self.active_powerups = {}
        # extra balls list used when multiball is active
        self.extra_balls = []

    # -------------------------
    # Power-up helpers
    # -------------------------
    def _spawn_powerup(self, x: int, y: int) -> None:
        """Spawn a falling power-up at (x, y)."""
        pu_type = random.choice(POWERUP_TYPES)
        rect = pygame.Rect(
            x - POWERUP_SIZE // 2, y - POWERUP_SIZE // 2, POWERUP_SIZE, POWERUP_SIZE
        )
        self.powerups.append({"type": pu_type, "rect": rect, "speed": 3})

    def _apply_powerup(self, pu_type: str) -> None:
        """Apply the collected power-up effect."""
        if pu_type == "expand_paddle":
            self.paddle.width = PADDLE_WIDTH + PADDLE_EXPANSION
            self.active_powerups["expand_paddle"] = POWERUP_DURATION
        elif pu_type == "multiball":
            # spawn two extra balls
            for _ in range(2):
                new_rect = pygame.Rect(
                    self.paddle.centerx - BALL_RADIUS,
                    self.paddle.top - 2 * BALL_RADIUS,
                    BALL_RADIUS * 2,
                    BALL_RADIUS * 2,
                )
                new_vel = [random.choice([-BALL_SPEED, BALL_SPEED]), -BALL_SPEED]
                self.extra_balls.append((new_rect, new_vel))
        elif pu_type == "slow_ball":
            # activate slow-ball effect (temporary speed reduction)
            self.active_powerups["slow_ball"] = POWERUP_DURATION

    def update(self, dt: float) -> None:
        """Update the game state: handle paddle movement, ball physics, collisions, scoring, and win/lose conditions."""
        if self.game_over or self.paused:
            return
        # Handle countdown
        if self.countdown_active:
            self.countdown_remaining -= dt
            if self.countdown_remaining <= 0:
                # Start new level
                self.__init__()
            return
        keys = pygame.key.get_pressed()
        # Paddle movement
        if keys[KEY_LEFT] and self.paddle.left > 0:
            self.paddle.move_ip(-PADDLE_SPEED, 0)
        if keys[KEY_RIGHT] and self.paddle.right < SCREEN_WIDTH:
            self.paddle.move_ip(PADDLE_SPEED, 0)
        # Ball movement (handle main ball and any extra balls)
        # Determine speed factor for slow-ball effect
        speed_factor = 0.5 if "slow_ball" in self.active_powerups else 1.0
        all_balls = [
            (self.ball, self.ball_vel),
        ] + [(b[0], b[1]) for b in self.extra_balls]

        for ball_rect, vel in all_balls:
            # Apply speed factor when moving the ball
            move_x = int(vel[0] * speed_factor)
            move_y = int(vel[1] * speed_factor)
            ball_rect.move_ip(move_x, move_y)
            # Collisions with walls
            if ball_rect.left <= 0 or ball_rect.right >= SCREEN_WIDTH:
                vel[0] = -vel[0]
            if ball_rect.top <= 0:
                vel[1] = -vel[1]
            # Collision with paddle (only if ball moving downwards)
            if ball_rect.colliderect(self.paddle) and vel[1] > 0:
                vel[1] = -vel[1]
                offset = (ball_rect.centerx - self.paddle.centerx) / (
                    self.paddle.width / 2
                )
                vel[0] = int(BALL_SPEED * offset)
                try:
                    audio.play_effect("breakout", "bounce.wav")
                except Exception:
                    pass
            # Collision with bricks — bricks now carry hit points
            if not self.bricks:
                continue
            hit_index = ball_rect.collidelist([br[0] for br in self.bricks])
            if hit_index != -1:
                brick_rect, brick_color = self.bricks[hit_index]
                hp = self.brick_hps[hit_index]
                # Reduce hit points or destroy
                if hp > 1:
                    hp -= 1
                    self.brick_hps[hit_index] = hp
                    # Optionally change colour to indicate damage; keep MAGENTA for strong bricks
                    self.bricks[hit_index] = (brick_rect, MAGENTA)
                else:
                    # destroyed: remove both lists' entries
                    self.bricks.pop(hit_index)
                    self.brick_hps.pop(hit_index)
                    self.brick_initial_hps.pop(hit_index)
                    self.score += 1
                    # chance to drop a powerup
                    if random.random() < POWERUP_SPAWN_CHANCE:
                        self._spawn_powerup(brick_rect.centerx, brick_rect.centery)
                # bounce the ball vertically
                vel[1] = -vel[1]
                try:
                    audio.play_effect("breakout", "brick.wav")
                except Exception:
                    pass
        # Update active power‑up timers (expand paddle and slow ball)
        for power in list(self.active_powerups.keys()):
            self.active_powerups[power] -= dt
            if self.active_powerups[power] <= 0:
                if power == "expand_paddle":
                    # Revert paddle width to original
                    self.paddle.width = PADDLE_WIDTH
                # Remove the expired power‑up
                del self.active_powerups[power]
        # Move falling power‑ups and check collection
        for pu in self.powerups[:]:
            pu_rect = pu["rect"]
            pu_rect.move_ip(0, pu["speed"])
            if pu_rect.top > SCREEN_HEIGHT:
                self.powerups.remove(pu)
                continue
            if pu_rect.colliderect(self.paddle):
                self._apply_powerup(pu["type"])
                self.powerups.remove(pu)

        # Check win
        if not self.bricks:
            self.win = True
        # Handle level transition countdown
        if self.win and not self.countdown_active:
            self.countdown_active = True
            self.countdown_remaining = COUNTDOWN_SECONDS
        # Check lose: game over only when all balls are lost
        # Remove any extra balls that have fallen below the screen
        self.extra_balls = [
            (rect, vel) for rect, vel in self.extra_balls if rect.bottom < SCREEN_HEIGHT
        ]
        if self.ball.bottom >= SCREEN_HEIGHT:
            if self.extra_balls:
                # Promote the first extra ball to become the main ball
                new_rect, new_vel = self.extra_balls.pop(0)
                self.ball = new_rect
                self.ball_vel = new_vel
            else:
                self.game_over = True

    def _draw_background(self, screen: pygame.Surface) -> None:
        """Draw the background (black fill)."""
        screen.fill(BLACK)

    def _draw_paddle(self, screen: pygame.Surface) -> None:
        """Draw the paddle (white rectangle)."""
        pygame.draw.rect(screen, WHITE, self.paddle)

    def _draw_balls(self, screen: pygame.Surface) -> None:
        """Draw the main ball and extra balls (green ellipses)."""
        pygame.draw.ellipse(screen, GREEN, self.ball)
        for ball_rect, _ in self.extra_balls:
            pygame.draw.ellipse(screen, GREEN, ball_rect)

    def _draw_bricks(self, screen: pygame.Surface) -> None:
        """Draw bricks with HP-aware rendering (crack overlay for damaged bricks)."""
        for idx, (rect, color) in enumerate(self.bricks):
            pygame.draw.rect(screen, color, rect)
            try:
                initial = self.brick_initial_hps[idx]
                current = self.brick_hps[idx]
            except Exception:
                initial = 1
                current = 1
            if initial == 2 and current == 1:
                x1, y1 = rect.left + 4, rect.top + 4
                x2, y2 = rect.right - 4, rect.bottom - 4
                pygame.draw.line(screen, CRACK_COLOR, (x1, y1), (x2, y2), 2)
                pygame.draw.line(screen, CRACK_COLOR, (x1, y2), (x2, y1), 2)

    def _draw_powerups(self, screen: pygame.Surface) -> None:
        """Draw falling power-ups with type-specific colors (expand_paddle=YELLOW, multiball=CYAN, slow_ball=MAGENTA)."""
        for pu in self.powerups:
            pu_rect = pu["rect"]
            pu_type = pu["type"]
            if pu_type == "expand_paddle":
                pu_color = YELLOW
            elif pu_type == "multiball":
                pu_color = CYAN
            else:
                pu_color = MAGENTA
            pygame.draw.rect(screen, pu_color, pu_rect)

    def _draw_score(self, screen: pygame.Surface) -> None:
        """Draw the current score text."""
        draw_text(
            screen,
            f"Score: {self.score}",
            FONT_SIZE_MEDIUM,
            WHITE,
            60,
            20,
            center=False,
        )

    def _draw_game_over(self, screen: pygame.Surface) -> None:
        """Draw the game-over screen with high score if game is over."""
        if self.game_over:
            record_highscore(self, "breakout", self.score)
            draw_highscore_screen(
                screen,
                self.highscores,
                instruction_text="Game Over! Press R to restart or ESC to menu",
                instruction_color=RED,
                font_size=FONT_SIZE_MEDIUM,
            )

    def _draw_win_countdown(self, screen: pygame.Surface) -> None:
        """Draw the countdown or win message when all bricks are cleared."""
        if self.countdown_active:
            self.draw_countdown(screen)
        elif self.win:
            draw_text(
                screen,
                "You Win! Starting next level...",
                FONT_SIZE_MEDIUM,
                YELLOW,
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2,
                center=True,
            )

    def _draw_pause_mute_overlays(self, screen: pygame.Surface) -> None:
        """Draw the pause and mute status overlays."""
        if self.paused:
            self.draw_pause_overlay(screen)
        self.draw_mute_overlay(screen)

    def draw(self, screen: pygame.Surface) -> None:
        """Render the breakout game elements and UI onto the screen."""
        self._draw_background(screen)
        self._draw_paddle(screen)
        self._draw_balls(screen)
        self._draw_bricks(screen)
        self._draw_powerups(screen)
        self._draw_score(screen)
        self._draw_game_over(screen)
        self._draw_win_countdown(screen)
        self._draw_pause_mute_overlays(screen)

    @classmethod
    def get_controls(cls) -> List[str]:
        """Return control instructions for Breakout.

        Returns:
            List of control description strings.
        """
        return [
            "Left/Right: Move paddle",
            "R: Restart after game over",
            "ESC: Return to main menu",
        ]


def create_bricks() -> List[Tuple[pygame.Rect, Tuple[int, int, int]]]:
    """Create and return a list of brick (rect, color) tuples.

    Strong bricks are coloured MAGENTA and will be represented in the
    parallel `brick_hps` list on the BreakoutState instance.
    """
    bricks: List[Tuple[pygame.Rect, Tuple[int, int, int]]] = []
    colors = [RED, GREEN, BLUE, YELLOW, CYAN]
    for row in range(BRICK_ROWS):
        for col in range(BRICK_COLS):
            x = BRICK_SPACING + col * (BRICK_WIDTH + BRICK_SPACING)
            y = BRICK_SPACING + row * (BRICK_HEIGHT + BRICK_SPACING) + 50
            rect = pygame.Rect(x, y, BRICK_WIDTH, BRICK_HEIGHT)
            if random.random() < 0.2:
                color = MAGENTA
            else:
                color = colors[row % len(colors)]
            bricks.append((rect, color))
    return bricks


def run() -> None:
    """Run Breakout using the shared run helper."""
    from games.run_helper import run_game

    run_game(BreakoutState)


if __name__ == "__main__":
    run()
