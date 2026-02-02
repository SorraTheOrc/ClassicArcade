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
│   ├── __init__.py       # Package marker
│   ├── snake.py          # Snake game
│   ├── pong.py           # Pong game
│   ├── breakout.py       # Breakout game
│   ├── space_invaders.py # Space Invaders game
│   └── tetris.py         # Tetris game
└── README.md
```

## License

This project is released under the MIT License.
