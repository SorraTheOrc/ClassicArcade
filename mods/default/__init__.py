"""Default mod for Space Invaders Redux.

This is a simple Python-based mod that defines a basic alien class.
It serves as both a working example and a fallback when no other mods are found.
"""

import pygame

from games.space_invaders_redux.alien_base import AlienBase


class DefaultAlien(AlienBase):
    """Default alien with simple rectangular rendering."""

    DEFAULT_COLOR = (0, 255, 0)  # Green
    DEFAULT_SPEED = 0.6

    def __init__(self, x: int, y: int, width: int, height: int):
        """Initialize a default alien.

        Args:
            x: X coordinate of the alien's left edge
            y: Y coordinate of the alien's top edge
            width: Width of the alien in pixels
            height: Height of the alien in pixels
        """
        super().__init__(x, y, width, height)

    def move(self, dt: float, direction: int) -> None:
        """Move the alien horizontally based on direction.

        Args:
            dt: Delta time in seconds
            direction: 1 for right, -1 for left
        """
        move_amount = self.speed * direction * dt * 45
        self._fractional_x += move_amount
        integer_move = int(self._fractional_x)
        self._fractional_x -= integer_move
        self.rect.move_ip(integer_move, 0)

    def draw(self, screen: pygame.Surface) -> None:
        """Draw a red rectangle with simple eyes for the alien.

        Args:
            screen: Pygame surface to draw to
        """
        # Draw the main body
        pygame.draw.rect(screen, self.color, self.rect)

        # Draw simple eyes
        eye_color = (0, 0, 0)  # Black
        eye_width = self.rect.width // 5
        eye_height = self.rect.height // 6

        # Left eye
        pygame.draw.rect(
            screen,
            eye_color,
            (self.rect.x + 5, self.rect.y + 5, eye_width, eye_height),
        )
        # Right eye
        pygame.draw.rect(
            screen,
            eye_color,
            (
                self.rect.x + self.rect.width - 5 - eye_width,
                self.rect.y + 5,
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
