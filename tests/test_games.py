"""Tests for game state classes.

Each game state is instantiated, updated for a few frames, and drawn to a dummy surface.
The tests ensure that no exceptions are raised during a short headless run.
"""

import os

# Ensure headless mode for pygame (dummy video driver) before importing pygame
os.environ["HEADLESS"] = "1"
# Optionally set SDL_VIDEODRIVER to dummy
os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame

import config

# Initialize pygame before importing game modules that may set up display
pygame.init()
pygame.font.init()

from engine import MenuState
from games.breakout import BreakoutState
from games.pong import PongMultiplayerState, PongSinglePlayerState
from games.settings import SettingsState
from games.snake import SnakeState
from games.space_invaders import SpaceInvadersState
from games.tetris import TetrisState
from menu_items import get_menu_items


def run_state(state_class):
    """Instantiate a game state, run a short loop and draw.

    Returns the instantiated state for further inspection if needed.
    """
    state = state_class()
    # Dummy surface
    screen = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    dt = 1.0 / 60.0
    for _ in range(10):
        # No events are sent; handle_event would be called by engine normally.
        state.update(dt)
        state.draw(screen)
    return state


def test_snake_state():
    run_state(SnakeState)


def test_pong_single_player_state():
    run_state(PongSinglePlayerState)


def test_pong_multiplayer_state():
    run_state(PongMultiplayerState)


def test_breakout_state():
    run_state(BreakoutState)


def test_space_invaders_state():
    run_state(SpaceInvadersState)


def test_tetris_state():
    run_state(TetrisState)


def test_settings_state():
    run_state(SettingsState)


def test_menu_state():
    # MenuState expects a list of menu items
    menu_items = get_menu_items()
    menu_state = MenuState(menu_items)
    screen = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    dt = 1.0 / 60.0
    for _ in range(10):
        menu_state.update(dt)
        menu_state.draw(screen)
    # Ensure that the menu can handle navigation without errors
    # Simulate pressing down and up keys via handle_event
    down_event = pygame.event.Event(pygame.KEYDOWN, key=config.KEY_DOWN)
    up_event = pygame.event.Event(pygame.KEYDOWN, key=config.KEY_UP)
    menu_state.handle_event(down_event)
    menu_state.handle_event(up_event)
    assert True
