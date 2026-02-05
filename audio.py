"""Audio utilities for the arcade suite.

Provides initialization of pygame.mixer, a global mute flag, and
functions to toggle mute and play looping background music.
"""

import os
import pygame
import config


def init() -> None:
    """Initialise the pygame mixer and start looping background music.

    The function attempts to load ``assets/sounds/background.wav``. If that file
    does not exist, it falls back to ``assets/sounds/placeholder.wav``. Errors
    while loading or playing are ignored – the game will continue without audio.
    """
    try:
        pygame.mixer.init()
    except pygame.error:
        # Mixer could not be initialised (e.g., no audio device). Silently ignore.
        return

    base_dir = os.path.abspath(os.path.dirname(__file__))
    music_path = os.path.join(base_dir, "assets", "sounds", "background.wav")
    if not os.path.isfile(music_path):
        placeholder_path = os.path.join(base_dir, "assets", "sounds", "placeholder.wav")
        if os.path.isfile(placeholder_path):
            music_path = placeholder_path
        else:
            # No music file available.
            return
    try:
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.set_volume(0 if config.MUTE else 1)
        pygame.mixer.music.play(-1)  # Loop indefinitely.
    except pygame.error:
        # Loading or playing failed – ignore to keep the game functional.
        return


def toggle_mute() -> None:
    """Toggle the global mute flag and update music volume accordingly."""
    config.MUTE = not config.MUTE
    if pygame.mixer.get_init():
        pygame.mixer.music.set_volume(0 if config.MUTE else 1)
