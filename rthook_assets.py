"""Runtime hook to fix asset paths for PyInstaller bundles."""

import os
import sys


def _resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and PyInstaller bundles."""
    if hasattr(sys, "_MEIPASS"):
        # Running in a PyInstaller bundle
        base_path = sys._MEIPASS
    else:
        # Running in a normal Python environment
        base_path = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(base_path, relative_path)


# Override the resource path functions in audio module
try:
    import audio

    original_sound_path = audio._sound_path
    original_music_dir = audio._music_dir
    original_sound_path_type = audio._sound_path_type

    def _sound_path_fixed(name: str) -> str:
        base_dir = _resource_path("assets/sounds")
        return os.path.join(base_dir, name)

    def _music_dir_fixed() -> str:
        base_dir = _resource_path("assets/music")
        return base_dir

    def _sound_path_type_fixed(sound_type: str, name: str) -> str:
        base_dir = _resource_path(f"assets/sounds/{sound_type}")
        return os.path.join(base_dir, name)

    audio._sound_path = _sound_path_fixed
    audio._music_dir = _music_dir_fixed
    audio._sound_path_type = _sound_path_type_fixed
except Exception:
    # If audio module isn't loaded yet or other error, skip
    pass
