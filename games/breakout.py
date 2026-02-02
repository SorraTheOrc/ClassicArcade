# games/breakout.py
"""Simple Breakout game implementation using Pygame.

Controls:
    Left/Right arrow keys - move the paddle.
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
    draw_text,
)

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


def create_bricks():
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


def run():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Breakout")
    clock = pygame.time.Clock()

    paddle = pygame.Rect(
        (SCREEN_WIDTH - PADDLE_WIDTH) // 2,
        SCREEN_HEIGHT - PADDLE_HEIGHT - 30,
        PADDLE_WIDTH,
        PADDLE_HEIGHT,
    )
    # Ball starts above paddle
    ball = pygame.Rect(
        paddle.centerx - BALL_RADIUS,
        paddle.top - 2 * BALL_RADIUS,
        BALL_RADIUS * 2,
        BALL_RADIUS * 2,
    )
    ball_vel = [random.choice([-BALL_SPEED, BALL_SPEED]), -BALL_SPEED]
    bricks = create_bricks()
    score = 0
    game_over = False
    win = False

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.KEYDOWN:
                if game_over or win:
                    if event.key == pygame.K_r:
                        return run()
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        return
        keys = pygame.key.get_pressed()
        if not (game_over or win):
            # Paddle movement
            if keys[pygame.K_LEFT] and paddle.left > 0:
                paddle.move_ip(-PADDLE_SPEED, 0)
            if keys[pygame.K_RIGHT] and paddle.right < SCREEN_WIDTH:
                paddle.move_ip(PADDLE_SPEED, 0)
            # Ball movement
            ball.move_ip(*ball_vel)
            # Collisions with walls
            if ball.left <= 0 or ball.right >= SCREEN_WIDTH:
                ball_vel[0] = int(-ball_vel[0])
            if ball.top <= 0:
                ball_vel[1] = -ball_vel[1]
            # Collision with paddle
            if ball.colliderect(paddle) and ball_vel[1] > 0:
                ball_vel[1] = -ball_vel[1]
                # Slightly adjust X based on where it hit paddle
                offset = (ball.centerx - paddle.centerx) / (PADDLE_WIDTH / 2)
                ball_vel[0] = int(BALL_SPEED * offset)
            # Collision with bricks
            hit_index = ball.collidelist([br[0] for br in bricks])
            if hit_index != -1:
                brick_rect, brick_color = bricks.pop(hit_index)
                score += 1
                # Simple bounce: invert Y velocity
                ball_vel[1] = -ball_vel[1]
            # Check for win
            if not bricks:
                win = True
            # Check for lose (ball below paddle)
            if ball.bottom >= SCREEN_HEIGHT:
                game_over = True
        # Drawing
        screen.fill(BLACK)
        # Draw paddle
        pygame.draw.rect(screen, WHITE, paddle)
        # Draw ball
        pygame.draw.ellipse(screen, GREEN, ball)
        # Draw bricks
        for rect, color in bricks:
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
                YELLOW,
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2,
                center=True,
            )
        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    run()
