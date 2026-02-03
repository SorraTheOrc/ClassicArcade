import unittest
import pygame
import os
import sys

# Ensure the project root is on sys.path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from games.space_invaders import (
    SpaceInvadersState,
    SHELTER_COLOR,
    SHELTER_WIDTH,
    SHELTER_HEIGHT,
    PLAYER_WIDTH,
    PLAYER_HEIGHT,
    BULLET_WIDTH,
    BULLET_HEIGHT,
    NUM_SHELTERS,
)


class TestSpaceInvadersShelters(unittest.TestCase):
    def setUp(self):
        pygame.init()
        self.state = SpaceInvadersState()

    def tearDown(self):
        pygame.quit()

    def test_enemy_bullet_hits_shelter(self):
        # Ensure there is at least one shelter
        self.assertGreater(len(self.state.shelters), 0)
        shelter = self.state.shelters[0]
        # Place an enemy bullet overlapping the shelter
        bullet = pygame.Rect(shelter.x, shelter.y, BULLET_WIDTH, BULLET_HEIGHT)
        self.state.enemy_bullets.append(bullet)
        # Run update (no keys pressed)
        pygame.key.get_pressed = lambda: [False] * 512
        self.state.update(0.016)
        # Bullet should be removed and game not over
        self.assertEqual(len(self.state.enemy_bullets), 0)
        self.assertFalse(self.state.game_over)

    def test_player_protected_by_shelter(self):
        # Place player inside a shelter
        shelter = self.state.shelters[0]
        self.state.player.topleft = shelter.topleft
        # Place an enemy bullet overlapping the player (and shelter)
        bullet = pygame.Rect(
            self.state.player.x, self.state.player.y, BULLET_WIDTH, BULLET_HEIGHT
        )
        self.state.enemy_bullets.append(bullet)
        # Run update (no keys pressed)
        pygame.key.get_pressed = lambda: [False] * 512
        self.state.update(0.016)
        # Bullet should be removed and player not dead
        self.assertEqual(len(self.state.enemy_bullets), 0)
        self.assertFalse(self.state.game_over)

    def test_player_not_protected_without_shelter(self):
        # Ensure player is not overlapping any shelter
        # Move player to leftmost position away from shelters
        self.state.player.topleft = (0, self.state.player.top)
        # Ensure no shelter overlaps player
        overlapping = any(
            shelter.colliderect(self.state.player) for shelter in self.state.shelters
        )
        self.assertFalse(overlapping)
        # Place an enemy bullet overlapping the player
        bullet = pygame.Rect(
            self.state.player.x, self.state.player.y, BULLET_WIDTH, BULLET_HEIGHT
        )
        self.state.enemy_bullets.append(bullet)
        # Run update (no keys pressed)
        pygame.key.get_pressed = lambda: [False] * 512
        self.state.update(0.016)
        # Player should be dead
        self.assertTrue(self.state.game_over)

    def test_shelter_block_count(self):
        # Each shelter should have 6 blocks (shape 0 1 0 / 1 1 1 / 1 0 1)
        expected_blocks = NUM_SHELTERS * 6
        self.assertEqual(len(self.state.shelters), expected_blocks)


if __name__ == "__main__":
    unittest.main()
