# games/snake.py
"""Simple Snake game implementation using Pygame.

Controls:
    Arrow keys - change direction of the snake.
    R - restart after game over.
    ESC - return to main menu.
"""

import logging
from typing import List, Tuple

import pygame

from engine import State

logger = logging.getLogger(__name__)
import logging
import math
import random
from datetime import datetime

import audio
import config
from config import (
    BLACK,
    BLUE,
    CYAN,
    FONT_SIZE_LARGE,
    FONT_SIZE_MEDIUM,
    FONT_SIZE_SMALL,
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
from engine import Engine
from games.game_base import Game
from games.highscore import add_score
from utils import draw_text

logger = logging.getLogger(__name__)
import logging

logger = logging.getLogger(__name__)

# Game constants
BLOCK_SIZE = 20
BASE_SNAKE_SPEED = 10  # frames per second (base)
# Determine snake speed based on difficulty setting (computed per game start)


def get_snake_speed() -> int:
    """Calculate snake speed based on the current difficulty.

    Uses the difficulty multiplier defined in ``config`` to compute the speed.
    Returns an integer FPS value.
    """
    multiplier = config.difficulty_multiplier(config.SNAKE_DIFFICULTY)
    return int(BASE_SNAKE_SPEED * multiplier)


class SnakeState(Game):
    """State for the Snake game, compatible with the engine loop."""

    def __init__(self) -> None:
        """Initialize Snake game state, setting up the snake, direction, food, and game variables."""
        super().__init__()
        # Compute snake speed based on current difficulty
        self.snake_speed = get_snake_speed()
        # Log game start with difficulty and speed
        logger.info(
            f"Snake game started: difficulty={config.SNAKE_DIFFICULTY}, speed={self.snake_speed}"
        )
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
        self.crash_played = False
        # High‑score tracking flags
        self.highscore_recorded = False
        self.highscores = []
        # Power-up state
        # List of powerups as dicts: {"type": str, "pos": (x,y), "ttl": float}
        self.powerups = []
        # Remaining seconds for active speed boost
        self._speed_boost_time = 0.0
        # Extra lives collected via powerups (start with 1 so player has at least one)
        self.extra_lives = 1
        # Store base speed so temporary boosts can be applied
        self._base_snake_speed = self.snake_speed
        self._time_acc = 0.0
        # Visual feedback timers for shrink power-up
        self._shrink_feedback_time = 0.0
        # flash timing: duration and remaining
        self._shrink_flash_duration = 0.6
        self._shrink_flash_remaining = 0.0
        # particle list for shrink effect
        self._particles = []

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
        # Immediate collection: if a power-up is currently under the head, collect it
        head_pos = self.snake[0]
        for pu in list(self.powerups):
            if pu.get("pos") == head_pos:
                try:
                    self._collect_powerup(pu)
                except Exception:
                    pass
                try:
                    self.powerups.remove(pu)
                except ValueError:
                    pass
        # Update power-up timers and remove expired powerups
        for pu in list(self.powerups):
            pu["ttl"] -= dt
            if pu["ttl"] <= 0:
                try:
                    self.powerups.remove(pu)
                except ValueError:
                    pass

        if self._speed_boost_time > 0:
            self._speed_boost_time = max(0.0, self._speed_boost_time - dt)
        if self._shrink_feedback_time > 0:
            self._shrink_feedback_time = max(0.0, self._shrink_feedback_time - dt)
        if self._shrink_flash_remaining > 0:
            self._shrink_flash_remaining = max(0.0, self._shrink_flash_remaining - dt)

        # update particles
        if self._particles:
            for p in list(self._particles):
                p["ttl"] -= dt
                if p["ttl"] <= 0:
                    try:
                        self._particles.remove(p)
                    except ValueError:
                        pass
                    continue
                # apply gravity and move particle (vel in pixels/sec)
                g = 200.0  # pixels/sec^2 downward gravity
                try:
                    # vel is mutable list now
                    p["vel"][1] += g * dt
                    p["pos"][0] += p["vel"][0] * dt
                    p["pos"][1] += p["vel"][1] * dt
                except Exception:
                    # fallback to tuple style
                    p["pos"] = (
                        p["pos"][0] + p["vel"][0] * dt,
                        p["pos"][1] + p["vel"][1] * dt,
                    )

        # Accumulate time and move snake at the effective speed
        self._time_acc += dt
        effective_speed = int(
            self._base_snake_speed * (2 if self._speed_boost_time > 0 else 1)
        )
        if effective_speed <= 0:
            effective_speed = 1
        self.snake_speed = effective_speed
        interval = 1.0 / self.snake_speed

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
                    # If player has an extra life, consume it and reset snake
                    if getattr(self, "extra_lives", 0) > 0:
                        self.extra_lives -= 1
                        logger.info("Extra life used to avoid wall collision")
                        self.snake = [(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)]
                        self.direction = (0, 0)
                        self.score = max(0, self.score - 1)
                        try:
                            audio.play_effect("snake", "crash.wav")
                        except Exception:
                            pass
                        break
                    self.game_over = True
                    logger.info(
                        f"Snake game over (wall collision). Score: {self.score}"
                    )
                    if not getattr(self, "crash_played", False):
                        self.crash_played = True
                        try:
                            audio.play_effect("snake", "crash.wav")
                        except Exception:
                            pass
                    break
                else:
                    self.snake.insert(0, new_head)
                    # Food collision
                    if new_head == self.food:
                        self.score += 1
                        # Play food-eat sound effect
                        try:
                            audio.play_effect("snake", "eat.wav")
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
                        # Small chance to spawn a power-up when food is eaten
                        try:
                            # Double frequency: 10% chance to spawn a power-up when food is eaten
                            if random.random() < 0.10:
                                self._spawn_powerup()
                        except Exception:
                            pass
                    else:
                        self.snake.pop()
                    # Power-up collision: check if new head landed on a powerup
            for pu in list(self.powerups):
                if new_head == pu.get("pos"):
                    try:
                        self._collect_powerup(pu)
                    except Exception:
                        pass
                    try:
                        self.powerups.remove(pu)
                    except ValueError:
                        pass
                    # Self collision
                    if new_head in self.snake[1:]:
                        # Self collision
                        if getattr(self, "extra_lives", 0) > 0:
                            self.extra_lives -= 1
                            logger.info("Extra life used to avoid self collision")
                            self.snake = [(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)]
                            self.direction = (0, 0)
                            self.score = max(0, self.score - 1)
                            try:
                                audio.play_effect("snake", "crash.wav")
                            except Exception:
                                pass
                            break
                        self.game_over = True
                        logger.info(
                            f"Snake game over (self collision). Score: {self.score}"
                        )
                        if not getattr(self, "crash_played", False):
                            self.crash_played = True
                            try:
                                audio.play_effect("snake", "crash.wav")
                            except Exception:
                                pass
                        break

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
        # Draw power-ups
        self._draw_powerups(screen)
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
        # Draw HUD: extra lives and speed boost remaining
        # Draw Unicode heart glyphs for lives if a suitable font is available.
        hearts = max(0, getattr(self, "extra_lives", 0))
        margin_right = 20
        heart_size = 20

        def _find_heart_font(sz: int):
            # Try a list of candidate fonts that often include the heart glyph
            candidates = [
                "DejaVu Sans",
                "Segoe UI Symbol",
                "Symbola",
                "Noto Color Emoji",
                "Arial Unicode MS",
                "Arial",
                "FreeSans",
            ]
            for name in candidates:
                try:
                    f = pygame.font.SysFont(name, sz)
                    m = f.metrics("♥")
                    if m and m[0] is not None:
                        return f
                except Exception:
                    continue
            # Last resort: use default font and hope for the glyph
            try:
                f = pygame.font.Font(None, sz)
                m = f.metrics("♥")
                if m and m[0] is not None:
                    return f
            except Exception:
                pass
            return None

        heart_font = _find_heart_font(heart_size)
        if heart_font:
            heart_surf = heart_font.render("♥", True, RED)
            w = heart_surf.get_width()
            padding = 4
            for i in range(hearts):
                x = SCREEN_WIDTH - margin_right - (i + 1) * (w + padding)
                y = 16
                screen.blit(heart_surf, (x, y))
        else:
            # Fallback: small red circle to indicate lives (better than prior polygon heart)
            spacing = 18
            size = 10
            cy = 16 + size // 2
            for i in range(hearts):
                cx = SCREEN_WIDTH - margin_right - (i * spacing) - size // 2
                try:
                    pygame.draw.circle(screen, RED, (cx, cy), size // 2)
                except Exception:
                    # ultimate fallback: draw text +N
                    draw_text(
                        screen,
                        f"+{hearts}",
                        FONT_SIZE_SMALL,
                        YELLOW,
                        SCREEN_WIDTH - margin_right - 40,
                        16,
                        center=False,
                    )
        # Visual feedback for shrink power-up: pulsing cyan overlay on the snake
        if getattr(self, "_shrink_flash_remaining", 0) > 0:
            dur = max(self._shrink_flash_duration, 0.001)
            elapsed = dur - self._shrink_flash_remaining
            frac = max(0.0, min(1.0, elapsed / dur))
            # two cycles of sine for a more noticeable pulse
            intensity = 0.5 * (1.0 + math.sin(frac * 2 * math.pi * 2))

            # blend GREEN -> CYAN based on intensity
            def _blend(c1, c2, t):
                return (
                    int(c1[0] + (c2[0] - c1[0]) * t),
                    int(c1[1] + (c2[1] - c1[1]) * t),
                    int(c1[2] + (c2[2] - c1[2]) * t),
                )

            seg_color = _blend(GREEN, CYAN, intensity)
            for segment in self.snake:
                pygame.draw.rect(screen, seg_color, (*segment, BLOCK_SIZE, BLOCK_SIZE))

        # Draw particles for shrink effect
        if self._particles:
            for p in list(self._particles):
                life = p.get("life", 1.0)
                ttl = max(0.0, p.get("ttl", 0.0))
                t = ttl / life if life > 0 else 0
                # size fades with ttl, alpha fades too
                radius = max(1, int(p.get("size", 3) * t))
                col = p.get("color", CYAN)
                alpha = int(255 * t)
                try:
                    # draw with per-pixel alpha surface for smooth fade
                    surf = pygame.Surface(
                        (radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA
                    )
                    pygame.draw.circle(
                        surf,
                        (col[0], col[1], col[2], alpha),
                        (radius + 1, radius + 1),
                        radius,
                    )
                    screen.blit(
                        surf,
                        (int(p["pos"][0] - radius - 1), int(p["pos"][1] - radius - 1)),
                    )
                except Exception:
                    try:
                        pygame.draw.circle(
                            screen, col, (int(p["pos"][0]), int(p["pos"][1])), radius
                        )
                    except Exception:
                        pass

        if getattr(self, "_speed_boost_time", 0) > 0:
            sb_text = f"Speed: {self._speed_boost_time:.1f}s"
            draw_text(
                screen,
                sb_text,
                FONT_SIZE_SMALL,
                MAGENTA,
                SCREEN_WIDTH - 120,
                44,
                center=False,
            )
        # Shrink feedback message
        if getattr(self, "_shrink_feedback_time", 0) > 0:
            draw_text(
                screen,
                "SHRUNK!",
                FONT_SIZE_SMALL,
                CYAN,
                SCREEN_WIDTH - 160,
                44,
                center=False,
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
                FONT_SIZE_MEDIUM,
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
                    FONT_SIZE_MEDIUM,
                    WHITE,
                    SCREEN_WIDTH // 2,
                    score_y,
                    center=True,
                )
            # Instruction line at bottom
            draw_text(
                screen,
                "Game Over! Press R to restart or ESC to menu",
                FONT_SIZE_MEDIUM,
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

    # --- Power-up helpers -------------------------------------------------
    def _spawn_powerup(self) -> None:
        """Spawn a random power-up at a free grid location.

        Power-up types: 'speed' (temporary double speed), 'shrink' (shorten snake by 3),
        'life' (extra life). Each power-up expires from the grid after 10 seconds.
        """
        types = ["speed", "shrink", "life"]
        pu_type = random.choice(types)
        # Find a free position
        for _ in range(100):
            pos = (
                random.randrange(0, SCREEN_WIDTH // BLOCK_SIZE) * BLOCK_SIZE,
                random.randrange(0, SCREEN_HEIGHT // BLOCK_SIZE) * BLOCK_SIZE,
            )
            if (
                pos not in self.snake
                and pos != self.food
                and pos not in [p["pos"] for p in self.powerups]
            ):
                self.powerups.append({"type": pu_type, "pos": pos, "ttl": 10.0})
                break

    def _collect_powerup(self, pu: dict) -> None:
        """Apply the effects of a collected power-up. Does not remove the pu from the list.

        Effects:
        - speed: double speed for 5 seconds
        - shrink: remove up to 3 tail segments and award +1 score
        - life: grant one extra life
        """
        t = pu.get("type")
        if t == "speed":
            self._speed_boost_time = max(self._speed_boost_time, 5.0)
        elif t == "shrink":
            # remove up to 3 segments but keep at least head
            remove_n = min(3, max(0, len(self.snake) - 1))
            for _ in range(remove_n):
                try:
                    self.snake.pop()
                except Exception:
                    break
            self.score += 1
            # Visual feedback: set timers so draw() can show cyan flash/message
            self._shrink_feedback_time = max(self._shrink_feedback_time, 1.5)
            # enable the flash/pulse by setting the remaining time
            self._shrink_flash_remaining = max(
                self._shrink_flash_remaining, self._shrink_flash_duration
            )
            # spawn particles at the head to give visual feedback
            try:
                head = self.snake[0]
                cx = int(head[0] + BLOCK_SIZE // 2)
                cy = int(head[1] + BLOCK_SIZE // 2)
                # spawn a burst of particles with variation
                for _ in range(20):
                    angle = random.random() * 2 * math.pi
                    speed = random.uniform(60, 180)  # pixels per second
                    vx = math.cos(angle) * speed
                    vy = math.sin(angle) * speed
                    ttl = random.uniform(0.6, 1.2)
                    size = random.randint(3, 6)
                    # slight color variation around CYAN
                    try:
                        base = CYAN
                        vr = min(255, max(0, base[0] + random.randint(-20, 20)))
                        vg = min(255, max(0, base[1] + random.randint(-20, 20)))
                        vb = min(255, max(0, base[2] + random.randint(-20, 20)))
                        color = (vr, vg, vb)
                    except Exception:
                        color = CYAN
                    # store vel as mutable list so we can apply gravity
                    self._particles.append(
                        {
                            "pos": [float(cx), float(cy)],
                            "vel": [float(vx), float(vy)],
                            "ttl": ttl,
                            "life": ttl,
                            "size": size,
                            "color": color,
                        }
                    )
            except Exception:
                pass
            # play shrink sound if available
            try:
                audio.play_effect("snake", "shrink.wav")
            except Exception:
                pass
        elif t == "life":
            self.extra_lives = getattr(self, "extra_lives", 0) + 1

    # Draw power-ups on screen just above draw
    def _draw_powerups(self, screen: pygame.Surface) -> None:
        for pu in self.powerups:
            color = BLUE
            if pu.get("type") == "speed":
                color = MAGENTA
            elif pu.get("type") == "shrink":
                # CYAN is defined in config and re-exported; fall back to MAGENTA
                from config import CYAN

                color = CYAN
            elif pu.get("type") == "life":
                color = YELLOW
            pygame.draw.rect(screen, color, (*pu.get("pos"), BLOCK_SIZE, BLOCK_SIZE))

    @classmethod
    def get_controls(cls) -> List[str]:
        """Return control instructions for Snake.

        Returns:
            List of control description strings.
        """
        return [
            "Arrow keys: Change direction",
            "R: Restart after game over",
            "ESC: Return to main menu",
        ]


# Run function removed; use package-level run()


class Snake2PlayerState(Game):
    """Two-player Snake game with split-screen.

    Player 1 uses arrow keys, Player 2 uses WASD keys.
    Each player has their own grid on half the screen.
    """

    def __init__(self) -> None:
        """Initialize 2-player Snake game state."""
        super().__init__()
        self.snake_speed = get_snake_speed()
        logger.info(
            f"2-Player Snake game started: difficulty={config.SNAKE_DIFFICULTY}, speed={self.snake_speed}"
        )

        # Player 1 (left side, arrow keys)
        self.snake1 = [(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2)]
        self.direction1 = (0, 0)
        self.score1 = 0
        self.game_over1 = False
        self.food1 = (
            random.randrange(0, SCREEN_WIDTH // 2 // BLOCK_SIZE) * BLOCK_SIZE,
            random.randrange(0, SCREEN_HEIGHT // BLOCK_SIZE) * BLOCK_SIZE,
        )

        # Player 2 (right side, WASD keys)
        self.snake2 = [(SCREEN_WIDTH * 3 // 4, SCREEN_HEIGHT // 2)]
        self.direction2 = (0, 0)
        self.score2 = 0
        self.game_over2 = False
        self.food2 = (
            random.randrange(SCREEN_WIDTH // 2, SCREEN_WIDTH // BLOCK_SIZE)
            * BLOCK_SIZE,
            random.randrange(0, SCREEN_HEIGHT // BLOCK_SIZE) * BLOCK_SIZE,
        )

        self.font_size = 24
        self.highscore_recorded = False
        self.highscores = []

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle key events for 2-player Snake.

        Player 1 (left): Arrow keys
        Player 2 (right): WASD keys
        """
        if event.type == pygame.KEYDOWN:
            if not self.game_over1:
                # Player 1 controls (arrow keys)
                if event.key == KEY_UP:
                    if self.direction1 != (0, BLOCK_SIZE):
                        self.direction1 = (0, -BLOCK_SIZE)
                elif event.key == KEY_DOWN:
                    if self.direction1 != (0, -BLOCK_SIZE):
                        self.direction1 = (0, BLOCK_SIZE)
                elif event.key == KEY_LEFT:
                    if self.direction1 != (BLOCK_SIZE, 0):
                        self.direction1 = (-BLOCK_SIZE, 0)
                elif event.key == KEY_RIGHT:
                    if self.direction1 != (-BLOCK_SIZE, 0):
                        self.direction1 = (BLOCK_SIZE, 0)

            if not self.game_over2:
                # Player 2 controls (WASD)
                if event.key == pygame.K_w:
                    if self.direction2 != (0, BLOCK_SIZE):
                        self.direction2 = (0, -BLOCK_SIZE)
                elif event.key == pygame.K_s:
                    if self.direction2 != (0, -BLOCK_SIZE):
                        self.direction2 = (0, BLOCK_SIZE)
                elif event.key == pygame.K_a:
                    if self.direction2 != (BLOCK_SIZE, 0):
                        self.direction2 = (-BLOCK_SIZE, 0)
                elif event.key == pygame.K_d:
                    if self.direction2 != (-BLOCK_SIZE, 0):
                        self.direction2 = (BLOCK_SIZE, 0)

        # Delegate remaining keys (ESC, P, R) to base class
        super().handle_event(event)

    def update(self, dt: float) -> None:
        """Update the 2-player Snake game state."""
        if self.game_over1 and self.game_over2:
            return

        # Update both snakes
        self._update_snake(
            self.snake1, self.direction1, self.food1, self.score1, self.game_over1, 1
        )
        self._update_snake(
            self.snake2, self.direction2, self.food2, self.score2, self.game_over2, 2
        )

        # Check if both players are game over
        if self.game_over1 and self.game_over2:
            self.game_over = True

    def _update_snake(
        self,
        snake: List[Tuple[int, int]],
        direction: Tuple[int, int],
        food: Tuple[int, int],
        score: int,
        game_over: bool,
        player_num: int,
    ) -> None:
        """Update a single snake's position and check collisions."""
        if game_over or self.paused:
            return

        if direction == (0, 0):
            return

        new_head = (snake[0][0] + direction[0], snake[0][1] + direction[1])

        # Determine bounds based on player
        if player_num == 1:
            max_x = SCREEN_WIDTH // 2
        else:
            min_x = SCREEN_WIDTH // 2
            max_x = SCREEN_WIDTH

        # Check wall collision
        if player_num == 1:
            if (
                new_head[0] < 0
                or new_head[0] >= SCREEN_WIDTH // 2
                or new_head[1] < 0
                or new_head[1] >= SCREEN_HEIGHT
            ):
                self.game_over1 = True
                logger.info(f"Player 1 game over (wall collision). Score: {score}")
                return
        else:
            if (
                new_head[0] < SCREEN_WIDTH // 2
                or new_head[0] >= SCREEN_WIDTH
                or new_head[1] < 0
                or new_head[1] >= SCREEN_HEIGHT
            ):
                self.game_over2 = True
                logger.info(f"Player 2 game over (wall collision). Score: {score}")
                return

        # Check self collision
        if new_head in snake[1:]:
            if player_num == 1:
                self.game_over1 = True
                logger.info(f"Player 1 game over (self collision). Score: {score}")
            else:
                self.game_over2 = True
                logger.info(f"Player 2 game over (self collision). Score: {score}")
            return

        # Check collision with other player's snake
        other_snake = self.snake2 if player_num == 1 else self.snake1
        if new_head in other_snake:
            if player_num == 1:
                self.game_over1 = True
                logger.info(
                    f"Player 1 game over (collision with Player 2). Score: {score}"
                )
            else:
                self.game_over2 = True
                logger.info(
                    f"Player 2 game over (collision with Player 1). Score: {score}"
                )
            return

        # Move snake
        snake.insert(0, new_head)

        # Food collision
        if new_head == food:
            if player_num == 1:
                self.score1 += 1
                # Place new food in player 1's half
                while True:
                    self.food1 = (
                        random.randrange(0, SCREEN_WIDTH // 2 // BLOCK_SIZE)
                        * BLOCK_SIZE,
                        random.randrange(0, SCREEN_HEIGHT // BLOCK_SIZE) * BLOCK_SIZE,
                    )
                    if self.food1 not in self.snake1 and self.food1 not in self.snake2:
                        break
            else:
                self.score2 += 1
                # Place new food in player 2's half
                while True:
                    self.food2 = (
                        random.randrange(SCREEN_WIDTH // 2, SCREEN_WIDTH // BLOCK_SIZE)
                        * BLOCK_SIZE,
                        random.randrange(0, SCREEN_HEIGHT // BLOCK_SIZE) * BLOCK_SIZE,
                    )
                    if self.food2 not in self.snake2 and self.food2 not in self.snake1:
                        break
        else:
            snake.pop()

    def draw(self, screen: pygame.Surface) -> None:
        """Render the 2-player Snake game with split screen."""
        # Draw center divider line
        pygame.draw.line(
            screen, WHITE, (SCREEN_WIDTH // 2, 0), (SCREEN_WIDTH // 2, SCREEN_HEIGHT), 2
        )

        # Draw Player 1 (left side)
        screen.fill(BLACK, (0, 0, SCREEN_WIDTH // 2, SCREEN_HEIGHT))
        pygame.draw.rect(screen, GREEN, (*self.snake1[0], BLOCK_SIZE, BLOCK_SIZE))
        for segment in self.snake1[1:]:
            pygame.draw.rect(screen, (0, 200, 0), (*segment, BLOCK_SIZE, BLOCK_SIZE))
        pygame.draw.rect(screen, RED, (*self.food1, BLOCK_SIZE, BLOCK_SIZE))
        draw_text(
            screen,
            f"P1 Score: {self.score1}",
            FONT_SIZE_MEDIUM,
            GREEN,
            SCREEN_WIDTH // 4,
            20,
            center=True,
        )

        # Draw Player 2 (right side)
        screen.fill(BLACK, (SCREEN_WIDTH // 2, 0, SCREEN_WIDTH // 2, SCREEN_HEIGHT))
        pygame.draw.rect(screen, BLUE, (*self.snake2[0], BLOCK_SIZE, BLOCK_SIZE))
        for segment in self.snake2[1:]:
            pygame.draw.rect(screen, (0, 0, 200), (*segment, BLOCK_SIZE, BLOCK_SIZE))
        pygame.draw.rect(screen, MAGENTA, (*self.food2, BLOCK_SIZE, BLOCK_SIZE))
        draw_text(
            screen,
            f"P2 Score: {self.score2}",
            FONT_SIZE_MEDIUM,
            BLUE,
            SCREEN_WIDTH * 3 // 4,
            20,
            center=True,
        )

        # Draw game over screen
        if self.game_over1 and self.game_over2:
            if not getattr(self, "highscore_recorded", False):
                self.highscores = add_score("snake", max(self.score1, self.score2))
                self.highscore_recorded = True

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

    @classmethod
    def get_controls(cls) -> List[str]:
        """Return control instructions for 2-player Snake.

        Returns:
            List of control description strings.
        """
        return [
            "Player 1: Arrow keys to move",
            "Player 2: WASD keys to move",
            "R: Restart after game over",
            "ESC: Return to main menu",
        ]


class SnakeModeSelectState(State):
    """Mode selection screen for Snake game.

    Allows the player to choose between single-player and 2-player modes.
    """

    def __init__(self) -> None:
        """Initialize the mode selection screen."""
        super().__init__()
        self.options = ["Single Player", "2 Player (Split Screen)"]
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
                    from games.snake import SnakeState

                    self.request_transition(SnakeState())
                elif self.selected == 1:
                    from games.snake import Snake2PlayerState

                    self.request_transition(Snake2PlayerState())
            elif event.key == pygame.K_ESCAPE:
                from engine import MenuState

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
            "Select Snake Mode",
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


def run() -> None:
    """Run Snake using the shared run helper."""
    from games.run_helper import run_game

    run_game(SnakeModeSelectState)
