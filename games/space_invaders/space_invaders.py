# games/space_invaders.py
"""Simple Space Invaders game implementation using Pygame.

Controls:
    Left/Right arrow keys - move the spaceship.
    Space - fire a bullet.
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
    KEY_LEFT,
    KEY_RIGHT,
)
from utils import draw_text
from datetime import datetime
from games.highscore import add_score

from typing import List, Tuple
from games.game_base import Game

# Game constants
PLAYER_WIDTH = 50
PLAYER_HEIGHT = 30
PLAYER_SPEED = 5  # pixels per frame
BULLET_WIDTH = 4
BULLET_HEIGHT = 10
BULLET_SPEED = 7
ALIEN_ROWS = 4
ALIEN_COLS = 8
ALIEN_WIDTH = 40
ALIEN_HEIGHT = 30
ALIEN_H_SPACING = 10
ALIEN_V_SPACING = 10
ALIEN_SPEED = 1  # horizontal speed per frame
ALIEN_DESCEND = 20
FONT_SIZE = 24

# Configurable constants
PLAYER_SHOOT_COOLDOWN = 0.5  # seconds between player shots
# Bomb shelter constants
SHELTER_WIDTH = 80
SHELTER_HEIGHT = 30
SHELTER_SPACING = 50
SHELTER_COLOR = BLUE
NUM_SHELTERS = 3
# Shelter block layout (0 = empty, 1 = block)
SHELTER_SHAPE = [
    [0, 1, 0],
    [1, 1, 1],
    [1, 0, 1],
]
SHELTER_BLOCK_WIDTH = SHELTER_WIDTH // 3
SHELTER_BLOCK_HEIGHT = SHELTER_HEIGHT // 3


class SpaceInvadersState(Game):
    """Game class for Space Invaders, inherits from ``Game`` and compatible with the engine loop."""

    def __init__(self) -> None:
        """Initialize the Space Invaders game state, setting up player, aliens, shelters, and game variables."""
        super().__init__()
        # Player ship
        self.player = pygame.Rect(
            (SCREEN_WIDTH - PLAYER_WIDTH) // 2,
            SCREEN_HEIGHT - PLAYER_HEIGHT - 30,
            PLAYER_WIDTH,
            PLAYER_HEIGHT,
        )
        self.bullets: List[pygame.Rect] = []
        self.enemy_bullets: List[pygame.Rect] = []
        self.enemy_shoot_cooldown = 2.0  # seconds
        self.player_shoot_cooldown = 0.0  # seconds
        self.aliens = create_aliens()
        self.shelters = create_shelters()
        self.alien_direction = 1
        self.score = 0
        self.game_over = False
        # High‑score tracking flags
        self.highscore_recorded = False
        self.highscores = []
        self.win = False

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle events specific to Space Invaders, delegating common keys to the base class."""
        # Let Game base handle ESC, pause, restart
        super().handle_event(event)
        # No additional handling needed for Space Invaders

    def update(self, dt: float) -> None:
        """Update the game state, handling player movement, shooting, alien behavior, and collisions."""
        if self.game_over or self.win or self.paused:
            return
        keys = pygame.key.get_pressed()

        # Player movement
        def is_pressed(key: int) -> bool:
            try:
                return keys[key]
            except (IndexError, TypeError):
                # keys may be a list/tuple or a dict-like object
                if isinstance(keys, dict):
                    return keys.get(key, False)
                return False

        if is_pressed(KEY_LEFT) and self.player.left > 0:
            self.player.move_ip(-PLAYER_SPEED, 0)
        if is_pressed(KEY_RIGHT) and self.player.right < SCREEN_WIDTH:
            self.player.move_ip(PLAYER_SPEED, 0)
        # Move player bullets
        for bullet in self.bullets[:]:
            bullet.move_ip(0, -BULLET_SPEED)
            if bullet.bottom < 0:
                self.bullets.remove(bullet)
        # Move enemy bullets
        for bullet in self.enemy_bullets[:]:
            bullet.move_ip(0, BULLET_SPEED)
            if bullet.top > SCREEN_HEIGHT:
                self.enemy_bullets.remove(bullet)
        # Enemy shooting timer
        self.enemy_shoot_cooldown -= dt
        # Player shooting cooldown timer
        self.player_shoot_cooldown -= dt
        if self.enemy_shoot_cooldown <= 0 and self.aliens:
            alien_rect, _ = random.choice(self.aliens)
            enemy_bullet = pygame.Rect(
                alien_rect.centerx - BULLET_WIDTH // 2,
                alien_rect.bottom,
                BULLET_WIDTH,
                BULLET_HEIGHT,
            )
            self.enemy_bullets.append(enemy_bullet)
            self.enemy_shoot_cooldown = random.uniform(1.0, 3.0)
        # Player shooting (with configurable cooldown)
        if is_pressed(pygame.K_SPACE) and self.player_shoot_cooldown <= 0:
            bullet = pygame.Rect(
                self.player.centerx - BULLET_WIDTH // 2,
                self.player.top - BULLET_HEIGHT,
                BULLET_WIDTH,
                BULLET_HEIGHT,
            )
            self.bullets.append(bullet)
            self.player_shoot_cooldown = PLAYER_SHOOT_COOLDOWN
        # Move aliens horizontally
        move_down = False
        for rect, color in self.aliens:
            rect.move_ip(ALIEN_SPEED * self.alien_direction, 0)
            if rect.right >= SCREEN_WIDTH or rect.left <= 0:
                move_down = True
        if move_down:
            self.alien_direction *= -1
            for rect, color in self.aliens:
                rect.move_ip(0, ALIEN_DESCEND)
        # Bullet-alien collisions (player bullets vs aliens)
        for bullet in self.bullets[:]:
            hit_index = bullet.collidelist([a[0] for a in self.aliens])
            if hit_index != -1:
                # Destroy alien and the bullet
                self.aliens.pop(hit_index)
                self.bullets.remove(bullet)
                self.score += 10
                continue
            # Player bullet vs shelter blocks
            shelter_hit = bullet.collidelist(self.shelters)
            if shelter_hit != -1:
                # Destroy the shelter block and the bullet
                self.shelters.pop(shelter_hit)
                self.bullets.remove(bullet)
                # No score change – shelters are neutral objects
                continue
        # Enemy bullet-player collisions (with shelter blocks)
        for bullet in self.enemy_bullets[:]:
            # Check collision with shelter blocks first
            hit_idx = bullet.collidelist(self.shelters)
            if hit_idx != -1:
                # Bullet hits a shelter block, remove the block and the bullet
                self.shelters.pop(hit_idx)
                self.enemy_bullets.remove(bullet)
                continue
            if bullet.colliderect(self.player):
                # Player hit (no shelter block protecting)
                self.game_over = True
                self.enemy_bullets.remove(bullet)
                break
        # Check win
        if not self.aliens:
            self.win = True
        # Check lose
        for rect, _ in self.aliens:
            if rect.bottom >= self.player.top:
                self.game_over = True
                break

    def draw(self, screen: pygame.Surface) -> None:
        """Render the game objects (player, aliens, bullets, shelters) and UI onto the screen."""
        screen.fill(BLACK)
        # Draw player
        pygame.draw.rect(screen, WHITE, self.player)
        # Draw bullets
        for bullet in self.bullets:
            pygame.draw.rect(screen, YELLOW, bullet)
        # Draw enemy bullets
        for bullet in self.enemy_bullets:
            pygame.draw.rect(screen, RED, bullet)
        # Draw aliens
        for rect, color in self.aliens:
            pygame.draw.rect(screen, color, rect)
        # Draw shelters
        for shelter in self.shelters:
            pygame.draw.rect(screen, SHELTER_COLOR, shelter)
        # Draw score
        draw_text(
            screen, f"Score: {self.score}", FONT_SIZE, WHITE, 60, 20, center=False
        )
        if self.game_over:
            # Record high score once (score is stored in self.score)
            if not getattr(self, "highscore_recorded", False):
                self.highscores = add_score("space_invaders", self.score)
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
        if self.win:
            draw_text(
                screen,
                "You Win! Press R to restart or ESC to menu",
                FONT_SIZE,
                GREEN,
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2,
                center=True,
            )
        # Draw pause overlay if paused
        if self.paused:
            self.draw_pause_overlay(screen)


def create_aliens() -> List[Tuple[pygame.Rect, Tuple[int, int, int]]]:
    """Create and return a list of alien (rect, color) tuples."""
    aliens = []
    start_x = (
        SCREEN_WIDTH - (ALIEN_COLS * ALIEN_WIDTH + (ALIEN_COLS - 1) * ALIEN_H_SPACING)
    ) // 2
    start_y = 50
    for row in range(ALIEN_ROWS):
        for col in range(ALIEN_COLS):
            x = start_x + col * (ALIEN_WIDTH + ALIEN_H_SPACING)
            y = start_y + row * (ALIEN_HEIGHT + ALIEN_V_SPACING)
            rect = pygame.Rect(x, y, ALIEN_WIDTH, ALIEN_HEIGHT)
            color = random.choice([RED, GREEN, BLUE, YELLOW])
            aliens.append((rect, color))
    return aliens


def create_shelters() -> List[pygame.Rect]:
    """Create bomb shelter blocks.

    Each shelter consists of a 3x3 grid of blocks with the shape:
    0 1 0
    1 1 1
    1 0 1
    This results in 6 blocks per shelter.
    """
    shelters = []
    # Calculate starting x to center the group of shelters
    start_x = (
        SCREEN_WIDTH
        - (NUM_SHELTERS * SHELTER_WIDTH + (NUM_SHELTERS - 1) * SHELTER_SPACING)
    ) // 2
    # Position shelters above the player
    y = SCREEN_HEIGHT - PLAYER_HEIGHT - 80
    for i in range(NUM_SHELTERS):
        shelter_origin_x = start_x + i * (SHELTER_WIDTH + SHELTER_SPACING)
        # Generate blocks for this shelter based on SHELTER_SHAPE
        for row_idx, row in enumerate(SHELTER_SHAPE):
            for col_idx, cell in enumerate(row):
                if cell:
                    block_x = shelter_origin_x + col_idx * SHELTER_BLOCK_WIDTH
                    block_y = y + row_idx * SHELTER_BLOCK_HEIGHT
                    rect = pygame.Rect(
                        block_x, block_y, SHELTER_BLOCK_WIDTH, SHELTER_BLOCK_HEIGHT
                    )
                    shelters.append(rect)
    return shelters


def run() -> None:
    """Run Space Invaders using the shared run helper."""
    from games.run_helper import run_game

    run_game(SpaceInvadersState)


if __name__ == "__main__":
    run()
