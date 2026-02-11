"""Compatibility shim for classic_arcade.audio."""

import sys as _sys

from classic_arcade import audio as _audio

_sys.modules[__name__] = _audio
