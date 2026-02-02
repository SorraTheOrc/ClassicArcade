# main.py
"""Main entry point for the arcade suite.
Provides a loading screen with a menu to select one of the classic arcade games.
"""

import pygame

# Import game modules
import games.snake as snake
import games.pong as pong
import games.breakout as breakout
import games.space_invaders as space_invaders
import games.tetris as tetris

from utils import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK, YELLOW, draw_text


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Arcade Suite")
    clock = pygame.time.Clock()

    menu_items = ["Snake", "Pong", "Breakout", "Space Invaders", "Tetris"]
    selected = 0
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    selected = (selected - 1) % len(menu_items)
                elif event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(menu_items)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    # Launch selected game
                    if selected == 0:
                        snake.run()
                    elif selected == 1:
                        pong.run()
                    elif selected == 2:
                        breakout.run()
                    elif selected == 3:
                        space_invaders.run()
                    elif selected == 4:
                        tetris.run()
                    # Re‑initialize pygame after returning from the game (the game calls pygame.quit())
                    pygame.init()
                    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
                    pygame.display.set_caption("Arcade Suite")
                    clock = pygame.time.Clock()
                elif event.key == pygame.K_ESCAPE:
                    running = False
                    break
        # Draw menu
        screen.fill(BLACK)
        # Title
        draw_text(
            screen,
            "Arcade Suite",
            48,
            WHITE,
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT // 4,
            center=True,
        )
        # Menu items
        start_y = SCREEN_HEIGHT // 4 + 80
        for idx, name in enumerate(menu_items):
            color = YELLOW if idx == selected else WHITE
            draw_text(
                screen,
                name,
                32,
                color,
                SCREEN_WIDTH // 2,
                start_y + idx * 50,
                center=True,
            )
        pygame.display.flip()
        clock.tick(60)
    pygame.quit()


if __name__ == "__main__":
    main()
