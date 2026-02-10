"""Tests for the Help/controls screen.

Verifies that the help screen displays controls for all games
and transitions correctly when pressing H or ESC.
"""

import os

os.environ["HEADLESS"] = "1"

import pygame

pygame.init()

from engine import Engine, HelpState, MenuState


def test_help_state_exists():
    """Verify HelpState class is exported from engine module."""
    assert HelpState is not None


def test_help_state_initialization():
    """Test that HelpState initializes without errors."""
    help_state = HelpState()
    assert help_state.title_font_size == 48
    assert help_state.item_font_size == 24
    assert help_state.next_state is None


def test_help_state_esc_returns_to_menu():
    """Test that HelpState transitions to menu on ESC key."""
    help_state = HelpState()
    help_state.next_state = None

    # The handle_event imports get_menu_items locally, so we just verify
    # that the key event is handled without raising an exception
    event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)

    # Should not raise any exception
    help_state.handle_event(event)

    # Transition should be requested (will be a MenuState instance)
    assert help_state.next_state is not None
    assert isinstance(help_state.next_state, MenuState)


def test_help_state_h_returns_to_menu():
    """Test that HelpState transitions to menu on H key."""
    help_state = HelpState()
    help_state.next_state = None

    # Simulate H key event
    event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_h)

    # Should not raise any exception
    help_state.handle_event(event)

    # Transition should be requested
    assert help_state.next_state is not None
    assert isinstance(help_state.next_state, MenuState)


def test_help_state_update_no_error():
    """Test that HelpState.update() runs without errors."""
    help_state = HelpState()
    # Should not raise any exception
    help_state.update(1.0 / 60)


def test_help_state_draw_no_error():
    """Test that HelpState.draw() runs without errors."""
    help_state = HelpState()
    # Create a dummy surface for drawing
    screen = pygame.Surface((640, 480))
    # Should not raise any exception
    help_state.draw(screen)


def test_help_state_get_all_controls():
    """Test that HelpState can collect controls from all games."""
    help_state = HelpState()

    controls = help_state._get_all_controls()

    # Should have controls for at least some games
    assert isinstance(controls, list)
    assert len(controls) >= 1

    # Each entry should be a tuple of (game_name, control_lines)
    for game_name, control_lines in controls:
        assert isinstance(game_name, str)
        assert isinstance(control_lines, list)
        assert len(control_lines) >= 1


def test_snake_get_controls():
    """Test that SnakeState has get_controls() method."""
    from games.snake.snake import SnakeState

    controls = SnakeState.get_controls()
    assert isinstance(controls, list)
    assert len(controls) >= 1
    # Check for expected control descriptions
    control_text = "\n".join(controls)
    assert "Arrow keys" in control_text
    assert "ESC" in control_text


def test_pong_single_player_get_controls():
    """Test that PongSinglePlayerState has get_controls() method."""
    from games.pong.pong import PongSinglePlayerState

    controls = PongSinglePlayerState.get_controls()
    assert isinstance(controls, list)
    assert len(controls) >= 1
    control_text = "\n".join(controls)
    assert "W/S" in control_text or "Up/Down" in control_text
    assert "ESC" in control_text


def test_pong_multiplayer_get_controls():
    """Test that PongMultiplayerState has get_controls() method."""
    from games.pong.pong import PongMultiplayerState

    controls = PongMultiplayerState.get_controls()
    assert isinstance(controls, list)
    assert len(controls) >= 1
    control_text = "\n".join(controls)
    assert "Player" in control_text
    assert "ESC" in control_text


def test_breakout_get_controls():
    """Test that BreakoutState has get_controls() method."""
    from games.breakout.breakout import BreakoutState

    controls = BreakoutState.get_controls()
    assert isinstance(controls, list)
    assert len(controls) >= 1
    control_text = "\n".join(controls)
    assert "Left/Right" in control_text
    assert "ESC" in control_text


def test_space_invaders_get_controls():
    """Test that Space Invaders has controls in module docstring."""
    from games.space_invaders import space_invaders

    doc = space_invaders.__doc__
    assert doc is not None
    assert "Controls:" in doc
    assert "Left/Right" in doc
    assert "Space" in doc
    assert "ESC" in doc


def test_tetris_get_controls():
    """Test that Tetris has controls in module docstring."""
    from games.tetris import tetris

    doc = tetris.__doc__
    assert doc is not None
    assert "Controls:" in doc
    assert "Left/Right" in doc
    assert "Up" in doc
    assert "ESC" in doc
