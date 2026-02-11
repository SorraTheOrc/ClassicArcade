import importlib.util

from classic_arcade.engine import State
from classic_arcade.menu_items import discover_games


def test_discover_includes_space_invaders():
    items = discover_games()
    names = [name for name, _, _ in items]
    assert "Space Invaders" in names


def test_discover_ignores_non_game_modules(tmp_path, monkeypatch):
    # Create a fake module under games that does not define a State subclass
    # We'll inject it into sys.modules so pkgutil can find it during discovery.
    module_name = "games._fake_helper"
    spec = importlib.util.spec_from_loader(module_name, loader=None)
    assert spec is not None
    fake_mod = importlib.util.module_from_spec(spec)
    # Put a dummy attribute but no State subclass
    fake_mod.__dict__["SOME_CONST"] = 1
    import sys

    sys.modules[module_name] = fake_mod

    try:
        items = discover_games()
        names = [name for name, _, _ in items]
        assert "_Fake Helper" not in names
    finally:
        del sys.modules[module_name]


def test_discover_finds_state_subclasses():
    """Verify that discover_games correctly identifies State subclasses."""
    items = discover_games()

    # Build a mapping of display names to launch targets
    name_to_target = {
        name: (launch_target, icon_path) for name, launch_target, icon_path in items
    }

    # Check that games with State subclasses are discovered
    expected_games = {
        "Breakout",
        "Pong",
        "Snake",
        "Space Invaders",
        "Tetris",
    }

    discovered = set(name_to_target.keys())
    assert expected_games.issubset(
        discovered
    ), f"Missing games: {expected_games - discovered}"


def test_discover_excludes_internal_modules():
    """Verify that internal modules without State subclasses are excluded."""
    items = discover_games()
    names = [name for name, _, _ in items]

    # These modules should not appear in the menu
    excluded = {
        "Game Base",
        "Highscore",
        "Run Helper",
        "Settings",
        "Splash",
    }

    for name in excluded:
        assert name not in names, f"Internal module '{name}' should be excluded"


def test_discover_provides_run_launch_target():
    """Verify that games with run() functions get the run function as launch target."""
    items = discover_games()

    # Check that all discovered games have a run function as launch target
    for name, launch_target, _ in items:
        # All discovered games should have a run function
        assert launch_target is not None, f"Game '{name}' should have a launch target"
        assert callable(
            launch_target
        ), f"Game '{name}' launch target should be callable"


def test_discover_handles_missing_icons_gracefully():
    """Verify that discover_games handles modules without icons."""
    items = discover_games()

    # All items should have a valid icon_path (None is valid if no icon exists)
    for name, _, icon_path in items:
        # icon_path should be None or a string representing a path
        assert icon_path is None or isinstance(
            icon_path, str
        ), f"Game '{name}' icon_path should be None or str, got {type(icon_path)}"
