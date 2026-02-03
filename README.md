# Classic Arcade Suite (Pygame)

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
2. Install the required dependency:

```bash
pip install pygame
```

3. Clone the repository (if you haven't already) and navigate to the project directory.

## Running the Arcade Suite

Run the main entry point:

```bash
python main.py
```

You will see a loading screen with a list of games. Use the **Up/Down** arrow keys to navigate, press **Enter** to launch a game, and **Esc** to quit.

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


## License

This project is released under the MIT License.
