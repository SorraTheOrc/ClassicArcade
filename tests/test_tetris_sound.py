"""Unit tests for Tetris sound integration.

Verifies that rotation and line-clear events invoke the audio helper and that
the global mute flag prevents playback.
"""

import pygame
import config

from games.tetris.tetris import TetrisState, GRID_HEIGHT
import audio


def test_rotate_plays_sound(monkeypatch):
    t = TetrisState()
    # Use a shape and position where rotation is valid.
    t.current_shape_name = "T"
    t.shape_coords = t.SHAPES["T"]
    t.shape_x = 4
    t.shape_y = 0

    calls = []

    def fake_play(*args):
        """Capture audio.play_effect calls, handling both old and new signatures."""
        if len(args) == 2:
            calls.append(args[1])
        elif len(args) == 1:
            calls.append(args[0])
        else:
            pass

    monkeypatch.setattr(audio, "play_effect", fake_play)

    # Simulate pressing the rotate key
    event = pygame.event.Event(pygame.KEYDOWN, key=config.KEY_UP)
    t.handle_event(event)

    assert calls == ["rotate.wav"]


def test_line_clear_plays_sound(monkeypatch):
    t = TetrisState()
    # Position piece so it will lock immediately (at bottom)
    t.shape_coords = [(0, 0)]
    t.shape_x = 0
    t.shape_y = GRID_HEIGHT - 1

    # Force clear_lines to report a cleared line when called
    monkeypatch.setattr(t, "clear_lines", lambda grid: 1)

    calls = []

    def fake_play(*args):
        """Capture audio.play_effect calls, handling both old and new signatures."""
        if len(args) == 2:
            calls.append(args[1])
        elif len(args) == 1:
            calls.append(args[0])
        else:
            pass

    monkeypatch.setattr(audio, "play_effect", fake_play)

    # Ensure the fall timer triggers the lock path
    t.fall_timer = t.fall_interval
    t.update(1.0)

    # Expect a place sound first, then a line_clear sound
    assert calls == ["place.wav", "line_clear.wav"]


def test_place_sound_without_line(monkeypatch):
    t = TetrisState()
    # Position piece so it will lock but not clear any lines
    t.shape_coords = [(0, 0)]
    t.shape_x = 0
    t.shape_y = GRID_HEIGHT - 1

    # Force clear_lines to report zero cleared lines
    monkeypatch.setattr(t, "clear_lines", lambda grid: 0)

    calls = []

    def fake_play(*args):
        """Capture audio.play_effect calls, handling both old and new signatures."""
        if len(args) == 2:
            calls.append(args[1])
        elif len(args) == 1:
            calls.append(args[0])
        else:
            pass

    monkeypatch.setattr(audio, "play_effect", fake_play)

    # Ensure the fall timer triggers the lock path
    t.fall_timer = t.fall_interval
    t.update(1.0)

    assert calls == ["place.wav"]


def test_sounds_respect_mute(monkeypatch):
    t = TetrisState()
    t.current_shape_name = "T"
    t.shape_coords = t.SHAPES["T"]
    t.shape_x = 4
    t.shape_y = 0

    called = []

    def fake_play(*args):
        """Capture audio.play_effect calls, handling both old and new signatures, respecting mute."""
        if len(args) == 2:
            filename = args[1]
        elif len(args) == 1:
            filename = args[0]
        else:
            return
        if not config.MUTE:
            called.append(filename)

    monkeypatch.setattr(audio, "play_effect", fake_play)

    # Mute should prevent playback
    config.MUTE = True

    event = pygame.event.Event(pygame.KEYDOWN, key=config.KEY_UP)
    t.handle_event(event)

    assert called == []
