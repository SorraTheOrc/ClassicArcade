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
from utils import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    WHITE,
    BLACK,
    RED,
    GREEN,
    BLUE,
    YELLOW,
    draw_text,
)
from .game_base import Game

# Game constants
PLAYER_WIDTH = 50
PLAYER_HEIGHT = 30
PLAYER_SPEED = 5
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


class SpaceInvadersState(Game):
    """Game class for Space Invaders, inherits from ``Game`` and compatible with the engine loop."""

    def __init__(self):
        super().__init__()
        # Player ship
        self.player = pygame.Rect(
            (SCREEN_WIDTH - PLAYER_WIDTH) // 2,
            SCREEN_HEIGHT - PLAYER_HEIGHT - 30,
            PLAYER_WIDTH,
            PLAYER_HEIGHT,
        )
        self.bullets = []
        self.enemy_bullets = []
        self.enemy_shoot_cooldown = 2.0  # seconds
        self.aliens = create_aliens()
        self.alien_direction = 1
        self.score = 0
        self.game_over = False
        self.win = False

    def handle_event(self, event: pygame.event.Event) -> None:
        # Let Game base handle ESC, pause, restart
        super().handle_event(event)
        # No additional handling needed for Space Invaders

    def update(self, dt: float) -> None:
        if self.game_over or self.win or self.paused:
            return
        keys = pygame.key.get_pressed()
        # Player movement
        if keys[pygame.K_LEFT] and self.player.left > 0:
            self.player.move_ip(-PLAYER_SPEED, 0)
        if keys[pygame.K_RIGHT] and self.player.right < SCREEN_WIDTH:
            self.player.move_ip(PLAYER_SPEED, 0)
        # Player shooting
        if keys[pygame.K_SPACE]:
            bullet = pygame.Rect(
                self.player.centerx - BULLET_WIDTH // 2,
                self.player.top - BULLET_HEIGHT,
                BULLET_WIDTH,
                BULLET_HEIGHT,
            )
            self.bullets.append(bullet)
        # Move bullets
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
        # Bullet-alien collisions
        for bullet in self.bullets[:]:
            hit_index = bullet.collidelist([a[0] for a in self.aliens])
            if hit_index != -1:
                self.aliens.pop(hit_index)
                self.bullets.remove(bullet)
                self.score += 10
        # Enemy bullet-player collisions
        for bullet in self.enemy_bullets[:]:
            if bullet.colliderect(self.player):
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


def create_aliens():
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


def run():
    """Run Space Invaders using the shared run helper."""
    from .run_helper import run_game

    run_game(SpaceInvadersState)


if __name__ == "__main__":
    run()
