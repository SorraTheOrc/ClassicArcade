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
from engine import State

# Game constants
PADDLE_WIDTH = 10
PADDLE_HEIGHT = 100
BALL_SIZE = 10
MAX_SCORE = 10
PADDLE_SPEED = 5
BALL_SPEED_X = 4
BALL_SPEED_Y = 4
FONT_SIZE = 24

# State implementation for the engine
from engine import State
from utils import draw_text, WHITE, BLACK, GREEN, RED, SCREEN_WIDTH, SCREEN_HEIGHT
import pygame


class PongState(State):
    """State for the Pong game, compatible with the engine loop."""

    def __init__(self):
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
        self.winner = None

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if self.game_over:
                if event.key == pygame.K_r:
                    # Restart by reinitialising the state
                    self.__init__()
                elif event.key == pygame.K_ESCAPE:
                    # Return to menu
                    from menu_items import get_menu_items
                    from engine import MenuState

                    self.request_transition(MenuState(get_menu_items()))

    def update(self, dt: float) -> None:
        if self.game_over:
            return
        keys = pygame.key.get_pressed()
        # Player paddle movement
        if keys[pygame.K_UP] and self.left_paddle.top > 0:
            self.left_paddle.move_ip(0, -PADDLE_SPEED)
        if keys[pygame.K_DOWN] and self.left_paddle.bottom < SCREEN_HEIGHT:
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
