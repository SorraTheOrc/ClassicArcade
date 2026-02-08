import importlib

from menu_items import discover_games


def test_discover_includes_space_invaders():
    items = discover_games()
    # Make a mapping name -> class for easier assertions
    names = [name for name, _ in items]
    assert "Space Invaders" in names


def test_discover_ignores_non_game_modules(tmp_path, monkeypatch):
    # Create a fake module under games that does not define a State subclass
    # We'll inject it into sys.modules so pkgutil can find it during discovery.
    module_name = "games._fake_helper"
    spec = importlib.util.spec_from_loader(module_name, loader=None)
    fake_mod = importlib.util.module_from_spec(spec)
    # Put a dummy attribute but no State subclass
    fake_mod.__dict__["SOME_CONST"] = 1
    import sys

    sys.modules[module_name] = fake_mod

    try:
        items = discover_games()
        names = [name for name, _ in items]
        assert "_Fake Helper" not in names
    finally:
        del sys.modules[module_name]
