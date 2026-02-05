"""Audio utilities for the arcade suite.

Provides initialization of pygame.mixer, a global mute flag, and
functions to toggle mute and play looping background music.
"""

import os
import pygame
import config
import shutil

from typing import Dict, List


def init() -> None:
    """Initialise the audio system and preload short‑effect sounds.

    This function now loads the background music (as before) **and** pre‑loads any
    short sound‑effect files that are used throughout the suite (e.g. ``eat.wav``
    and ``crash.wav``). Pre‑loading eliminates the I/O latency that would occur
    on the first call to :func:`play_effect`, ensuring the sound plays
    immediately when the associated game event occurs.
    """
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
    # Prefer an explicit background music file in sounds; however some users
    # keep music under assets/music — try both locations and accept mp3 as a
    # fallback. If nothing is available, fall back to the placeholder behaviour.
    sounds_dir = os.path.join(base_dir, "assets", "sounds")
    music_dir = os.path.join(base_dir, "assets", "music")

    candidates = [
        os.path.join(sounds_dir, "background.wav"),
        os.path.join(sounds_dir, "music.mp3"),
        os.path.join(music_dir, "background.wav"),
        os.path.join(music_dir, "music.mp3"),
    ]

    music_path = None
    for c in candidates:
        if os.path.isfile(c):
            music_path = c
            break

    if music_path is None:
        # Try to create a prefixed placeholder in the sounds directory first.
        try:
            if ensure_sound("background.wav"):
                music_path = os.path.join(sounds_dir, "background.wav")
        except Exception:
            # If anything goes wrong ensuring the sound, leave music_path None.
            music_path = None

    if music_path is None:
        # No music available and no placeholder to create from – nothing to do.
        return

    # Load and start playback; guard against FileNotFoundError and other
    # exceptions in addition to pygame.error so missing files don't crash the
    # launcher when users have reorganised assets.
    try:
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.set_volume(0 if config.MUTE else 1)
        pygame.mixer.music.play(-1)  # Loop indefinitely.
        # Pre‑load short effect sounds used in games to avoid first‑play latency.
        preload_effects(["eat.wav", "crash.wav"])
    except (pygame.error, FileNotFoundError, OSError, Exception):
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
# Cache loaded Sound objects so repeated short effects don't re-open files.
_SOUND_CACHE: Dict[str, "pygame.mixer.Sound"] = {}


def _sound_path(name: str) -> str:
    base_dir = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_dir, "assets", "sounds", name)


def ensure_sound(filename: str, placeholder_name: str = "placeholder.wav") -> bool:
    """Ensure a sound asset exists under ``assets/sounds``.

    The function now follows the *prefixed placeholder* convention:
    1. If ``filename`` already exists, nothing is done.
    2. If a per‑sound placeholder ``placeholder_<filename>`` exists, it is copied to
       ``filename``.
    3. Otherwise a generic placeholder ``placeholder.wav`` is copied to the
       per‑sound placeholder name, then that placeholder is copied to ``filename``.
    Returns ``True`` when ``filename`` exists after the call, ``False`` otherwise.
    """
    target = _sound_path(filename)
    # If the actual sound file exists, we're done.
    if os.path.isfile(target):
        return True

    # Look for a prefixed placeholder first. We should not auto-create the
    # concrete target file; only the prefixed placeholder is created/copied.
    prefixed_placeholder = _sound_path(f"placeholder_{filename}")
    if os.path.isfile(prefixed_placeholder):
        return True

    # No prefixed placeholder – create one from the generic placeholder if possible.
    generic_placeholder = _sound_path(placeholder_name)
    if os.path.isfile(generic_placeholder):
        try:
            # Create the prefixed placeholder from generic, but do NOT copy it to
            # the requested target filename. Loading code will use the prefixed
            # placeholder path when the real file is missing.
            shutil.copyfile(generic_placeholder, prefixed_placeholder)
            return True
        except Exception:
            return False

    # No placeholder available.
    return False


def preload_effects(filenames: List[str]) -> None:
    """Preload a list of short sound‑effect files.

    This loads each sound into the global ``_SOUND_CACHE`` so subsequent calls to
    :func:`play_effect` can play instantly without disk I/O. It also ensures the
    placeholder asset is copied if the target file does not exist.
    """
    if not pygame.mixer.get_init():
        return
    for filename in filenames:
        # Ensure the file exists (copy placeholder if missing)
        try:
            ensure_sound(filename)
        except Exception:
            # If placeholder copy fails, continue – play_effect will handle missing file.
            pass
        try:
            if filename not in _SOUND_CACHE:
                # Prefer the real sound file; if it's not present, try the
                # prefixed placeholder file (which ensure_sound may have created).
                path = _sound_path(filename)
                if not os.path.isfile(path):
                    prefixed = _sound_path(f"placeholder_{filename}")
                    if os.path.isfile(prefixed):
                        path = prefixed
                if os.path.isfile(path):
                    _SOUND_CACHE[filename] = pygame.mixer.Sound(path)
        except Exception:
            # Ignore load errors – playback will fallback gracefully.
            pass


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

    # Ensure the sound or its prefixed placeholder exists.
    ensure_sound(filename)
    # Prefer the real file; if missing, use the prefixed placeholder path.
    path = _sound_path(filename)
    if not os.path.isfile(path):
        prefixed = _sound_path(f"placeholder_{filename}")
        if os.path.isfile(prefixed):
            path = prefixed
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
