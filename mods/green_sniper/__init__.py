"""Green Sniper mod for Space Invaders Redux.

This mod features green aliens that are slower but have larger hit points
(different visual style). It demonstrates a different visual approach.
"""

import pygame

from games.space_invaders_redux.alien_base import AlienBase


class GreenSniperAlien(AlienBase):
    """Green alien with larger size and different visual style."""

    DEFAULT_SPEED = 1.1  # Move at 110% of default speed (10% faster)
    DEFAULT_SHOOT_CHANCE = 0.002  # Lower shooting rate
    DEFAULT_BULLET_SPEED = 8.0  # Faster bullets
    DEFAULT_COLOR = (255, 0, 0)  # Red
    DEFAULT_WIDTH = 50
    DEFAULT_HEIGHT = 40

    def __init__(self, x: int, y: int, width: int, height: int):
        """Initialize a green sniper alien.

        Args:
            x: X coordinate of the alien's left edge
            y: Y coordinate of the alien's top edge
            width: Width of the alien in pixels
            height: Height of the alien in pixels
        """
        # Store original dimensions for reference
        self.original_width = width
        self.original_height = height
        super().__init__(x, y, width, height)

    def move(self, dt: float, direction: int) -> None:
        """Move the alien horizontally.

        Args:
            dt: Delta time in seconds
            direction: 1 for right, -1 for left
        """
        move_amount = int(self.speed * direction * dt * 200)
        self.rect.move_ip(move_amount, 0)

    def draw(self, screen: pygame.Surface) -> None:
        """Draw a green alien with sniper scope visual.

        Args:
            screen: Pygame surface to draw to
        """
        # Draw the main body (green)
        pygame.draw.rect(screen, self.color, self.rect)

        # Draw sniper scope pattern
        scope_color = (0, 150, 0)  # Darker green
        pygame.draw.rect(
            screen,
            scope_color,
            (
                self.rect.x + 5,
                self.rect.y + 5,
                self.rect.width - 10,
                self.rect.height - 10,
            ),
            2,
        )

        # Draw center dot
        center_x = self.rect.centerx
        center_y = self.rect.centery
        pygame.draw.circle(screen, scope_color, (center_x, center_y), 3)

        # Draw eyes
        eye_color = (0, 0, 0)  # Black
        eye_width = self.rect.width // 8
        eye_height = self.rect.height // 6

        pygame.draw.rect(
            screen,
            eye_color,
            (self.rect.x + 8, self.rect.y + 10, eye_width, eye_height),
        )
        pygame.draw.rect(
            screen,
            eye_color,
            (
                self.rect.x + self.rect.width - 8 - eye_width,
                self.rect.y + 10,
                eye_width,
                eye_height,
            ),
        )

    def get_rect(self) -> pygame.Rect:
        """Return the alien's bounding rectangle.

        Returns:
            Rect representing the alien's position and size
        """
        return self.rect
