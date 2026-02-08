"""Utility module providing the list of menu items for the arcade engine.

The function ``get_menu_items`` returns a list of tuples ``(display_name, state_class)``
which the ``MenuState`` uses to build the menu and transition to the appropriate game
state when the user selects an entry.
"""

import importlib
import inspect
import logging
import pkgutil
from typing import List, Tuple, Type

from engine import State

logger = logging.getLogger(__name__)


def _friendly_name_from_module(module_name: str, cls_name: str | None = None) -> str:
    """Create a display name for a menu entry.

    Prefer a class name that ends with 'State' (stripping the suffix), otherwise
    fall back to the module name (underscores -> spaces, titlecased).
    """
    if cls_name and cls_name.endswith("State"):
        base = cls_name[: -len("State")]
        # If the class name uses underscores prefer those, otherwise split CamelCase
        if "_" in base:
            return base.replace("_", " ").strip()
        # Insert spaces between camelcase boundaries: e.g. SpaceInvaders -> Space Invaders
        import re

        split = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", base)
        return split.strip()
    # module_name is like 'space_invaders' -> 'Space Invaders'
    return module_name.replace("_", " ").title()


def discover_games() -> List[Tuple[str, Type[State]]]:
    """Dynamically discover game modules in the `games` package.

    Scans `games` for submodules, imports each one and looks for classes that are
    subclasses of ``engine.State``. Modules that do not define a concrete State
    subclass are ignored.

    Returns a list of ``(display_name, state_class)`` tuples.
    """
    items: List[Tuple[str, Type[State]]] = []
    try:
        import games

        package_path = games.__path__
    except Exception:
        logger.exception("Unable to import games package for discovery")
        return items

    # Exclude internal/non-game modules
    excluded = {
        "__init__",
        "game_base",
        "run_helper",
        "settings",
        "highscore",
        "splash",
    }

    for finder, name, ispkg in pkgutil.iter_modules(package_path):
        if name in excluded or name.startswith("._"):
            continue
        full_name = f"games.{name}"
        try:
            module = importlib.import_module(full_name)
        except Exception:
            logger.debug("Failed to import %s, skipping", full_name, exc_info=True)
            continue

        # Collect candidate modules to inspect: the module itself, plus any submodules if
        # the entry is a package (e.g. games.space_invaders.space_invaders).
        candidates = [module]
        if ispkg:
            try:
                for _, subname, _ in pkgutil.iter_modules(module.__path__):
                    try:
                        submod = importlib.import_module(f"{full_name}.{subname}")
                        candidates.append(submod)
                    except Exception:
                        logger.debug(
                            "Failed to import submodule %s.%s, skipping",
                            full_name,
                            subname,
                            exc_info=True,
                        )
            except Exception:
                # Some packages may not expose __path__ or be importable in this way
                logger.debug(
                    "Unable to iterate submodules of %s", full_name, exc_info=True
                )

        # Find classes defined in any candidate module that subclass engine.State
        state_cls = None
        for mod in candidates:
            for _, obj in inspect.getmembers(mod, inspect.isclass):
                # Prefer classes defined in the inspected module
                if obj.__module__ != mod.__name__:
                    continue
                try:
                    if issubclass(obj, State) and obj is not State:
                        state_cls = obj
                        break
                except Exception:
                    continue
            if state_cls:
                break

        if state_cls is None:
            # No State subclass found; ignore this module
            continue

        display_name = _friendly_name_from_module(
            name, getattr(state_cls, "__name__", None)
        )
        items.append((display_name, state_cls))

    # Sort alphabetically by display name
    items.sort(key=lambda t: t[0].lower())
    return items


def get_menu_items() -> List[Tuple[str, Type[State]]]:
    """Return menu items as ``(name, state_class)`` tuples.

    The menu is populated by scanning the ``games`` package at runtime so new
    games can be added without modifying this file. The Settings entry is always
    appended as the last (non-game) option.
    """
    items = discover_games()

    # Always ensure Settings is present as the last menu item.
    try:
        settings_mod = importlib.import_module("games.settings")
        SettingsState = getattr(settings_mod, "SettingsState")
        items.append(("Settings", SettingsState))
    except Exception:
        logger.debug(
            "SettingsState not available; skipping Settings menu entry", exc_info=True
        )

    return items
