import pygame
import sys
import os

# Ensure the project root is on sys.path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from games.space_invaders import (
    SpaceInvadersState,
    BULLET_SPEED,
    BULLET_HEIGHT,
    BULLET_WIDTH,
    PLAYER_HEIGHT,
    PLAYER_WIDTH,
    ALIEN_ROWS,
    ALIEN_COLS,
)


class TestSpaceInvadersShooting:
    def setUp(self):
        pygame.init()
        self.state = SpaceInvadersState()

    def tearDown(self):
        pygame.quit()

    def test_player_can_shoot(self):
        # Patch pygame.key.get_pressed to simulate SPACE pressed
        original_get_pressed = pygame.key.get_pressed

        def fake_get_pressed():
            keys = [False] * 512
            keys[pygame.K_SPACE] = True
            return keys

        pygame.key.get_pressed = fake_get_pressed
        # Call update with small dt
        self.state.update(0.016)
        # Restore original function
        pygame.key.get_pressed = original_get_pressed
        # Verify a bullet was added
        assert len(self.state.bullets) == 1
        bullet = self.state.bullets[0]
        # Verify bullet spawns at player top center
        expected_x = self.state.player.centerx - BULLET_WIDTH // 2
        expected_y = self.state.player.top - BULLET_HEIGHT
        assert bullet.x == expected_x
        assert bullet.y == expected_y

    def test_player_bullet_moves_upward(self):
        # Add a bullet manually
        bullet = pygame.Rect(
            self.state.player.centerx - BULLET_WIDTH // 2,
            self.state.player.top - BULLET_HEIGHT,
            BULLET_WIDTH,
            BULLET_HEIGHT,
        )
        self.state.bullets.append(bullet)
        # Simulate update (no keys pressed)
        original_get_pressed = pygame.key.get_pressed
        pygame.key.get_pressed = lambda: [False] * 512
        self.state.update(0.1)  # 0.1 seconds
        pygame.key.get_pressed = original_get_pressed
        # Bullet should have moved upward by BULLET_SPEED * dt
        expected_y = bullet.y + BULLET_SPEED * -0.1  # negative because moving up
        # Since the code moves bullet up by -BULLET_SPEED each frame (not dt dependent), we only moved 0.1 sec but speed is per frame, not per second.
        # In the current implementation, bullet.move_ip(0, -BULLET_SPEED) is independent of dt.
        # Therefore after one update call, bullet.y should have decreased by BULLET_SPEED.
        assert bullet.y == self.state.player.top - BULLET_HEIGHT - BULLET_SPEED

    def test_enemy_can_shoot(self):
        # Ensure there are aliens present
        assert len(self.state.aliens) > 0
        # Force cooldown to zero
        self.state.enemy_shoot_cooldown = 0
        # Patch get_pressed to return no keys pressed
        original_get_pressed = pygame.key.get_pressed
        pygame.key.get_pressed = lambda: [False] * 512
        self.state.update(0.016)
        pygame.key.get_pressed = original_get_pressed
        # Verify an enemy bullet was added
        assert len(self.state.enemy_bullets) == 1

    def test_enemy_bullet_hits_player(self):
        # Place an enemy bullet directly overlapping the player
        bullet = pygame.Rect(
            self.state.player.x,
            self.state.player.y,
            BULLET_WIDTH,
            BULLET_HEIGHT,
        )
        self.state.enemy_bullets.append(bullet)
        # Run update (no keys pressed)
        original_get_pressed = pygame.key.get_pressed
        pygame.key.get_pressed = lambda: [False] * 512
        self.state.update(0.016)
        pygame.key.get_pressed = original_get_pressed
        # Game should be over
        assert self.state.game_over is True

    def test_player_bullet_hits_alien(self):
        # Place an alien directly above the player
        alien_rect = pygame.Rect(
            self.state.player.centerx - BULLET_WIDTH // 2,
            self.state.player.top - BULLET_HEIGHT - 1,
            BULLET_WIDTH,
            BULLET_HEIGHT,
        )
        # Replace aliens list with a single alien
        self.state.aliens = [(alien_rect, pygame.Color("red"))]
        # Add a bullet that will collide with the alien
        bullet = pygame.Rect(
            self.state.player.centerx - BULLET_WIDTH // 2,
            self.state.player.top - BULLET_HEIGHT,
            BULLET_WIDTH,
            BULLET_HEIGHT,
        )
        self.state.bullets.append(bullet)
        # Run update (no keys pressed)
        original_get_pressed = pygame.key.get_pressed
        pygame.key.get_pressed = lambda: [False] * 512
        self.state.update(0.016)
        pygame.key.get_pressed = original_get_pressed
        # Alien should be removed and score increased
        assert len(self.state.aliens) == 0
        assert self.state.score == 10
