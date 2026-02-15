"""Blue Wave mod for Space Invaders Redux.

This mod features a blue alien that moves faster and shoots more frequently.
It demonstrates how to customize alien behavior through Python.
"""

import random

import pygame

from games.space_invaders_redux.alien_base import AlienBase


class BlueWaveAlien(AlienBase):
    """Blue alien with higher shooting rate but slower movement."""

    # Override class constants for custom behavior
    DEFAULT_SPEED = 1.0  # Move at 100% of base speed
    DEFAULT_SHOOT_CHANCE = 0.005  # 5x higher shooting rate
    DEFAULT_BULLET_SPEED = 6.0
    DEFAULT_COLOR = (0, 0, 255)  # Bright blue

    def __init__(self, x: int, y: int, width: int, height: int):
        """Initialize a blue wave alien.

        Args:
            x: X coordinate of the alien's left edge
            y: Y coordinate of the alien's top edge
            width: Width of the alien in pixels
            height: Height of the alien in pixels
        """
        super().__init__(x, y, width, height)
        # Randomize shooting chance slightly for variety
        self.shoot_chance = self.DEFAULT_SHOOT_CHANCE * random.uniform(0.8, 1.2)

    def move(self, dt: float, direction: int) -> None:
        """Move the alien horizontally with slight vertical drift.

        Args:
            dt: Delta time in seconds
            direction: 1 for right, -1 for left
        """
        move_amount = self.speed * direction * dt * 60
        self._fractional_x += move_amount
        integer_move = int(self._fractional_x)
        self._fractional_x -= integer_move
        self.rect.move_ip(integer_move, 0)

        # Add slight vertical drift based on row position
        # Aliens at different heights drift differently for visual interest
        drift = int((self.rect.y % 3) * 0.1 * direction)
        self.rect.move_ip(0, drift)

    def draw(self, screen: pygame.Surface) -> None:
        """Draw a blue alien with a wave pattern.

        Args:
            screen: Pygame surface to draw to
        """
        # Draw the main body (blue)
        pygame.draw.rect(screen, self.color, self.rect)

        # Draw wave pattern on top
        wave_color = (1.0, 100, 255)  # Lighter blue
        wave_width = self.rect.width // 3
        wave_height = self.rect.height // 4

        for i in range(3):
            x = self.rect.x + i * wave_width + wave_width // 4
            y = self.rect.y + wave_height
            pygame.draw.ellipse(
                screen, wave_color, (x, y, wave_width // 2, wave_height)
            )

        # Draw eyes
        eye_color = (0, 0, 0)  # Black
        eye_width = self.rect.width // 6
        eye_height = self.rect.height // 5

        pygame.draw.rect(
            screen, eye_color, (self.rect.x + 5, self.rect.y + 8, eye_width, eye_height)
        )
        pygame.draw.rect(
            screen,
            eye_color,
            (
                self.rect.x + self.rect.width - 5 - eye_width,
                self.rect.y + 8,
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
