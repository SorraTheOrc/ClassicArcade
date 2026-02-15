"""Level loader for Space Invaders Redux.

This module handles parsing YAML level configuration files and creating
alien instances for the game.

Level configuration format (level.yaml):
    rows: 4
    columns: 8
    alien_spacing:
        horizontal: 10
        vertical: 10
    aliens:
        - type: "classic_red"
          probability: 0.4
        - type: "classic_green"
          probability: 0.3
        - type: "classic_blue"
          probability: 0.2
        - type: "classic_yellow"
          probability: 0.1
    alien_size:
        width: 40
        height: 30

The aliens list defines which alien types can appear and their
probability weights. The level loader will randomly select alien
types based on these probabilities when creating the grid.
"""

import logging
import pathlib
from typing import Any, Optional

import pygame

from .alien_base import AlienBase

logger = logging.getLogger(__name__)

# Default level configuration values
DEFAULT_ROWS = 4
DEFAULT_COLUMNS = 8
DEFAULT_HORIZONTAL_SPACING = 10
DEFAULT_VERTICAL_SPACING = 10
DEFAULT_ALIEN_WIDTH = 40
DEFAULT_ALIEN_HEIGHT = 30
DEFAULT_START_X_OFFSET = 0.5  # Center the aliens
DEFAULT_START_Y_OFFSET = 50


def parse_level_yaml(yaml_content: str) -> dict[str, Any]:
    """Parse a YAML level configuration string.

    Args:
        yaml_content: The YAML configuration string

    Returns:
        Parsed configuration as a dictionary

    Raises:
        ValueError: If the YAML is invalid or missing required fields
    """
    try:
        import yaml
    except ImportError:
        raise ImportError(
            "PyYAML is required for YAML level configuration. "
            "Install with: pip install pyyaml"
        )

    try:
        config = yaml.safe_load(yaml_content)
        if config is None:
            config = {}
        return config
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML configuration: {e}")


def load_level_config(level_path: pathlib.Path) -> dict[str, Any]:
    """Load a level configuration from a YAML file.

    Args:
        level_path: Path to the level.yaml file

    Returns:
        Parsed configuration as a dictionary
    """
    if not level_path.exists():
        logger.warning("Level file not found: %s", level_path)
        return {}

    try:
        with open(level_path, "r") as f:
            yaml_content = f.read()
        return parse_level_yaml(yaml_content)
    except Exception as e:
        logger.warning("Failed to load level config from %s: %s", level_path, e)
        return {}


def create_alien_grid(
    rows: int,
    columns: int,
    alien_class: type[AlienBase],
    start_x: int,
    start_y: int,
    horizontal_spacing: int,
    vertical_spacing: int,
    alien_width: int,
    alien_height: int,
) -> list[AlienBase]:
    """Create a grid of alien instances.

    Args:
        rows: Number of rows in the grid
        columns: Number of columns in the grid
        alien_class: The AlienBase subclass to instantiate
        start_x: X position of the first alien
        start_y: Y position of the first alien
        horizontal_spacing: Horizontal spacing between aliens
        vertical_spacing: Vertical spacing between rows
        alien_width: Width of each alien
        alien_height: Height of each alien

    Returns:
        List of AlienBase instances
    """
    aliens = []
    for row in range(rows):
        for col in range(columns):
            x = start_x + col * (alien_width + horizontal_spacing)
            y = start_y + row * (alien_height + vertical_spacing)
            alien = alien_class(x, y, alien_width, alien_height)
            aliens.append(alien)
    return aliens


def get_alien_type_weights(config: dict[str, Any]) -> list[tuple[str, float]]:
    """Get alien type weights from configuration.

    Args:
        config: Level configuration dictionary

    Returns:
        List of (alien_type_name, weight) tuples
    """
    aliens_config = config.get("aliens", [])
    if not aliens_config:
        # Default weights if no configuration provided
        return [
            ("classic_red", 0.4),
            ("classic_green", 0.3),
            ("classic_blue", 0.2),
            ("classic_yellow", 0.1),
        ]

    weights = []
    for alien_entry in aliens_config:
        if isinstance(alien_entry, dict):
            alien_type = alien_entry.get("type", "classic_red")
            probability = alien_entry.get("probability", 0.25)
            weights.append((alien_type, probability))
        elif isinstance(alien_entry, str):
            # Simple string format: "type_name"
            weights.append((alien_entry, 0.25))

    return weights


def select_alien_type(weights: list[tuple[str, float]]) -> str:
    """Select an alien type based on probability weights.

    Args:
        weights: List of (alien_type_name, weight) tuples

    Returns:
        Selected alien type name
    """
    import random

    if not weights:
        return "classic_red"

    total_weight = sum(weight for _, weight in weights)
    if total_weight == 0:
        return weights[0][0]

    # Normalize weights
    normalized = [(name, weight / total_weight) for name, weight in weights]

    # Select based on weights
    r = random.random()
    cumulative = 0.0
    for name, weight in normalized:
        cumulative += weight
        if r <= cumulative:
            return name

    return normalized[-1][0]


class LevelLoader:
    """Loader for Space Invaders Redux levels.

    This class handles loading level configurations and creating
    alien instances based on the configuration.
    """

    def __init__(self, mods_dir: Optional[pathlib.Path] = None):
        """Initialize the level loader.

        Args:
            mods_dir: Path to the mods directory. Defaults to MODS_DIR
        """
        from .alien_loader import get_mods_dir

        self.mods_dir = mods_dir or get_mods_dir()
        self._level_configs: dict[str, dict[str, Any]] = {}
        self._aliens_cache: dict[str, list[AlienBase]] = {}

    def load_level_config(self, mod_name: str) -> dict[str, Any]:
        """Load level configuration for a specific mod.

        Args:
            mod_name: Name of the mod

        Returns:
            Parsed level configuration dictionary
        """
        if mod_name in self._level_configs:
            return self._level_configs[mod_name]

        mod_path = self.mods_dir / mod_name
        level_yaml_path = mod_path / "level.yaml"

        if not level_yaml_path.exists():
            logger.warning("No level.yaml found for mod %s", mod_name)
            config = {}
        else:
            config = load_level_config(level_yaml_path)

        self._level_configs[mod_name] = config
        return config

    def create_aliens(
        self,
        mod_name: str,
        alien_class: type[AlienBase],
        alien_weights: Optional[list[tuple[str, float]]] = None,
    ) -> list[AlienBase]:
        """Create aliens for a level based on configuration.

        Args:
            mod_name: Name of the mod
            alien_class: The AlienBase subclass to use
            alien_weights: Optional list of (type_name, weight) tuples

        Returns:
            List of AlienBase instances
        """
        config = self.load_level_config(mod_name)

        # Get configuration values with defaults
        rows = config.get("rows", DEFAULT_ROWS)
        columns = config.get("columns", DEFAULT_COLUMNS)
        horizontal_spacing = config.get("alien_spacing", {}).get(
            "horizontal", DEFAULT_HORIZONTAL_SPACING
        )
        vertical_spacing = config.get("alien_spacing", {}).get(
            "vertical", DEFAULT_VERTICAL_SPACING
        )
        alien_width = config.get("alien_size", {}).get("width", DEFAULT_ALIEN_WIDTH)
        alien_height = config.get("alien_size", {}).get("height", DEFAULT_ALIEN_HEIGHT)
        start_y = config.get("start_y", DEFAULT_START_Y_OFFSET)

        # Calculate start_x to center the aliens
        total_width = columns * (alien_width + horizontal_spacing) - horizontal_spacing
        from classic_arcade.utils import SCREEN_WIDTH

        start_x = int((SCREEN_WIDTH - total_width) * DEFAULT_START_X_OFFSET)

        # Create the grid
        aliens = create_alien_grid(
            rows=rows,
            columns=columns,
            alien_class=alien_class,
            start_x=start_x,
            start_y=start_y,
            horizontal_spacing=horizontal_spacing,
            vertical_spacing=vertical_spacing,
            alien_width=alien_width,
            alien_height=alien_height,
        )

        # Cache the result
        cache_key = f"{mod_name}:{alien_class.__name__}"
        self._aliens_cache[cache_key] = aliens

        return aliens

    def create_aliens_with_types(
        self,
        mod_name: str,
        alien_loader: Any,
        fallback_alien_class: Optional[type[AlienBase]] = None,
    ) -> list[AlienBase]:
        """Create aliens with different types based on level configuration.

        Args:
            mod_name: Name of the mod
            alien_loader: ModLoader instance to get alien classes
            fallback_alien_class: Alien class to use when type not found (defaults to mod's class)

        Returns:
            List of AlienBase instances with varying types
        """
        config = self.load_level_config(mod_name)
        weights = get_alien_type_weights(config)

        rows = config.get("rows", DEFAULT_ROWS)
        columns = config.get("columns", DEFAULT_COLUMNS)
        horizontal_spacing = config.get("alien_spacing", {}).get(
            "horizontal", DEFAULT_HORIZONTAL_SPACING
        )
        vertical_spacing = config.get("alien_spacing", {}).get(
            "vertical", DEFAULT_VERTICAL_SPACING
        )
        alien_width = config.get("alien_size", {}).get("width", DEFAULT_ALIEN_WIDTH)
        alien_height = config.get("alien_size", {}).get("height", DEFAULT_ALIEN_HEIGHT)
        start_y = config.get("start_y", DEFAULT_START_Y_OFFSET)

        # Calculate start_x to center the aliens
        total_width = columns * (alien_width + horizontal_spacing) - horizontal_spacing
        from classic_arcade.utils import SCREEN_WIDTH

        start_x = int((SCREEN_WIDTH - total_width) * DEFAULT_START_X_OFFSET)

        # Use fallback alien class if not provided
        if fallback_alien_class is None:
            from .alien_loader import create_simple_alien_class

            fallback_alien_class = create_simple_alien_class((255, 0, 0))

        # Get row-specific alien types from config
        row_types = {}
        aliens_config = config.get("aliens", [])
        for entry in aliens_config:
            if isinstance(entry, dict) and "row" in entry:
                row = entry.get("row")
                alien_type = entry.get("type")
                row_types[row] = alien_type

        # Create aliens with selected types (one type per row)
        aliens = []
        for row in range(rows):
            # Get alien type for this row from config, or use fallback
            if row in row_types:
                alien_type = row_types[row]
                alien_class = alien_loader.get_alien_class(alien_type)
            else:
                alien_class = fallback_alien_class

            if alien_class is None:
                alien_class = fallback_alien_class

            for col in range(columns):
                x = start_x + col * (alien_width + horizontal_spacing)
                y = start_y + row * (alien_height + vertical_spacing)
                alien = alien_class(x, y, alien_width, alien_height)
                aliens.append(alien)

        return aliens


def load_level(
    mod_name: str,
    alien_class: type[AlienBase],
    mods_dir: Optional[pathlib.Path] = None,
) -> list[AlienBase]:
    """Load a level and create aliens for it.

    This is a convenience function that creates a LevelLoader
    and uses it to create aliens.

    Args:
        mod_name: Name of the mod
        alien_class: The AlienBase subclass to use
        mods_dir: Path to the mods directory

    Returns:
        List of AlienBase instances
    """
    loader = LevelLoader(mods_dir)
    return loader.create_aliens(mod_name, alien_class)
