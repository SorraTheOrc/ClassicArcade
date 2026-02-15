"""Alien mod loader for Space Invaders Redux.

This module handles the discovery and loading of alien mods from the mods/ directory.
It supports both Python-based mods (with custom alien classes) and YAML-based mods
(configuration only).

The loader:
1. Scans the mods/ directory for mod folders
2. For Python mods: imports the module and looks for AlienBase subclasses
3. For YAML mods: parses the configuration and creates a simple Alien implementation
4. Caches loaded mods for performance
"""

import importlib.util
import logging
import os
import pathlib
import sys
from typing import Any, Optional, Type

import pygame

from classic_arcade.utils import BLACK, BLUE, GREEN, RED, WHITE, YELLOW

from .alien_base import AlienBase

logger = logging.getLogger(__name__)

# Directory containing user mods
MODS_DIR = pathlib.Path(__file__).parent.parent.parent / "mods"
DEFAULT_ALIEN_TYPES = {
    "classic_red": (RED, 0.4),
    "classic_green": (GREEN, 0.3),
    "classic_blue": (BLUE, 0.2),
    "classic_yellow": (YELLOW, 0.1),
}


def get_mods_dir() -> pathlib.Path:
    """Get the path to the mods directory.

    Returns:
        Path to the mods directory
    """
    return MODS_DIR


def is_valid_mod_dir(path: pathlib.Path) -> bool:
    """Check if a directory is a valid mod directory.

    A valid mod directory must contain:
    - __init__.py (for Python modules) or
    - level.yaml (for configuration-only mods)

    Args:
        path: Path to check

    Returns:
        True if the directory is a valid mod, False otherwise
    """
    if not path.is_dir():
        return False

    # Check for required files
    has_init = (path / "__init__.py").exists()
    has_level_yaml = (path / "level.yaml").exists()

    return has_init or has_level_yaml


def load_python_mod(mod_dir: pathlib.Path) -> Optional[Type[AlienBase]]:
    """Load a Python mod directory and return its AlienBase subclass.

    Args:
        mod_dir: Path to the Python mod directory

    Returns:
        The AlienBase subclass if found, None otherwise
    """
    init_file = mod_dir / "__init__.py"
    if not init_file.exists():
        logger.warning("No __init__.py found in mod directory %s", mod_dir)
        return None

    # Use a package name that includes 'mods.' prefix
    mod_name = f"mods.{mod_dir.name}"
    spec = importlib.util.spec_from_file_location(mod_name, init_file)
    if spec is None or spec.loader is None:
        logger.warning("Could not create spec for mod %s", mod_name)
        return None

    try:
        module = importlib.util.module_from_spec(spec)
        sys.modules[mod_name] = module
        spec.loader.exec_module(module)
    except Exception as e:
        logger.warning("Failed to load mod %s: %s", mod_name, e)
        return None

    # Look for AlienBase subclasses in the module
    for name in dir(module):
        obj = getattr(module, name)
        if isinstance(obj, type):
            # Check if it's a subclass of AlienBase but not AlienBase itself
            # and has no abstract methods (meaning it's fully implemented)
            is_subclass = issubclass(obj, AlienBase) and obj is not AlienBase
            has_no_abstract = not getattr(obj, "__abstractmethods__", None)

            if is_subclass and has_no_abstract:
                return obj

    logger.warning("No AlienBase subclass found in mod %s", mod_name)
    return None


def load_yaml_mod_config(mod_path: pathlib.Path) -> Optional[dict[str, Any]]:
    """Load a YAML mod configuration file.

    Args:
        mod_path: Path to the mod directory

    Returns:
        The parsed YAML config as a dict, or None if loading failed
    """
    try:
        import yaml
    except ImportError:
        logger.warning("PyYAML not installed, YAML mods not supported")
        return None

    level_yaml_path = mod_path / "level.yaml"
    if not level_yaml_path.exists():
        return None

    try:
        with open(level_yaml_path, "r") as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        logger.warning("Failed to load YAML config from %s: %s", level_yaml_path, e)
        return None


def create_simple_alien_class(color: tuple[int, int, int]) -> Type[AlienBase]:
    """Create a simple AlienBase subclass for YAML-based mods.

    Args:
        color: RGB tuple for the alien's color

    Returns:
        A new AlienBase subclass
    """
    color_rgb = color if isinstance(color, tuple) else tuple(color)

    class SimpleAlien(AlienBase):
        """Simple alien with basic rectangular rendering."""

        DEFAULT_COLOR = color_rgb

        def __init__(self, x: int, y: int, width: int, height: int):
            super().__init__(x, y, width, height)

        def move(self, dt: float, direction: int) -> None:
            """Move the alien horizontally."""
            move_x = self.speed * direction * dt * 60
            self._fractional_x += move_x
            integer_move = int(self._fractional_x)
            self._fractional_x -= integer_move
            self.rect.move_ip(integer_move, 0)

        def draw(self, screen: pygame.Surface) -> None:
            """Draw a colored rectangle for the alien."""
            pygame.draw.rect(screen, self.color, self.rect)
            # Draw simple eyes
            eye_color = BLACK
            eye_width = self.rect.width // 5
            eye_height = self.rect.height // 6
            pygame.draw.rect(
                screen,
                eye_color,
                (self.rect.x + 5, self.rect.y + 5, eye_width, eye_height),
            )
            pygame.draw.rect(
                screen,
                eye_color,
                (
                    self.rect.x + self.rect.width - 5 - eye_width,
                    self.rect.y + 5,
                    eye_width,
                    eye_height,
                ),
            )

        def get_rect(self) -> pygame.Rect:
            """Return the alien's bounding rectangle."""
            return self.rect

    return SimpleAlien


class ModLoader:
    """Loader for Space Invaders Redux mods.

    This class handles discovering and loading alien mods from the mods/ directory.
    It supports both Python-based mods (with custom alien classes) and YAML-based
    mods (configuration only).
    """

    def __init__(self, mods_dir: Optional[pathlib.Path] = None):
        """Initialize the mod loader.

        Args:
            mods_dir: Path to the mods directory. Defaults to MODS_DIR
        """
        self.mods_dir = mods_dir or get_mods_dir()
        self._loaded_mods: dict[str, Type[AlienBase]] = {}
        self._yaml_configs: dict[str, dict[str, Any]] = {}
        self._mod_paths: dict[str, pathlib.Path] = {}

    def discover_mods(self) -> list[str]:
        """Discover all valid mods in the mods directory.

        Returns:
            List of mod names that were discovered
        """
        if not self.mods_dir.exists():
            logger.info("Mods directory does not exist: %s", self.mods_dir)
            return []

        mod_names = []
        for item in self.mods_dir.iterdir():
            if is_valid_mod_dir(item):
                mod_name = item.name
                mod_names.append(mod_name)
                self._mod_paths[mod_name] = item
                logger.debug("Discovered mod: %s at %s", mod_name, item)

        return mod_names

    def load_mod(self, mod_name: str) -> Optional[Type[AlienBase]]:
        """Load a specific mod by name.

        Args:
            mod_name: Name of the mod to load

        Returns:
            The AlienBase subclass if found, None otherwise
        """
        if mod_name in self._loaded_mods:
            return self._loaded_mods[mod_name]

        mod_path = self._mod_paths.get(mod_name)
        if mod_path is None:
            logger.warning("Mod not discovered: %s", mod_name)
            return None

        # Try loading as Python mod first
        python_file = mod_path / "__init__.py"
        if python_file.exists():
            alien_class = load_python_mod(mod_path)
            if alien_class is not None:
                self._loaded_mods[mod_name] = alien_class
                return alien_class

        # Try loading as YAML mod
        yaml_config = load_yaml_mod_config(mod_path)
        if yaml_config is not None:
            self._yaml_configs[mod_name] = yaml_config
            # Create a simple alien class from the config
            # Use the first color defined in the config, or default to red
            default_color = yaml_config.get("default_color", RED)
            alien_class = create_simple_alien_class(default_color)
            self._loaded_mods[mod_name] = alien_class
            return alien_class

        logger.warning("Could not load mod %s (no valid alien definition)", mod_name)
        return None

    def load_all_mods(self) -> dict[str, Type[AlienBase]]:
        """Load all discovered mods.

        Returns:
            Dict mapping mod names to their AlienBase subclasses
        """
        self.discover_mods()
        loaded = {}
        for mod_name in self._mod_paths:
            alien_class = self.load_mod(mod_name)
            if alien_class is not None:
                loaded[mod_name] = alien_class
        return loaded

    def get_alien_class(self, mod_name: str) -> Optional[Type[AlienBase]]:
        """Get an AlienBase subclass by mod name without loading.

        Args:
            mod_name: Name of the mod

        Returns:
            The AlienBase subclass if loaded, None otherwise
        """
        return self._loaded_mods.get(mod_name)

    def get_yaml_config(self, mod_name: str) -> Optional[dict[str, Any]]:
        """Get the YAML config for a mod.

        Args:
            mod_name: Name of the mod

        Returns:
            The YAML config dict if loaded, None otherwise
        """
        return self._yaml_configs.get(mod_name)


# Global mod loader instance
_mod_loader: Optional[ModLoader] = None


def get_mod_loader() -> ModLoader:
    """Get the global mod loader instance.

    Returns:
        The global ModLoader instance
    """
    global _mod_loader
    if _mod_loader is None:
        _mod_loader = ModLoader()
    return _mod_loader


def load_alien_types() -> dict[str, Type[AlienBase]]:
    """Load all alien types from mods.

    Returns:
        Dict mapping alien type names to their AlienBase subclasses
    """
    loader = get_mod_loader()
    return loader.load_all_mods()
