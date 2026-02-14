"""Space Invaders Redux - The main game state class.

This module provides the main game state for Space Invaders Redux,
which uses the modding system to load alien types and levels.

Controls:
    Left/Right arrow keys - move the spaceship.
    Space - fire a bullet.
    R - restart after game over.
    ESC - return to main menu.

Waves:
    Clear all aliens to advance to the next wave.
    Each wave increases difficulty (aliens shoot faster).
    Wave number is displayed in the top-right corner.
"""

import logging
import random
from typing import Optional

import pygame

from classic_arcade.config import FONT_SIZE_MEDIUM
from classic_arcade.utils import (
    BLACK,
    BLUE,
    GREEN,
    RED,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    WHITE,
    YELLOW,
    draw_text,
)

from .alien_base import AlienBase
from .alien_loader import get_mod_loader, load_alien_types
from .level_loader import LevelLoader

logger = logging.getLogger(__name__)

# Game constants
PLAYER_WIDTH = 50
PLAYER_HEIGHT = 30
PLAYER_SPEED = 5
BULLET_WIDTH = 4
BULLET_HEIGHT = 10
BULLET_SPEED = 7
DEFAULT_ALIEN_SPEED = 1.0
DEFAULT_ALIEN_DESCEND = 20
DEFAULT_ALIEN_SHOOT_COOLDOWN = 2.0
DEFAULT_PLAYER_SHOOT_COOLDOWN = 0.75


from games.game_base import Game


class SpaceInvadersReduxState(Game):
    """Game class for Space Invaders Redux, using the modding system."""

    def __init__(
        self,
        mod_name: Optional[str] = None,
        alien_class: Optional[type[AlienBase]] = None,
    ):
        """Initialize the Space Invaders Redux state.

        Args:
            mod_name: Name of the mod to use (optional, uses first available if not specified)
            alien_class: Optional alien class to use (overrides mod loading)
        """
        # Initialize base Game class (includes countdown support)
        super().__init__()

        # Player ship
        self.player = pygame.Rect(
            (SCREEN_WIDTH - PLAYER_WIDTH) // 2,
            SCREEN_HEIGHT - PLAYER_HEIGHT - 30,
            PLAYER_WIDTH,
            PLAYER_HEIGHT,
        )
        self.bullets: list[pygame.Rect] = []
        self.enemy_bullets: list[pygame.Rect] = []
        self.aliens: list[AlienBase] = []
        self.alien_direction = 1
        self.score = 0
        self.game_over = False
        self.win = False

        # Cooldowns
        self.enemy_shoot_cooldown = DEFAULT_ALIEN_SHOOT_COOLDOWN
        self.current_wave_cooldown = DEFAULT_ALIEN_SHOOT_COOLDOWN
        self.player_shoot_cooldown = 0.0

        # Wave management
        self.current_wave = 1
        self.wave_transition_timeout = 0.0

        # Mod loading
        self.mod_name = mod_name
        self.alien_class = alien_class
        self._load_mods()

    def _load_mods(self) -> None:
        """Load modded aliens and create the level."""
        loader = get_mod_loader()
        loader.discover_mods()
        # Load all mods so they're available for create_aliens_with_types
        loader.load_all_mods()

        # Try to use the specified mod or find the first available one
        if self.mod_name:
            alien_class = loader.get_alien_class(self.mod_name)
            if alien_class is None:
                alien_class = loader.load_mod(self.mod_name)
        else:
            # Use the first discovered mod, or create a default
            mod_names = list(loader._mod_paths.keys())
            if mod_names:
                # Always use 'default' mod for wave 1 if available
                if "default" in mod_names:
                    self.mod_name = "default"
                else:
                    self.mod_name = mod_names[0]
                alien_class = loader.load_mod(self.mod_name)
            else:
                # Create a default alien class
                from .alien_loader import create_simple_alien_class

                alien_class = create_simple_alien_class(RED)
                self.mod_name = "default"

        self.alien_class = alien_class

        # Create level using the level loader with multiple alien types
        level_loader = LevelLoader()
        # Ensure alien_class is not None (should always have a value by here)
        if self.alien_class is None:
            from .alien_loader import create_simple_alien_class

            self.alien_class = create_simple_alien_class(RED)
        self.aliens = level_loader.create_aliens_with_types(
            mod_name=self.mod_name or "default",
            alien_loader=loader,
            fallback_alien_class=self.alien_class,
        )

        logger.info("Loaded mod %s with %d aliens", self.mod_name, len(self.aliens))

    def _load_next_wave(self) -> None:
        """Load the next wave in the sequence."""
        self.current_wave += 1
        self.wave_transition_timeout = 0.0

        # Reset countdown to allow new wave to start
        self.countdown_active = False
        self.countdown_remaining = 0.0

        # Reset game state for new wave
        self.bullets = []
        self.enemy_bullets = []
        self.game_over = False
        self.win = False
        self.alien_direction = 1
        self.player.left = (SCREEN_WIDTH - PLAYER_WIDTH) // 2

        # Reload the level with updated wave parameters
        level_loader = LevelLoader()
        loader = get_mod_loader()
        # Load all mods so they're available for create_aliens_with_types
        loader.load_all_mods()
        if self.alien_class is None:
            from .alien_loader import create_simple_alien_class

            self.alien_class = create_simple_alien_class(RED)
        self.aliens = level_loader.create_aliens_with_types(
            mod_name=self.mod_name or "default",
            alien_loader=loader,
            fallback_alien_class=self.alien_class,
        )

        # Increase difficulty for next wave
        self.current_wave_cooldown = max(
            0.5, DEFAULT_ALIEN_SHOOT_COOLDOWN - (self.current_wave * 0.1)
        )
        self.enemy_shoot_cooldown = self.current_wave_cooldown

        logger.info(
            "Loaded wave %d with %d aliens", self.current_wave, len(self.aliens)
        )

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle pygame events."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                from classic_arcade.engine import MenuState
                from classic_arcade.menu_items import get_menu_items

                self.next_state = MenuState(get_menu_items())
            elif event.key == pygame.K_r:
                self.__init__(mod_name=self.mod_name, alien_class=self.alien_class)

    def update(self, dt: float) -> None:
        """Update game state."""
        # Handle countdown (inherited from Game base class)
        if self.countdown_active:
            self.countdown_remaining -= dt
            if self.countdown_remaining <= 0:
                # Countdown expired, start next wave
                self.countdown_active = False
                self.countdown_remaining = 0.0
                self._load_next_wave()
            else:
                # Countdown still active, skip game logic
                return

        if self.game_over or self.paused:
            return

        keys = pygame.key.get_pressed()

        # Player movement
        if keys[pygame.K_LEFT] and self.player.left > 0:
            self.player.move_ip(-PLAYER_SPEED, 0)
        if keys[pygame.K_RIGHT] and self.player.right < SCREEN_WIDTH:
            self.player.move_ip(PLAYER_SPEED, 0)

        # Move player bullets
        for bullet in self.bullets[:]:
            bullet.move_ip(0, -BULLET_SPEED)
            if bullet.bottom < 0:
                self.bullets.remove(bullet)

        # Move enemy bullets
        for bullet in self.enemy_bullets[:]:
            bullet.move_ip(0, BULLET_SPEED)
            if bullet.top > SCREEN_HEIGHT:
                self.enemy_bullets.remove(bullet)

        # Enemy shooting timer
        self.enemy_shoot_cooldown -= dt

        # Player shooting cooldown timer
        self.player_shoot_cooldown -= dt

        # Enemy shooting (alien shoots when cooldown expires)
        if self.enemy_shoot_cooldown <= 0 and self.aliens:
            alien = random.choice(self.aliens)
            enemy_bullet = alien.shoot()
            self.enemy_bullets.append(enemy_bullet)
            # Reset to current wave's cooldown (which may be lower due to difficulty scaling)
            self.enemy_shoot_cooldown = self.current_wave_cooldown

        # Player shooting
        if keys[pygame.K_SPACE] and self.player_shoot_cooldown <= 0:
            bullet = pygame.Rect(
                self.player.centerx - BULLET_WIDTH // 2,
                self.player.top - BULLET_HEIGHT,
                BULLET_WIDTH,
                BULLET_HEIGHT,
            )
            self.bullets.append(bullet)
            self.player_shoot_cooldown = DEFAULT_PLAYER_SHOOT_COOLDOWN

        # Move aliens horizontally
        move_down = False
        for alien in self.aliens:
            alien.move(dt, self.alien_direction)
            if alien.rect.right >= SCREEN_WIDTH or alien.rect.left <= 0:
                move_down = True

        if move_down:
            self.alien_direction *= -1
            for alien in self.aliens:
                alien.rect.move_ip(0, DEFAULT_ALIEN_DESCEND)

        # Bullet-alien collisions
        for bullet in self.bullets[:]:
            for i, alien in enumerate(self.aliens):
                if bullet.colliderect(alien.rect):
                    self.aliens.pop(i)
                    self.bullets.remove(bullet)
                    self.score += 10
                    break

        # Enemy bullet-player collisions
        for bullet in self.enemy_bullets[:]:
            if bullet.colliderect(self.player):
                self.game_over = True
                self.enemy_bullets.remove(bullet)
                break

        # Check win - check if wave is complete (aliens cleared)
        if not self.aliens:
            self.win = True

        # Handle level transition countdown (after win is set)
        if self.win and not self.countdown_active:
            self.countdown_active = True
            self.countdown_remaining = 3.0

        # Check lose
        for alien in self.aliens:
            if alien.rect.bottom >= self.player.top:
                self.game_over = True
                break

    def draw(self, screen: pygame.Surface) -> None:
        """Draw the game to the screen."""
        screen.fill(BLACK)

        # Draw player
        pygame.draw.rect(screen, WHITE, self.player)

        # Draw bullets
        for bullet in self.bullets:
            pygame.draw.rect(screen, YELLOW, bullet)

        # Draw enemy bullets
        for bullet in self.enemy_bullets:
            pygame.draw.rect(screen, RED, bullet)

        # Draw aliens
        for alien in self.aliens:
            alien.draw(screen)

        # Draw score
        draw_text(
            screen,
            f"Score: {self.score}",
            FONT_SIZE_MEDIUM,
            WHITE,
            60,
            20,
            center=False,
        )

        # Draw wave
        draw_text(
            screen,
            f"Wave: {self.current_wave}",
            FONT_SIZE_MEDIUM,
            WHITE,
            SCREEN_WIDTH - 120,
            20,
            center=False,
        )

        # Draw countdown overlay if active
        if self.countdown_active:
            self.draw_countdown(screen)
        elif self.game_over:
            draw_text(
                screen,
                "Game Over! Press R to restart or ESC to menu",
                FONT_SIZE_MEDIUM,
                RED,
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2,
                center=True,
            )
        elif self.win:
            draw_text(
                screen,
                "You Win! Starting next wave...",
                FONT_SIZE_MEDIUM,
                GREEN,
                SCREEN_WIDTH // 2,
                SCREEN_HEIGHT // 2,
                center=True,
            )


def run() -> None:
    """Run Space Invaders Redux using the shared run helper."""
    from games.run_helper import run_game

    run_game(SpaceInvadersReduxState)


if __name__ == "__main__":
    run()
