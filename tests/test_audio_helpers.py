"""Tests for audio helper utilities.

These tests cover the placeholder handling and the short‑effect playback logic.
"""

import os
import importlib
from unittest import mock

import pygame
import config
import audio


# Helper to get the absolute path to a sound asset via the module function.
def _asset_path(name: str) -> str:
    return audio._sound_path(name)


def test_ensure_sound_copies_placeholder(tmp_path):
    """When a sound file is missing, ``ensure_sound`` should copy ``placeholder.wav``."""
    # Use a unique filename that does not exist in assets.
    fname = "test_placeholder_copy.wav"
    target = _asset_path(fname)
    # Ensure any leftover file is removed.
    if os.path.isfile(target):
        os.remove(target)
    # Call the function – it should copy the placeholder.
    result = audio.ensure_sound(fname)
    assert result is True
    # The file now exists.
    assert os.path.isfile(target)
    # Clean up.
    os.remove(target)


def test_play_effect_plays_when_not_muted(monkeypatch):
    """``play_effect`` should load the sound and call ``play`` when not muted."""
    # Ensure mute flag is off.
    config.MUTE = False
    # Pretend the mixer is initialised.
    monkeypatch.setattr(pygame.mixer, "get_init", lambda: True)
    # Use a unique name.
    fname = "test_play.wav"
    target = _asset_path(fname)
    # Remove any prior file.
    if os.path.isfile(target):
        os.remove(target)
    # Ensure the placeholder will be copied.
    audio.ensure_sound(fname)
    # Mock the Sound class.
    mock_sound = mock.Mock()

    def fake_sound(path):
        # Verify the path matches what we expect.
        assert os.path.abspath(path) == os.path.abspath(target)
        return mock_sound

    monkeypatch.setattr(pygame.mixer, "Sound", fake_sound)
    # Call the function.
    audio.play_effect(fname)
    # The mock's ``play`` method should have been called exactly once.
    mock_sound.play.assert_called_once()
    # Clean up.
    if os.path.isfile(target):
        os.remove(target)


def test_play_effect_respects_mute(monkeypatch):
    """When ``config.MUTE`` is True, ``play_effect`` should early‑return."""
    config.MUTE = True
    monkeypatch.setattr(pygame.mixer, "get_init", lambda: True)

    # Patch Sound to raise if called.
    def bad_sound(_):
        raise AssertionError("Sound should not be instantiated when muted")

    monkeypatch.setattr(pygame.mixer, "Sound", bad_sound)
    # Should not raise.
    audio.play_effect("any.wav")
