"""Tests for config module.

Ensures difficulty multiplier, get/set difficulty functions work correctly.
"""

import json
import os

import pytest

# Ensure headless mode for pygame (if needed)
os.environ["HEADLESS"] = "1"

from classic_arcade import config


def test_difficulty_multiplier_values():
    # Easy
    assert config.difficulty_multiplier(config.DIFFICULTY_EASY) == 1.0
    # Medium
    assert config.difficulty_multiplier(config.DIFFICULTY_MEDIUM) == 1.5
    # Hard
    assert config.difficulty_multiplier(config.DIFFICULTY_HARD) == 2.0
    # Unknown defaults to medium (1.5)
    assert config.difficulty_multiplier("unknown") == 1.5


def test_get_set_difficulty_and_persistence(tmp_path, monkeypatch):
    # Use a temporary directory for settings.json to avoid affecting repo
    settings_path = tmp_path / "settings.json"
    # Monkeypatch the _SETTINGS_PATH in config to point to temporary file
    monkeypatch.setattr(config, "_SETTINGS_PATH", str(settings_path))
    # Ensure defaults are easy
    assert config.get_difficulty("snake") == config.DIFFICULTY_EASY
    # Change difficulty for snake to hard
    config.set_difficulty("snake", config.DIFFICULTY_HARD)
    assert config.get_difficulty("snake") == config.DIFFICULTY_HARD
    # Verify that settings file was written and contains the new value
    with open(settings_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["snake_difficulty"] == config.DIFFICULTY_HARD
    # Changing an unknown game key should raise ValueError
    with pytest.raises(ValueError):
        config.set_difficulty("unknown_game", config.DIFFICULTY_EASY)

    # Ensure other difficulties remain unchanged (default easy)
    assert config.get_difficulty("pong") == config.DIFFICULTY_EASY
    assert config.get_difficulty("breakout") == config.DIFFICULTY_EASY
    assert config.get_difficulty("space_invaders") == config.DIFFICULTY_EASY
    assert config.get_difficulty("tetris") == config.DIFFICULTY_EASY
