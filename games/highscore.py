"""High score persistence utilities for classic arcade games.

Provides functions to store and retrieve high scores per game in JSON files.
Each game should call :func:`add_score` when a game ends, passing the
game's name (e.g. "breakout", "pong") and the final score.
The function returns the full list of score entries sorted in descending
order by score.  The caller can then display the top N entries.

The JSON format is a list of objects::

    [{"score": 123, "timestamp": "2026-02-05T12:34:56.789123"}, ...]

If the file does not exist or is malformed an empty list is returned.
"""

import json
import os
from datetime import datetime
from typing import Dict, List

# Directory for high‑score files – placed next to this module's parent directory (project root).
_HIGHSCORE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _ensure_dir() -> None:
    """Make sure the directory for high‑score files exists."""
    os.makedirs(_HIGHSCORE_DIR, exist_ok=True)


def _file_path(game_name: str) -> str:
    """Return the absolute path for the high‑score file of *game_name*.

    The file is named ``highscore_<game_name>.json`` and lives in the project
    root directory (one level above ``games/``).
    """
    filename = f"highscore_{game_name.lower()}.json"
    return os.path.join(_HIGHSCORE_DIR, filename)


def load_highscores(game_name: str) -> List[Dict]:
    """Load the list of high‑score entries for *game_name*.

    Returns an empty list if the file does not exist or cannot be parsed.
    """
    path = _file_path(game_name)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
    except Exception:
        # Corrupted file – treat as empty.
        return []
    return []


def save_highscores(game_name: str, scores: List[Dict]) -> None:
    """Write *scores* (a list of ``{"score": int, "timestamp": str}`` entries) to the JSON file."""
    _ensure_dir()
    path = _file_path(game_name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(scores, f, indent=2)


def add_score(game_name: str, score: int) -> List[Dict]:
    """Add a new *score* for *game_name* and persist the updated list.

    The function returns the full list of entries sorted by score in
    descending order.  New entries are timestamped with the current ISO‑8601
    datetime.
    """
    scores = load_highscores(game_name)
    entry = {"score": int(score), "timestamp": datetime.now().isoformat()}
    scores.append(entry)
    # Sort descending by score.
    scores.sort(key=lambda e: e["score"], reverse=True)
    save_highscores(game_name, scores)
    return scores


__all__ = ["load_highscores", "save_highscores", "add_score"]
