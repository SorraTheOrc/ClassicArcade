"""Utility module providing the list of menu items for the arcade engine.

The function ``get_menu_items`` returns a list of tuples ``(display_name, state_class)``
which the ``MenuState`` uses to build the menu and transition to the appropriate game
state when the user selects an entry.
"""

import importlib
import inspect
import logging
import os
import pkgutil
from typing import Callable, List, Tuple, Type, Union

from classic_arcade.engine import State

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


def discover_games() -> List[Tuple[str, object, str | None]]:
    """Dynamically discover game modules in the `games` package.

    Scans `games` for submodules, imports each one and looks for either:
    - a callable ``run`` function (preferred for launching)
    - or a concrete subclass of ``engine.State`` (fallback, but will be disabled if ``run`` is missing).

    Packages that define neither are still added as disabled entries.

    Returns a list of ``(display_name, launch_target, icon_path)`` tuples where
    ``launch_target`` is a callable ``run`` function if available, otherwise ``None``
    to indicate a disabled entry.
    """
    items: List[Tuple[str, object, str | None]] = []
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

    import os as _os

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
                logger.debug(
                    "Unable to iterate submodules of %s", full_name, exc_info=True
                )

        # Determine if a callable run function exists in any candidate module
        run_callable = None
        for mod in candidates:
            if hasattr(mod, "run") and callable(getattr(mod, "run")):
                run_callable = getattr(mod, "run")
                break

        # Determine friendly display name (prefer State subclass name if present)
        state_cls = None
        for mod in candidates:
            for _, obj in inspect.getmembers(mod, inspect.isclass):
                if obj.__module__ != mod.__name__:
                    continue
                try:
                    if issubclass(obj, State) and obj is not State:
                        # Skip mode-specific states that shouldn't appear as separate menu entries
                        if not (
                            obj.__name__.startswith("PongSinglePlayer")
                            or obj.__name__.startswith("PongMultiplayer")
                            or obj.__name__.startswith("SnakeMode")
                            or obj.__name__.startswith("Snake2Player")
                            or obj.__name__.startswith("TetrisMode")
                            or obj.__name__.startswith("Tetris2Player")
                        ):
                            state_cls = obj
                            break
                except Exception:
                    continue
            if state_cls:
                break

        display_name = _friendly_name_from_module(
            name, getattr(state_cls, "__name__", None) if state_cls else None
        )

        # For Pong, use the module name instead of state class name
        if name == "pong":
            display_name = "Pong"

        # Determine icon path for the module
        import os

        icon_path = None
        if hasattr(module, "__path__"):
            package_dir = module.__path__[0]
        else:
            package_dir = _os.path.dirname(getattr(module, "__file__", ""))
        if not _os.path.isdir(package_dir):
            continue
        png_path = os.path.join(package_dir, "icon.png")
        svg_path = os.path.join(package_dir, "icon.svg")
        if os.path.isfile(png_path):
            icon_path = png_path
        elif os.path.isfile(svg_path):
            icon_path = svg_path

        # Use the run callable as launch target if available; otherwise entry is disabled
        launch_target = run_callable if run_callable is not None else None
        # If no run() was found, warn so maintainers know this entry will be disabled
        if run_callable is None:
            logger.warning(
                "Game package %s does not define a callable run(); menu entry will be disabled",
                full_name,
            )
        items.append((display_name, launch_target, icon_path))

    if not items:
        logger.warning("No games discovered; falling back to explicit import list")
        fallback_modules = (
            "games.breakout",
            "games.pong",
            "games.snake",
            "games.tetris",
            "games.space_invaders",
        )
        for full_name in fallback_modules:
            try:
                module = importlib.import_module(full_name)
            except Exception:
                logger.debug("Fallback import failed for %s", full_name, exc_info=True)
                continue

            candidates = [module]
            if hasattr(module, "__path__"):
                try:
                    for _, subname, _ in pkgutil.iter_modules(module.__path__):
                        try:
                            submod = importlib.import_module(f"{full_name}.{subname}")
                            candidates.append(submod)
                        except Exception:
                            logger.debug(
                                "Fallback import failed for %s.%s",
                                full_name,
                                subname,
                                exc_info=True,
                            )
                except Exception:
                    logger.debug(
                        "Fallback unable to iterate submodules of %s",
                        full_name,
                        exc_info=True,
                    )

            run_callable = None
            for mod in candidates:
                if hasattr(mod, "run") and callable(getattr(mod, "run")):
                    run_callable = getattr(mod, "run")
                    break

            state_cls = None
            for mod in candidates:
                for _, obj in inspect.getmembers(mod, inspect.isclass):
                    if obj.__module__ != mod.__name__:
                        continue
                    try:
                        if issubclass(obj, State) and obj is not State:
                            if not (
                                obj.__name__.startswith("PongSinglePlayer")
                                or obj.__name__.startswith("PongMultiplayer")
                            ):
                                state_cls = obj
                                break
                    except Exception:
                        continue
                if state_cls:
                    break

            module_name = full_name.split(".")[-1]
            display_name = _friendly_name_from_module(
                module_name, getattr(state_cls, "__name__", None) if state_cls else None
            )
            if module_name == "pong":
                display_name = "Pong"

            icon_path = None
            if hasattr(module, "__path__"):
                package_dir = module.__path__[0]
            else:
                package_dir = _os.path.dirname(getattr(module, "__file__", ""))
            if _os.path.isdir(package_dir):
                png_path = _os.path.join(package_dir, "icon.png")
                svg_path = _os.path.join(package_dir, "icon.svg")
                if _os.path.isfile(png_path):
                    icon_path = png_path
                elif _os.path.isfile(svg_path):
                    icon_path = svg_path

            launch_target = run_callable if run_callable is not None else None
            if run_callable is None:
                logger.warning(
                    "Game package %s does not define a callable run(); menu entry will be disabled",
                    full_name,
                )
            items.append((display_name, launch_target, icon_path))

    # Sort alphabetically by display name
    items.sort(key=lambda t: t[0].lower())
    return items


def get_menu_items() -> List[Tuple[str, object, str | None]]:
    """Return menu items as ``(name, state_class)`` tuples.

    The menu is populated by scanning the ``games`` package at runtime so new
    games can be added without modifying this file. The Settings entry is always
    appended as the last (non-game) option.
    """
    items = discover_games()

    # Log discovered game names (INFO level)
    if items:
        logger.info("Discovered games: %s", ", ".join(name for name, _, _ in items))
    else:
        logger.info("No games discovered")

    # Always ensure Settings is present as the last menu item.
    try:
        settings_mod = importlib.import_module("games.settings")
        SettingsState = getattr(settings_mod, "SettingsState")
        settings_icon_path = None
        icon_candidate = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "assets",
            "icons",
            "settings_icon.png",
        )
        if os.path.isfile(icon_candidate):
            settings_icon_path = icon_candidate
        items.append(("Settings", SettingsState, settings_icon_path))
    except Exception:
        logger.debug(
            "SettingsState not available; skipping Settings menu entry", exc_info=True
        )

    return items


__all__ = ["get_menu_items", "discover_games"]
