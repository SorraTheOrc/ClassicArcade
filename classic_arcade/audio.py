"""Audio utilities for the arcade suite.

Provides initialization of pygame.mixer, a global mute flag, and
functions to toggle mute and play looping background music.
"""

import logging
import os
import shutil
import subprocess
import sys
from typing import Dict, List, Optional

import pygame

from classic_arcade import config

# ---------------------------------------------------------------------------
# Helper path functions


def _get_base_dir() -> str:
    """Return the base directory for assets, handling PyInstaller bundle paths."""
    if hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    # assets/ is at the project root (parent of classic_arcade/)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Worklog integration for missing assets
# ---------------------------------------------------------------------------

# Parent work item ID for audio-related tasks (the "Add sound and music with mute toggle" task)
_AUDIO_PARENT_WORK_ITEM_ID = "G1-0ML5DRK5F02XA14R"

# Current music track being played (to avoid repeats and for cleanup)
_CURRENT_MUSIC_TRACK: Optional[str] = None


# Custom event for when music ends
MUSIC_END_EVENT = pygame.USEREVENT + 1


def _setup_music_end_event() -> None:
    """Set up the music end event listener to trigger new random music when track finishes."""
    try:
        if not pygame.mixer.get_init():
            return
        pygame.mixer.music.set_endevent(MUSIC_END_EVENT)
    except Exception:
        pass


def _create_missing_asset_work_item(
    name: str, sound_type: Optional[str] = None
) -> None:
    """Create a child work item for a missing audio asset.

    In production builds (when the environment variable ``PRODUCTION`` is set to a truthy value),
    this function becomes a no‑op to avoid creating work items.
    """
    # Skip work‑log creation in production environments.
    if os.getenv("PRODUCTION", "").lower() in ("1", "true", "yes"):
        return
    # Skip creating work items while running tests (pytest) to avoid noisy
    # worklog entries for test-only placeholder sounds. Detect pytest by the
    # presence of the PYTEST_CURRENT_TEST env var or the pytest module in
    # sys.modules.
    if "PYTEST_CURRENT_TEST" in os.environ or "pytest" in sys.modules:
        return

    title = f"Missing sound asset: {name}"
    if sound_type:
        description = (
            f"The sound file '{name}' for game type '{sound_type}' is missing. "
            "A placeholder has been generated. Please replace it with the proper asset."
        )
    else:
        description = (
            f"The generic sound file '{name}' is missing. A placeholder has been generated. "
            "Please replace it with the proper asset."
        )
    try:
        subprocess.run(
            [
                "wl",
                "create",
                "--title",
                title,
                "--description",
                description,
                "--parent",
                _AUDIO_PARENT_WORK_ITEM_ID,
                "--issue-type",
                "task",
                "--priority",
                "medium",
                "--json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        # Silently ignore any errors (e.g., wl not configured)
        pass


def _sound_path(name: str) -> str:
    """Return the absolute path for a generic sound file.

    Path is ``<project>/assets/sounds/<name>``.
    """
    base_dir = _get_base_dir()
    return os.path.join(base_dir, "assets", "sounds", name)


def _music_dir() -> str:
    """Return the absolute path to the music assets directory."""
    base_dir = _get_base_dir()
    return os.path.join(base_dir, "assets", "music")


def _sound_path_type(sound_type: str, name: str) -> str:
    """Return the absolute path for a sound file under a game‑specific sub‑folder.

    Path is ``<project>/assets/sounds/<sound_type>/<name>``.
    """
    base_dir = _get_base_dir()
    return os.path.join(base_dir, "assets", "sounds", sound_type, name)


# ---------------------------------------------------------------------------
# Audio system initialisation
# ---------------------------------------------------------------------------


def init() -> None:
    """Initialise the audio system and preload short‑effect sounds.

    This function loads the background music (as before) **and** pre‑loads any
    short sound‑effect files that are used throughout the suite. Generic sounds
    such as ``eat.wav`` and ``crash.wav`` are pre‑loaded globally, while game‑
    specific effects are pre‑loaded under a sub‑folder named after the game (e.g.
    ``pong``). Pre‑loading eliminates the I/O latency that would occur on the
    first call to :func:`play_effect`, ensuring the sound plays instantly.
    """
    """Initialise the pygame mixer and start looping background music.

    The function attempts to load ``assets/sounds/background.wav``. If that file
    does not exist, it falls back to ``assets/sounds/placeholder.wav``. Errors
    while loading or playing are ignored – the game will continue without audio.
    """
    try:
        # Configure audio buffer for low latency
        # Use smaller buffer size to reduce audio delay (default is typically 256 or 512)
        # Setting a smaller buffer size reduces latency but may cause crackling on slow systems
        audio_driver = os.getenv("PYGAME_AUDIO_DRIVER", "")
        if audio_driver:
            os.environ["SDL_AUDIODRIVER"] = audio_driver
        elif "SDL_AUDIODRIVER" not in os.environ:
            os.environ["SDL_AUDIODRIVER"] = "pipewire"
        selected_driver = os.environ.get("SDL_AUDIODRIVER")

        # Set SDL audio buffer size via environment variable (must be set before init)
        # Values: 128 (very low latency), 256 (low), 512 (normal), 1024+ (high latency but stable)
        if "SDL_AUDIO_BUFFER_SIZE" not in os.environ:
            os.environ["SDL_AUDIO_BUFFER_SIZE"] = (
                "2048"  # Increased buffer size for stability
            )

        # Try to use a smaller buffer size for lower latency
        # Format: 16-bit signed, stereo (2 channels), 44100 Hz sample rate
        try:
            pygame.mixer.pre_init(44100, -16, 2, 512)
        except Exception:
            pass

        try:
            pygame.mixer.init()
        except pygame.error:
            fallback_drivers = ("pipewire", "pulseaudio", "alsa", "dsp")
            for driver in fallback_drivers:
                try:
                    os.environ["SDL_AUDIODRIVER"] = driver
                    pygame.mixer.init()
                    selected_driver = driver
                    break
                except pygame.error:
                    continue
            else:
                return
        logging.getLogger(__name__).info(
            "Audio initialized with SDL_AUDIODRIVER=%s",
            selected_driver or "default",
        )
        _setup_music_end_event()
    except pygame.error:
        return

    # Use the same path resolution as _music_dir() and _sound_path()
    base_dir = _get_base_dir()
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
        try:
            if ensure_sound("background.wav"):
                music_path = os.path.join(sounds_dir, "background.wav")
        except Exception:
            music_path = None

    if music_path is None:
        return

    try:
        # Don't play music if random music feature is disabled
        # The menu state will play random music when it becomes active
        if config.ENABLE_MUSIC:
            import random

            music_files = get_music_files()
            if music_files:
                music_path = random.choice(music_files)
                global _CURRENT_MUSIC_TRACK
                _CURRENT_MUSIC_TRACK = music_path
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(0 if config.MUTE else 1)
            pygame.mixer.music.play()
        # Pre‑load generic short‑effect sounds used across multiple games.
        # preload_effects(["eat.wav", "crash.wav"])  # Removed generic preload; snake sounds are loaded via type‑specific path
        # Pre‑load Pong‑specific short‑effect sounds removed – lazy loading via play_effect will handle them.
        # preload_effects(
        #     [
        #         "pong_hit.wav",
        #         "pong_wall.wav",
        #         "pong_score.wav",
        #         "pong_game_over.wav",
        #     ],
        #     sound_type="pong",
        # )
    except (pygame.error, FileNotFoundError, OSError, Exception):
        return


# ---------------------------------------------------------------------------
# Mute handling
# ---------------------------------------------------------------------------


def toggle_mute() -> None:
    """Toggle the global mute flag and update music volume accordingly."""
    config.MUTE = not config.MUTE
    try:
        config.save_settings()
    except Exception:
        pass
    if not pygame.mixer.get_init():
        return
    try:
        if config.MUTE:
            # Mute: set volume to 0 and stop playback
            pygame.mixer.music.set_volume(0)
            pygame.mixer.music.stop()
        else:
            # Unmute: set volume to full and ensure music is playing
            pygame.mixer.music.set_volume(1)
            if not pygame.mixer.music.get_busy():
                try:
                    pygame.mixer.music.play(-1)
                except Exception:
                    pass
    except Exception:
        # Fallback: set volume according to mute state
        try:
            pygame.mixer.music.set_volume(0 if config.MUTE else 1)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Random music playback
# ---------------------------------------------------------------------------


def get_music_files() -> List[str]:
    """Return a list of music file paths from the music directory.

    Only files with supported audio extensions (mp3, wav, ogg) that don't contain
    "sound-effect" in their name are included (to exclude sound effects).
    """
    music_dir = _music_dir()
    if not os.path.isdir(music_dir):
        return []
    supported_extensions = (".mp3", ".wav", ".ogg")
    files = []
    try:
        for filename in os.listdir(music_dir):
            if filename.lower().endswith(supported_extensions):
                # Filter out sound effect files by filename pattern
                if "sound-effect" not in filename.lower():
                    files.append(os.path.join(music_dir, filename))
    except Exception:
        pass
    return files


def play_random_music(context: str = "menu") -> None:
    """Play a random music file from the music directory.

    The function respects the global ``config.MUTE`` and ``config.ENABLE_MUSIC`` flags.
    Only one music track may be playing at any time - starting a new track stops
    the previous track cleanly.

    Args:
        context: The context where music is being played. Currently supports
                 "menu" and "game". Used for future extensibility.
    """
    if not pygame.mixer.get_init():
        return
    if config.MUTE or not config.ENABLE_MUSIC:
        return
    if is_music_playing():
        return
    try:
        music_files = get_music_files()
        if not music_files:
            return
        global _CURRENT_MUSIC_TRACK
        previous_track = _CURRENT_MUSIC_TRACK
        available_files = [f for f in music_files if f != previous_track]
        if not available_files:
            available_files = music_files
        import random

        music_path = random.choice(available_files)
        _CURRENT_MUSIC_TRACK = music_path
        try:
            pygame.mixer.music.load(music_path)
            pygame.mixer.music.set_volume(1.0 if not config.MUTE else 0.0)
            # Play once without looping - when track ends, MUSIC_END_EVENT triggers new random track
            pygame.mixer.music.play()
        except Exception:
            pass
    except Exception:
        pass


def stop_music() -> None:
    """Stop the currently playing music track.

    This function respects the global ``config.MUTE`` flag.
    """
    if not pygame.mixer.get_init():
        return
    try:
        pygame.mixer.music.stop()
    except Exception:
        pass


def is_music_playing() -> bool:
    """Return True if background music is currently playing."""
    if not pygame.mixer.get_init():
        return False
    try:
        return bool(pygame.mixer.music.get_busy())
    except Exception:
        return False


__all__ = [
    "init",
    "toggle_mute",
    "play_effect",
    "preload_effects",
    "play_random_music",
    "is_music_playing",
    "stop_music",
    "fade_out_music",
    "on_music_end",
    "get_music_files",
]


def fade_out_music(duration_ms: int = 1000) -> None:
    """Fade out the currently playing music over the specified duration.

    Args:
        duration_ms: Duration of the fade-out in milliseconds.
    """
    if not pygame.mixer.get_init():
        return
    try:
        pygame.mixer.music.fadeout(duration_ms)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Sound‑effect helper infrastructure
# ---------------------------------------------------------------------------

_SOUND_CACHE: Dict[str, "pygame.mixer.Sound"] = {}


def on_music_end() -> None:
    """Called when the current music track finishes playing.

    Plays a new random music track to keep the audio going.
    """
    if not pygame.mixer.get_init():
        return
    try:
        if config.MUTE or not config.ENABLE_MUSIC:
            return
        play_random_music(context="menu")
    except Exception:
        pass


def ensure_sound(filename: str, placeholder_name: str = "placeholder.wav") -> bool:
    """Ensure a generic sound asset exists under ``assets/sounds``.

    The function follows the *prefixed placeholder* convention:
    1. If ``filename`` already exists, nothing is done.
    2. If a per‑sound placeholder ``placeholder_<filename>`` exists, it is copied to
       ``filename``.
    3. Otherwise a generic placeholder ``placeholder.wav`` is copied to the
       per‑sound placeholder name, then that placeholder is copied to ``filename``.
    Returns ``True`` when ``filename`` exists after the call, ``False`` otherwise.
    """
    target = _sound_path(filename)
    if os.path.isfile(target):
        return True
    prefixed_placeholder = _sound_path(f"placeholder_{filename}")
    if os.path.isfile(prefixed_placeholder):
        return True
    generic_placeholder = _sound_path(placeholder_name)
    if os.path.isfile(generic_placeholder):
        try:
            shutil.copyfile(generic_placeholder, prefixed_placeholder)
            # Create a work item for the missing asset
            _create_missing_asset_work_item(filename)
            return True
        except Exception:
            return False
    return False


def ensure_sound_type(
    sound_type: str, filename: str, placeholder_name: str = "placeholder.wav"
) -> bool:
    """Ensure a sound asset exists under ``assets/sounds/<sound_type>``.

    Mirrors :func:`ensure_sound` but works inside a game‑specific sub‑folder.
    Returns ``True`` when the file (or its prefixed placeholder) exists after the
    call, ``False`` otherwise.
    """
    target = _sound_path_type(sound_type, filename)
    if os.path.isfile(target):
        return True
    prefixed_placeholder = _sound_path_type(sound_type, f"placeholder_{filename}")
    if os.path.isfile(prefixed_placeholder):
        return True
    generic_placeholder = _sound_path(placeholder_name)
    if os.path.isfile(generic_placeholder):
        os.makedirs(os.path.dirname(prefixed_placeholder), exist_ok=True)
        try:
            shutil.copyfile(generic_placeholder, prefixed_placeholder)
            # Create a work item for the missing asset in the specific sound type
            _create_missing_asset_work_item(filename, sound_type)
            return True
        except Exception:
            return False
    return False


def preload_effects(filenames: List[str], sound_type: Optional[str] = None) -> None:
    """Preload a list of short sound‑effect files.

    If ``sound_type`` is provided, the files are looked up under the corresponding
    sub‑folder; otherwise they are loaded from the generic sounds directory.
    """
    if not pygame.mixer.get_init():
        return
    for filename in filenames:
        try:
            if sound_type:
                ensure_sound_type(sound_type, filename)
            else:
                ensure_sound(filename)
        except Exception:
            pass
        try:
            if filename not in _SOUND_CACHE:
                if sound_type:
                    path = _sound_path_type(sound_type, filename)
                    prefixed = _sound_path_type(sound_type, f"placeholder_{filename}")
                else:
                    path = _sound_path(filename)
                    prefixed = _sound_path(f"placeholder_{filename}")
                if not os.path.isfile(path):
                    if os.path.isfile(prefixed):
                        path = prefixed
                if os.path.isfile(path):
                    _SOUND_CACHE[filename] = pygame.mixer.Sound(path)
        except Exception:
            pass


def play_effect(
    sound_type: Optional[str] = None, filename: Optional[str] = None
) -> None:
    """Play a short sound effect.

    The function respects the global ``config.MUTE`` flag. It can be called in two
    ways for backward compatibility:

    1. ``play_effect("click.wav")`` – the single argument is interpreted as a
       filename in the generic sounds folder.
    2. ``play_effect("pong", "wall.wav")`` – the first argument is the game type
       (sub‑folder) and the second is the filename.
    """
    import time

    if filename is None:
        filename = sound_type
        sound_type = None
    if filename is None:
        return
    if config.MUTE:
        return
    try:
        if not pygame.mixer.get_init():
            return
    except Exception:
        return
    if sound_type:
        ensure_sound_type(sound_type, filename)
        path = _sound_path_type(sound_type, filename)
        prefixed = _sound_path_type(sound_type, f"placeholder_{filename}")
    else:
        ensure_sound(filename)
        path = _sound_path(filename)
        prefixed = _sound_path(f"placeholder_{filename}")
    if not os.path.isfile(path):
        if os.path.isfile(prefixed):
            path = prefixed
        else:
            return
    try:
        if filename not in _SOUND_CACHE:
            _SOUND_CACHE[filename] = pygame.mixer.Sound(path)
        sound = _SOUND_CACHE[filename]
        try:
            sound.play()
        except Exception:
            try:
                getattr(sound, "play")()
            except Exception:
                pass
    except Exception:
        return
