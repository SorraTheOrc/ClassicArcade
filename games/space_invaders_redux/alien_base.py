"""Abstract base class for Space Invaders Redux modded aliens.

This module defines the interface that all modded aliens must implement.
The base class provides default behavior for movement and shooting while
allowing mods to customize parameters and behavior through inheritance.
"""

import abc
import random

import pygame

from classic_arcade.utils import SCREEN_HEIGHT, SCREEN_WIDTH


class AlienBase(abc.ABC):
    """Abstract base class for all Space Invaders Redux aliens.

    Subclasses must implement:
    - `move()`: Define how the alien moves each frame
    - `draw()`: Define how the alien is rendered
    - `get_rect()`: Return the alien's bounding rectangle

    The base class provides default implementations for:
    - `should_shoot()`: Chance-based shooting logic
    - `shoot()`: Create enemy bullets
    """

    # Class-level constants that can be overridden in subclasses
    DEFAULT_SPEED = (
        1.0  # Base horizontal speed per frame (multiplied by speed modifier)
    )
    DEFAULT_SHOOT_CHANCE = 0.001  # Probability of shooting per frame
    DEFAULT_BULLET_SPEED = 5.0
    DEFAULT_BULLET_WIDTH = 4
    DEFAULT_BULLET_HEIGHT = 10
    DEFAULT_COLOR = (255, 0, 0)  # Red by default

    def __init__(self, x: int, y: int, width: int, height: int):
        """Initialize an alien at the given position.

        Args:
            x: X coordinate of the alien's left edge
            y: Y coordinate of the alien's top edge
            width: Width of the alien in pixels
            height: Height of the alien in pixels
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.speed = self.DEFAULT_SPEED
        self.color = self.DEFAULT_COLOR
        self.shoot_chance = self.DEFAULT_SHOOT_CHANCE
        self.bullet_speed = self.DEFAULT_BULLET_SPEED
        self.bullet_width = self.DEFAULT_BULLET_WIDTH
        self.bullet_height = self.DEFAULT_BULLET_HEIGHT
        self.direction = 1  # 1 = right, -1 = left

    @abc.abstractmethod
    def move(self, dt: float, direction: int) -> None:
        """Move the alien based on the given direction.

        Args:
            dt: Delta time in seconds
            direction: 1 for right, -1 for left
        """
        pass

    @abc.abstractmethod
    def draw(self, screen: pygame.Surface) -> None:
        """Draw the alien to the screen.

        Args:
            screen: Pygame surface to draw to
        """
        pass

    @abc.abstractmethod
    def get_rect(self) -> pygame.Rect:
        """Return the alien's bounding rectangle.

        Returns:
            Rect representing the alien's position and size
        """
        pass

    def should_shoot(self) -> bool:
        """Determine if this alien should shoot based on its shoot chance.

        Returns:
            True if the alien should shoot, False otherwise
        """
        return random.random() < self.shoot_chance

    def shoot(self) -> pygame.Rect:
        """Create an enemy bullet from this alien.

        Returns:
            A Rect representing the enemy bullet
        """
        bullet_x = self.rect.centerx - self.bullet_width // 2
        bullet_y = self.rect.bottom
        return pygame.Rect(bullet_x, bullet_y, self.bullet_width, self.bullet_height)

    def get_color(self) -> tuple[int, int, int]:
        """Get the alien's color.

        Returns:
            RGB tuple for the alien's color
        """
        return self.color
