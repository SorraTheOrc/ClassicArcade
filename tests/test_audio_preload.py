"""Tests for audio preload helper.

These tests verify that ``preload_effects`` loads the sound file and caches the
``pygame.mixer.Sound`` instance without playing it.
"""

import os
import importlib
import audio
import config
import pygame
from unittest import mock


def test_preload_effects(monkeypatch):
    """Calling ``preload_effects`` should load and cache the sound.

    The test uses a temporary filename, ensures the placeholder is copied, then
    mocks ``pygame.mixer.Sound`` to verify that the function creates a ``Sound``
    object and stores it in ``audio._SOUND_CACHE``.
    """
    # Ensure mute is off and mixer is considered initialised.
    config.MUTE = False
    monkeypatch.setattr(pygame.mixer, "get_init", lambda: True)

    # Use a unique temporary filename.
    filename = "test_preload.wav"
    target_path = audio._sound_path(filename)
    # Remove any existing file to start clean.
    if os.path.isfile(target_path):
        os.remove(target_path)

    # Ensure the placeholder is copied (creates the file).
    audio.ensure_sound(filename)

    # Mock pygame.mixer.Sound to capture instantiation.
    mock_sound = mock.Mock()

    def fake_sound(path):
        # Verify the path matches the expected target.
        assert os.path.abspath(path) == os.path.abspath(target_path)
        return mock_sound

    monkeypatch.setattr(pygame.mixer, "Sound", fake_sound)

    # Call preload – it should use the mocked Sound constructor.
    audio.preload_effects([filename])

    # Verify the cache now contains the mocked sound instance.
    assert filename in audio._SOUND_CACHE
    assert audio._SOUND_CACHE[filename] is mock_sound

    # Clean up the temporary file.
    if os.path.isfile(target_path):
        os.remove(target_path)
