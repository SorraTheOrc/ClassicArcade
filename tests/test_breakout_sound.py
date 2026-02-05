import pygame
import audio

from games.breakout import BreakoutState
from games.breakout.breakout import BALL_RADIUS, BALL_SPEED


def _dummy_keys():
    class DummyKeys(dict):
        def __getitem__(self, key):
            return False

    return DummyKeys()


def test_brick_hit_plays_sound(monkeypatch):
    # Capture calls to audio.play_effect
    calls = []

    def fake_play_effect(name):
        calls.append(name)

    monkeypatch.setattr(audio, "play_effect", fake_play_effect)
    # Mock pygame key presses to return no keys pressed
    monkeypatch.setattr(pygame.key, "get_pressed", lambda: _dummy_keys())
    # Initialise game state
    state = BreakoutState()
    assert state.bricks, "No bricks present to test"
    # Position ball overlapping the first brick
    brick_rect, _ = state.bricks[0]
    state.ball = pygame.Rect(
        brick_rect.x, brick_rect.y, BALL_RADIUS * 2, BALL_RADIUS * 2
    )
    state.ball_vel = [BALL_SPEED, BALL_SPEED]
    # Run update to trigger collision
    state.update(0.016)
    # Verify sound effect called for brick hit
    assert "brick.wav" in calls, f"Expected 'brick.wav' call, got {calls}"


def test_paddle_collision_plays_sound(monkeypatch):
    calls = []

    def fake_play_effect(name):
        calls.append(name)

    monkeypatch.setattr(audio, "play_effect", fake_play_effect)
    monkeypatch.setattr(pygame.key, "get_pressed", lambda: _dummy_keys())
    state = BreakoutState()
    # Position ball overlapping the paddle
    paddle = state.paddle
    state.ball = pygame.Rect(paddle.x, paddle.y, BALL_RADIUS * 2, BALL_RADIUS * 2)
    state.ball_vel = [0, BALL_SPEED]
    # Run update to trigger paddle collision
    state.update(0.016)
    assert "bounce.wav" in calls, f"Expected 'bounce.wav' call, got {calls}"
