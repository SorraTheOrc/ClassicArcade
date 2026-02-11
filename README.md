# Classic Arcade Suite (Pygame)

[![CI](https://github.com/SorraTheOrc/ClassicArcade/actions/workflows/ci.yml/badge.svg)](https://github.com/SorraTheOrc/ClassicArcade/actions/workflows/ci.yml) [![Coverage](https://img.shields.io/badge/coverage-100%25-brightgreen)](https://github.com/SorraTheOrc/ClassicArcade/actions/workflows/ci.yml) [![PyPI version](https://img.shields.io/pypi/v/classic-arcade)](https://pypi.org/project/classic-arcade/)

A collection of five classic arcade games implemented in Python using **Pygame**:

- **Snake**
- **Pong**
- **Breakout**
- **Space Invaders**
- **Tetris**

The project includes a simple loading screen (menu) that lets you select any game to play.

## Features

- Each game is a standalone module with its own controls.
- Simple graphics using only basic shapes and colors (no external assets).
- Restart a game after a game over and return to the main menu.
- Adjustable difficulty levels (Easy, Medium, Hard) for each game, affecting speed, AI, and spawn rates.
- Works with Python 3.10+ and Pygame 2.x.

## Controls

| Game | Controls |
|------|-----------|
| Snake | Arrow keys – move the snake. `R` – restart after game over. `ESC` – return to menu. |
| Pong | Arrow keys – move left paddle. `R` – restart after game over. `ESC` – return to menu. |
| Breakout | Arrow keys – move paddle. `R` – restart after game over. `ESC` – return to menu. |
| Space Invaders | Arrow keys – move ship. `Space` – fire. `R` – restart after game over. `ESC` – return to menu. |
| Tetris | Arrow keys – move piece left/right. `Up` – rotate. `Down` – soft drop. `R` – restart after game over. `ESC` – return to menu. |

## Installation

1. Ensure you have **Python 3.10** or newer installed.
2. Clone the repository (if you haven't already) and navigate to the project directory.
3. Install the package (including dependencies) with:

```bash
pip install .
```

   *If you only need the pygame library without installing the package, you can run `pip install pygame` instead.*

## Running the Arcade Suite

The arcade suite now features **dynamic game discovery**. On startup the launcher scans the `games/` package for available games. Any sub‑package that defines a concrete ``engine.State`` subclass or provides a callable ``run()`` function is automatically added to the menu. This means you can add new games simply by dropping a new module into the `games/` directory – no code changes are required. The launcher logs the names of all discovered games at INFO level.

## Running the Arcade Suite

You can run the suite using the main entry point:

```bash
python main.py
```

Or, after installing the package, use the installed console script:

```bash
classic-arcade
```

Both commands start the arcade suite and display the loading screen. Use the **Up/Down** arrow keys to navigate, press **Enter** to launch a game, and **Esc** to quit.

## Running Individual Games

Each game is packaged under `games/<name>/` and exposes a `run()` convenience function and the game `State` class for testing. Run a single game from the project root (ensure `pip install pygame` first):

- Using the `run()` export (recommended):

```bash
python -c "from games.pong import run; run()"
```

- Or execute the module directly with `-m`:

```bash
python -m games.pong.pong
```

Replace `pong` with `snake`, `breakout`, `space_invaders`, or `tetris` to run other games. Running from the project root ensures relative imports resolve correctly.

Programmatic usage example (import the state for tests or embedding):

```py
from games.snake import SnakeState
state = SnakeState()
```

## Scrollable Menu (new)

The main menu now supports scrolling when the list of discovered games exceeds the vertical space of the window. A **yellow triangle** appears near the bottom of the screen to indicate that more items are available below the visible area.

### How scrolling works
- The menu builds a grid of square *boxes* (default **160 × 160 px**). The size and spacing can be overridden with the environment variables:
  - `MENU_BOX_SIZE` – side length of each square box (default `160`).
  - `MENU_H_SPACING` – horizontal gap between boxes (default `20`).
  - `MENU_V_SPACING` – vertical gap between boxes (default `20`).
- When the highlighted entry moves off‑screen (using the **Up/Down** arrow keys), the grid automatically scrolls so the selected item stays fully visible.
- The scroll offset is clamped to the range `[0, max_offset]` where `max_offset` is the total height of the grid minus the visible height.
- The visual indicator is a filled yellow triangle (twice the size of the previous arrow) drawn at the bottom‑center of the window.

### Customising the layout
You can experiment with larger icons or tighter spacing without changing source code. For example:

```bash
export MENU_BOX_SIZE=200      # make each box 200 px square
export MENU_H_SPACING=30      # increase horizontal gap
export MENU_V_SPACING=30      # increase vertical gap
python main.py                # run the suite with the new layout
```

The menu will automatically recalculate the grid layout based on these values.

### Debug logging
When you run the suite with `--verbose`, the engine now logs the computed layout parameters (box size, spacing, columns, rows, max_offset, etc.). This helps verify that the scroll calculations are correct.

---

## Menu Icons

Each game can provide a custom icon that appears in the main menu. Place an image named **`icon.png`** (or **`icon.svg`**) in the game's package directory (e.g., `games/snake/`, `games/pong/`). The menu automatically discovers these files during start‑up via the `discover_games` function. 

You can also provide a custom icon for the Settings entry by placing **`settings_icon.png`** (or **`settings_icon.svg`**) in the `assets/icons/` directory. If present, this icon will be used for the Settings menu item, also receiving the deterministic hue shift.

When drawing the menu, the icon is loaded with `pygame.image.load` and **scaled** to fill the square box (default 160 × 160 px) while leaving enough vertical space for the game name. The scaling is performed with `pygame.transform.smoothscale`, ensuring the image fits neatly regardless of its original dimensions. If no icon file is found, a gray placeholder square of the same size is shown.

**Deterministic hue shift:** When an icon (or the shared default icon) is loaded, the menu applies a deterministic hue shift based on the game's display name. This ensures each game’s icon gets a unique, consistent color tint across runs, while still using the original artwork.

The hue offset is computed from a SHA‑256 hash of the name, guaranteeing the same tint every time the menu is displayed.

## Standalone Executables

The arcade suite can be packaged as standalone executables for Windows, macOS, and Linux using PyInstaller. Nightly builds are automatically created and published to GitHub Releases.

### Downloading Builds

Download the latest build for your platform from the [Releases page](https://github.com/SorraTheOrc/ClassicArcade/releases):
- **Windows**: `ClassicArcade-YYYYMMDD-commit-windows-latest.exe`
- **macOS**: `ClassicArcade-YYYYMMDD-commit-macos-latest.app`
- **Linux**: `ClassicArcade-YYYYMMDD-commit-ubuntu-latest.appimage`

Nightly builds are automatically generated for all three platforms and published to GitHub Releases.

### Building Locally

To build a standalone executable locally:

1. Install build dependencies:
   ```bash
   pip install --upgrade build PyInstaller
   ```

2. Build the executable:
   ```bash
   pyinstaller --clean classic-arcade.spec
   ```

3. The executable will be created in `dist/ClassicArcade` (Linux/macOS) or `dist/ClassicArcade.exe` (Windows).

**Note for Windows users:** If `pyinstaller` is not recognized, it may not be on your PATH. Add the Scripts directory to your PATH or run:
```powershell
& "$env:APPDATA\Python\Python313\Scripts\pyinstaller.exe" --clean classic-arcade.spec
```
(Adjust `Python313` to match your Python version)

### Platform-Specific Builds

**Important:** PyInstaller builds are platform-specific. Running the build on Linux produces a Linux executable, on macOS produces a macOS executable, and on Windows produces a Windows executable.

To build for a different platform, you need to run PyInstaller on that platform. For automated cross-platform builds, use the **nightly release workflow** which runs on GitHub's infrastructure:
- Runs on `ubuntu-latest` → produces Linux builds
- Runs on `macos-latest` → produces macOS builds
- Runs on `windows-latest` → produces Windows builds

The nightly workflow automatically builds and publishes all three platform executables to the [Releases page](https://github.com/SorraTheOrc/ClassicArcade/releases).

### Build Artifacts

Each build includes:
- All game modules (Snake, Pong, Breakout, Space Invaders, Tetris)
- All assets (sounds, music, icons)
- Pygame and dependencies

The Linux/macOS executable is a single binary (~39MB). Windows builds produce a standalone `.exe` file.

---

## Project Structure

```
.
├── main.py                # Entry point with menu
├── utils.py               # Shared utilities (colors, draw_text)
├── games/
│   ├── __init__.py        # Package marker
│   ├── snake/
│   │   └── snake.py       # Snake game (package)
│   ├── pong/
│   │   └── pong.py        # Pong game (package)
│   ├── breakout/
│   │   └── breakout.py    # Breakout game (package)
│   ├── space_invaders/
│   │   └── space_invaders.py # Space Invaders game (package)
│   └── tetris/
│       └── tetris.py      # Tetris game (package)
└── README.md
```

## License

This project is released under the MIT License.
