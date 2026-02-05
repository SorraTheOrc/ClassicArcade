"""Audio utilities for the arcade suite.

Provides initialization of pygame.mixer, a global mute flag, and
functions to toggle mute and play looping background music.
"""

import os
import pygame
import config
import shutil


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
    # Prefer an explicit background music file; fall back to mp3, then placeholder.
    music_path = os.path.join(base_dir, "assets", "sounds", "background.wav")
    if not os.path.isfile(music_path):
        # Try MP3 music file if present.
        mp3_path = os.path.join(base_dir, "assets", "sounds", "music.mp3")
        if os.path.isfile(mp3_path):
            music_path = mp3_path
        else:
            placeholder_path = os.path.join(
                base_dir, "assets", "sounds", "placeholder.wav"
            )
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
    # Persist the mute setting
    try:
        config.save_settings()
    except Exception:
        pass
    if not pygame.mixer.get_init():
        return

    # When muting, perform a fade-out over 0.5 seconds instead of cutting audio instantly.
    # When unmuting, restore volume and (re)start music playback if needed.
    try:
        if config.MUTE:
            # fadeout stops playback after the fade duration
            pygame.mixer.music.fadeout(500)
        else:
            # Fade in: restore volume and (re)start playback with a 0.5s fade-in
            try:
                # Ensure target volume is 1. Start playback with fade-in so it ramps smoothly.
                pygame.mixer.music.set_volume(1)
                if not pygame.mixer.music.get_busy():
                    try:
                        pygame.mixer.music.play(-1, fade_ms=500)
                    except TypeError:
                        # Some pygame versions expect fade_ms as keyword-only or don't support it
                        try:
                            pygame.mixer.music.play(-1)
                        except Exception:
                            pass
                else:
                    # Music is already playing (unlikely after fadeout) — emulate fade-in by
                    # setting volume to 0 and ramping up in a background timer would be ideal.
                    # For simplicity, set volume to 1 immediately in this case.
                    pygame.mixer.music.set_volume(1)
            except Exception:
                # If anything goes wrong, fallback to setting volume directly
                try:
                    pygame.mixer.music.set_volume(1)
                except Exception:
                    pass
    except Exception:
        # Any mixer error should not propagate
        try:
            # Fallback: force volume to expected value
            pygame.mixer.music.set_volume(0 if config.MUTE else 1)
        except Exception:
            pass


# Lightweight sound-effect helper functions
from typing import Dict

# Cache loaded Sound objects so repeated short effects don't re-open files.
_SOUND_CACHE: Dict[str, "pygame.mixer.Sound"] = {}


def _sound_path(name: str) -> str:
    base_dir = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_dir, "assets", "sounds", name)


def ensure_sound(filename: str, placeholder_name: str = "placeholder.wav") -> bool:
    """Ensure a sound asset exists under assets/sounds.

    If the named file does not exist but a placeholder is available, copy the
    placeholder to the target filename. Returns True when the target file
    exists after the call, False otherwise.
    """
    target = _sound_path(filename)
    if os.path.isfile(target):
        return True
    placeholder = _sound_path(placeholder_name)
    try:
        if os.path.isfile(placeholder):
            # Copy placeholder to target name so the game has an asset to play.
            shutil.copyfile(placeholder, target)
            return True
    except Exception:
        # Never raise from asset handling
        return False
    return False


def play_effect(filename: str) -> None:
    """Play a short sound effect from assets/sounds.

    The function respects the global `config.MUTE` flag and will return
    immediately when muted. It attempts to load the sound once and cache
    it for subsequent calls. Errors are swallowed to keep the game running
    even when audio fails.
    """
    if config.MUTE:
        return
    try:
        if not pygame.mixer.get_init():
            return
    except Exception:
        # If mixer isn't available, bail out silently
        return

    path = _sound_path(filename)
    try:
        if filename not in _SOUND_CACHE:
            if not os.path.isfile(path):
                return
            _SOUND_CACHE[filename] = pygame.mixer.Sound(path)
        sound = _SOUND_CACHE[filename]
        try:
            sound.play()
        except Exception:
            # Some mock objects may not implement play exactly as expected.
            try:
                # In pygame Sound.play can accept kwargs; try a safe call.
                getattr(sound, "play")()
            except Exception:
                pass
    except Exception:
        # Never raise from audio playback
        return
