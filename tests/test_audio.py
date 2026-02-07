"""Tests for audio infrastructure.

These tests verify that the global mute flag defaults to ``False`` and that the
``audio`` helper can toggle the flag and initialise the mixer without raising
exceptions.
"""

import importlib

import pygame

import audio
# Import the modules under test.
import config


def test_mute_default():
    """The global mute flag should default to ``False``."""
    assert hasattr(config, "MUTE"), "config should have MUTE attribute"
    # The module exposes a `MUTE` name but it should default to False.
    assert config.MUTE is False


def test_toggle_mute():
    """Calling ``audio.toggle_mute`` should flip the ``config.MUTE`` flag.
    The function should also update the mixer volume if the mixer is initialised.
    """
    # Ensure starting state
    config.MUTE = False
    audio.toggle_mute()
    assert config.MUTE is True
    # Volume should be 0 if mixer is initialised.
    if pygame.mixer.get_init():
        assert pygame.mixer.music.get_volume() == 0
    # Toggle back
    audio.toggle_mute()
    assert config.MUTE is False
    if pygame.mixer.get_init():
        assert pygame.mixer.music.get_volume() > 0.9


def test_audio_init_no_exception():
    """Calling ``audio.init`` should not raise any exception.
    The function loads a background music file (or placeholder) and starts
    playback. Errors are caught internally, so the call should always succeed.
    """
    # Ensure mute flag is False for this test.
    config.MUTE = False
    # Reload the audio module to ensure a clean state.
    importlib.reload(audio)
    # Call init – any exception will cause the test to fail.
    audio.init()
    # If mixer is initialised, volume should be 1 (since MUTE is False).
    if pygame.mixer.get_init():
        assert pygame.mixer.music.get_volume() > 0.9
