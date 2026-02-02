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
from engine import State

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
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
)
import pygame
import random


class SpaceInvadersState(State):
    """State for the Space Invaders game, compatible with the engine loop."""

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
        self.aliens = create_aliens()
        self.alien_direction = 1
        self.score = 0
        self.game_over = False
        self.win = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if not (self.game_over or self.win):
                if event.key == pygame.K_SPACE:
                    bullet_rect = pygame.Rect(
                        self.player.centerx - BULLET_WIDTH // 2,
                        self.player.top - BULLET_HEIGHT,
                        BULLET_WIDTH,
                        BULLET_HEIGHT,
                    )
                    self.bullets.append(bullet_rect)
            else:
                if event.key == pygame.K_r:
                    self.__init__()
                elif event.key == pygame.K_ESCAPE:
                    from menu_items import get_menu_items
                    from engine import MenuState

                    self.request_transition(MenuState(get_menu_items()))

    def update(self, dt: float) -> None:
        if self.game_over or self.win:
            return
        keys = pygame.key.get_pressed()
        # Player movement
        if keys[pygame.K_LEFT] and self.player.left > 0:
            self.player.move_ip(-PLAYER_SPEED, 0)
        if keys[pygame.K_RIGHT] and self.player.right < SCREEN_WIDTH:
            self.player.move_ip(PLAYER_SPEED, 0)
        # Move bullets
        for bullet in self.bullets[:]:
            bullet.move_ip(0, -BULLET_SPEED)
            if bullet.bottom < 0:
                self.bullets.remove(bullet)
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
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Space Invaders")
    clock = pygame.time.Clock()

    # Player ship
    player = pygame.Rect(
        (SCREEN_WIDTH - PLAYER_WIDTH) // 2,
        SCREEN_HEIGHT - PLAYER_HEIGHT - 30,
        PLAYER_WIDTH,
        PLAYER_HEIGHT,
    )
    # Bullets list (rects)
    bullets = []
    # Aliens list (rect, color)
    aliens = create_aliens()
    alien_direction = 1  # 1 = right, -1 = left
    score = 0
    game_over = False
    win = False

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.KEYDOWN:
                if not (game_over or win):
                    if event.key == pygame.K_SPACE:
                        # Fire a bullet from the top-center of the ship
                        bullet_rect = pygame.Rect(
                            player.centerx - BULLET_WIDTH // 2,
                            player.top - BULLET_HEIGHT,
                            BULLET_WIDTH,
                            BULLET_HEIGHT,
                        )
                        bullets.append(bullet_rect)
                else:
                    if event.key == pygame.K_r:
                        return run()
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        return
        keys = pygame.key.get_pressed()
        if not (game_over or win):
            # Player movement
            if keys[pygame.K_LEFT] and player.left > 0:
                player.move_ip(-PLAYER_SPEED, 0)
            if keys[pygame.K_RIGHT] and player.right < SCREEN_WIDTH:
                player.move_ip(PLAYER_SPEED, 0)
            # Move bullets
            for bullet in bullets[:]:
                bullet.move_ip(0, -BULLET_SPEED)
                if bullet.bottom < 0:
                    bullets.remove(bullet)
            # Move aliens horizontally
            move_down = False
            for i, (rect, color) in enumerate(aliens):
                rect.move_ip(ALIEN_SPEED * alien_direction, 0)
                # Check for edge collision
                if rect.right >= SCREEN_WIDTH or rect.left <= 0:
                    move_down = True
            if move_down:
                alien_direction *= -1
                for i, (rect, color) in enumerate(aliens):
                    rect.move_ip(0, ALIEN_DESCEND)
            # Bullet-alien collisions
            for bullet in bullets[:]:
                hit_index = bullet.collidelist([a[0] for a in aliens])
                if hit_index != -1:
                    # Remove alien and bullet
                    aliens.pop(hit_index)
                    bullets.remove(bullet)
                    score += 10
            # Check win condition
            if not aliens:
                win = True
            # Check lose condition: any alien reaches player's y level
            for rect, _ in aliens:
                if rect.bottom >= player.top:
                    game_over = True
                    break
        # Drawing
        screen.fill(BLACK)
        # Draw player
        pygame.draw.rect(screen, WHITE, player)
        # Draw bullets
        for bullet in bullets:
            pygame.draw.rect(screen, YELLOW, bullet)
        # Draw aliens
        for rect, color in aliens:
            pygame.draw.rect(screen, color, rect)
        # Draw score
        draw_text(screen, f"Score: {score}", FONT_SIZE, WHITE, 60, 20, center=False)
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
        if win:
            draw_text(
                screen,
                "You Win! Press R to restart or ESC to menu",
                FONT_SIZE,
                GREEN,
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2,
                center=True,
            )
        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    run()
