# games/pong.py
"""Simple Pong game implementation using Pygame.

Controls:
    Up/Down arrow keys - move the left paddle (player).
    R - restart after game over.
    ESC - return to main menu.
"""

import pygame
from utils import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    WHITE,
    BLACK,
    GREEN,
    RED,
    BLUE,
    draw_text,
)

# Game constants
PADDLE_WIDTH = 10
PADDLE_HEIGHT = 100
BALL_SIZE = 10
MAX_SCORE = 10
PADDLE_SPEED = 5
BALL_SPEED_X = 4
BALL_SPEED_Y = 4
FONT_SIZE = 24


def run():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Pong")
    clock = pygame.time.Clock()

    # Initialize paddles
    left_paddle = pygame.Rect(
        20, SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2, PADDLE_WIDTH, PADDLE_HEIGHT
    )
    right_paddle = pygame.Rect(
        SCREEN_WIDTH - 20 - PADDLE_WIDTH,
        SCREEN_HEIGHT // 2 - PADDLE_HEIGHT // 2,
        PADDLE_WIDTH,
        PADDLE_HEIGHT,
    )
    # Initialize ball
    ball = pygame.Rect(
        SCREEN_WIDTH // 2 - BALL_SIZE // 2,
        SCREEN_HEIGHT // 2 - BALL_SIZE // 2,
        BALL_SIZE,
        BALL_SIZE,
    )
    ball_vel = [BALL_SPEED_X, BALL_SPEED_Y]
    # Scores
    left_score = 0
    right_score = 0
    game_over = False
    winner = None

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.KEYDOWN:
                if game_over:
                    if event.key == pygame.K_r:
                        return run()
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        return
        keys = pygame.key.get_pressed()
        if not game_over:
            # Player paddle movement
            if keys[pygame.K_UP] and left_paddle.top > 0:
                left_paddle.move_ip(0, -PADDLE_SPEED)
            if keys[pygame.K_DOWN] and left_paddle.bottom < SCREEN_HEIGHT:
                left_paddle.move_ip(0, PADDLE_SPEED)
            # Simple AI for right paddle: follow ball Y position
            if ball.centery < right_paddle.centery and right_paddle.top > 0:
                right_paddle.move_ip(0, -PADDLE_SPEED)
            elif (
                ball.centery > right_paddle.centery
                and right_paddle.bottom < SCREEN_HEIGHT
            ):
                right_paddle.move_ip(0, PADDLE_SPEED)
            # Ball movement
            ball.move_ip(*ball_vel)
            # Collisions with top/bottom
            if ball.top <= 0 or ball.bottom >= SCREEN_HEIGHT:
                ball_vel[1] = -ball_vel[1]
            # Collisions with paddles
            if ball.colliderect(left_paddle) and ball_vel[0] < 0:
                ball_vel[0] = -ball_vel[0]
            if ball.colliderect(right_paddle) and ball_vel[0] > 0:
                ball_vel[0] = -ball_vel[0]
            # Scoring
            if ball.left <= 0:
                right_score += 1
                ball.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
                ball_vel = [BALL_SPEED_X, BALL_SPEED_Y]
            if ball.right >= SCREEN_WIDTH:
                left_score += 1
                ball.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
                ball_vel = [-BALL_SPEED_X, -BALL_SPEED_Y]
            # Check for win condition
            if left_score >= MAX_SCORE:
                game_over = True
                winner = "Player"
            elif right_score >= MAX_SCORE:
                game_over = True
                winner = "AI"
        # Drawing
        screen.fill(BLACK)
        # Draw paddles and ball
        pygame.draw.rect(screen, WHITE, left_paddle)
        pygame.draw.rect(screen, WHITE, right_paddle)
        pygame.draw.ellipse(screen, GREEN, ball)
        # Draw scores
        draw_text(
            screen,
            f"{left_score}",
            FONT_SIZE,
            WHITE,
            SCREEN_WIDTH // 4,
            30,
            center=True,
        )
        draw_text(
            screen,
            f"{right_score}",
            FONT_SIZE,
            WHITE,
            SCREEN_WIDTH * 3 // 4,
            30,
            center=True,
        )
        if game_over:
            draw_text(
                screen,
                f"{winner} wins! Press R to restart or ESC to menu",
                FONT_SIZE,
                RED,
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2,
                center=True,
            )
        pygame.display.flip()
        clock.tick(60)


if __name__ == "__main__":
    run()
