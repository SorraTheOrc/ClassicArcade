# games/snake.py
"""Simple Snake game implementation using Pygame.

Controls:
    Arrow keys - change direction of the snake.
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
    YELLOW,
    draw_text,
)

# Game constants
BLOCK_SIZE = 20
SNAKE_SPEED = 10  # frames per second


def run():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Snake")
    clock = pygame.time.Clock()

    # Initialize snake in the middle of the screen
    snake = [(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)]
    direction = (0, 0)  # No movement initially
    # Place first food
    food = (
        random.randrange(0, SCREEN_WIDTH // BLOCK_SIZE) * BLOCK_SIZE,
        random.randrange(0, SCREEN_HEIGHT // BLOCK_SIZE) * BLOCK_SIZE,
    )
    score = 0
    font_size = 24
    game_over = False

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.KEYDOWN:
                if not game_over:
                    if event.key == pygame.K_UP:
                        direction = (0, -BLOCK_SIZE)
                    elif event.key == pygame.K_DOWN:
                        direction = (0, BLOCK_SIZE)
                    elif event.key == pygame.K_LEFT:
                        direction = (-BLOCK_SIZE, 0)
                    elif event.key == pygame.K_RIGHT:
                        direction = (BLOCK_SIZE, 0)
                else:
                    if event.key == pygame.K_r:
                        # Restart the game
                        return run()
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        return
        if not game_over:
            # Move snake
            if direction != (0, 0):
                new_head = (snake[0][0] + direction[0], snake[0][1] + direction[1])
                # Wrap around screen (optional) or treat as collision
                # Here we treat hitting wall as game over
                if (
                    new_head[0] < 0
                    or new_head[0] >= SCREEN_WIDTH
                    or new_head[1] < 0
                    or new_head[1] >= SCREEN_HEIGHT
                ):
                    game_over = True
                else:
                    snake.insert(0, new_head)
                    # Check food collision
                    if new_head == food:
                        score += 1
                        # Place new food at a location not occupied by snake
                        while True:
                            food = (
                                random.randrange(0, SCREEN_WIDTH // BLOCK_SIZE)
                                * BLOCK_SIZE,
                                random.randrange(0, SCREEN_HEIGHT // BLOCK_SIZE)
                                * BLOCK_SIZE,
                            )
                            if food not in snake:
                                break
                    else:
                        snake.pop()
                    # Check self collision
                    if new_head in snake[1:]:
                        game_over = True
        # Drawing
        screen.fill(BLACK)
        # Draw food
        pygame.draw.rect(screen, RED, (*food, BLOCK_SIZE, BLOCK_SIZE))
        # Draw snake
        for segment in snake:
            pygame.draw.rect(screen, GREEN, (*segment, BLOCK_SIZE, BLOCK_SIZE))
        # Draw score
        draw_text(screen, f"Score: {score}", font_size, WHITE, 60, 20, center=False)
        if game_over:
            draw_text(
                screen,
                "Game Over! Press R to restart or ESC to menu",
                24,
                YELLOW,
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2,
                center=True,
            )
        pygame.display.flip()
        clock.tick(SNAKE_SPEED)


if __name__ == "__main__":
    run()
