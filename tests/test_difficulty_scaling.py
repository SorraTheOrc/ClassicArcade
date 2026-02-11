# tests/test_difficulty_scaling.py
"""Tests for difficulty scaling functions across games.

These tests ensure that the per‑game scaling functions correctly adjust the
global speed/parameter constants based on the difficulty setting stored in
``config``.
"""

import importlib

from classic_arcade import config

# Helper to reset config difficulties to easy after each test


def reset_difficulties():
    config.SNAKE_DIFFICULTY = config.DIFFICULTY_EASY
    config.PONG_DIFFICULTY = config.DIFFICULTY_EASY
    config.BREAKOUT_DIFFICULTY = config.DIFFICULTY_EASY
    config.SPACE_INVADERS_DIFFICULTY = config.DIFFICULTY_EASY
    config.TETRIS_DIFFICULTY = config.DIFFICULTY_EASY
    # Re‑apply defaults for each module (they read globals on import)
    importlib.reload(importlib.import_module("games.breakout"))
    importlib.reload(importlib.import_module("games.pong"))
    importlib.reload(importlib.import_module("games.space_invaders"))
    importlib.reload(importlib.import_module("games.tetris"))


def test_breakout_scaling():
    # Easy (default) – values should be base
    breakout = importlib.import_module("games.breakout.breakout")

    config.BREAKOUT_DIFFICULTY = config.DIFFICULTY_EASY
    breakout._apply_breakout_speed_settings()
    assert breakout.PADDLE_SPEED == 6
    assert breakout.BALL_SPEED == 5
    assert breakout.BRICK_ROWS == 5

    # Medium – scaled values
    config.BREAKOUT_DIFFICULTY = config.DIFFICULTY_MEDIUM
    breakout._apply_breakout_speed_settings()
    assert breakout.PADDLE_SPEED == int(6 * 1.2)
    assert breakout.BALL_SPEED == int(5 * 1.5)
    assert breakout.BRICK_ROWS == 6

    # Hard – scaled values
    config.BREAKOUT_DIFFICULTY = config.DIFFICULTY_HARD
    breakout._apply_breakout_speed_settings()
    assert breakout.PADDLE_SPEED == int(6 * 1.5)
    assert breakout.BALL_SPEED == int(5 * 2)
    assert breakout.BRICK_ROWS == 7

    reset_difficulties()


def test_pong_scaling():
    pong = importlib.import_module("games.pong.pong")

    # Easy
    config.PONG_DIFFICULTY = config.DIFFICULTY_EASY
    pong._apply_pong_speed_settings()
    assert pong.PADDLE_SPEED == 5
    assert pong.BALL_SPEED_X == 4
    assert pong.BALL_SPEED_Y == 4
    assert pong.AI_PADDLE_SPEED == 5

    # Medium
    config.PONG_DIFFICULTY = config.DIFFICULTY_MEDIUM
    pong._apply_pong_speed_settings()
    assert pong.PADDLE_SPEED == int(5 * 1.2)
    assert pong.BALL_SPEED_X == int(4 * 1.5)
    assert pong.BALL_SPEED_Y == int(4 * 1.5)
    assert pong.AI_PADDLE_SPEED == int(5 * 1.2)

    # Hard
    config.PONG_DIFFICULTY = config.DIFFICULTY_HARD
    pong._apply_pong_speed_settings()
    assert pong.PADDLE_SPEED == int(5 * 1.5)
    assert pong.BALL_SPEED_X == int(4 * 2)
    assert pong.BALL_SPEED_Y == int(4 * 2)
    assert pong.AI_PADDLE_SPEED == int(5 * 1.5)

    reset_difficulties()


def test_space_invaders_scaling():
    si = importlib.import_module("games.space_invaders.space_invaders")

    # Easy
    config.SPACE_INVADERS_DIFFICULTY = config.DIFFICULTY_EASY
    si._apply_space_invaders_speed_settings()
    assert si.PLAYER_SPEED == 5
    assert si.BULLET_SPEED == 7
    assert si.ALIEN_SPEED == 1
    assert si.ENEMY_SHOOT_COOLDOWN == 2.0

    # Medium
    config.SPACE_INVADERS_DIFFICULTY = config.DIFFICULTY_MEDIUM
    si._apply_space_invaders_speed_settings()
    mult = 1.5
    assert si.PLAYER_SPEED == int(5 * mult)
    assert si.BULLET_SPEED == int(7 * mult)
    assert si.ALIEN_SPEED == int(1 * mult)
    assert si.ENEMY_SHOOT_COOLDOWN == 2.0 / mult

    # Hard
    config.SPACE_INVADERS_DIFFICULTY = config.DIFFICULTY_HARD
    si._apply_space_invaders_speed_settings()
    mult = 2.0
    assert si.PLAYER_SPEED == int(5 * mult)
    assert si.BULLET_SPEED == int(7 * mult)
    assert si.ALIEN_SPEED == int(1 * mult)
    assert si.ENEMY_SHOOT_COOLDOWN == 2.0 / mult

    reset_difficulties()


def test_tetris_scaling():
    tetris = importlib.import_module("games.tetris.tetris")

    # Easy
    config.TETRIS_DIFFICULTY = config.DIFFICULTY_EASY
    tetris._apply_tetris_speed_settings()
    assert tetris.FALL_SPEED == 500
    assert tetris.FAST_FALL_SPEED == 50

    # Medium
    config.TETRIS_DIFFICULTY = config.DIFFICULTY_MEDIUM
    tetris._apply_tetris_speed_settings()
    mult = 1.5
    assert tetris.FALL_SPEED == int(500 / mult)
    assert tetris.FAST_FALL_SPEED == int(50 / mult)

    # Hard
    config.TETRIS_DIFFICULTY = config.DIFFICULTY_HARD
    tetris._apply_tetris_speed_settings()
    mult = 2.0
    assert tetris.FALL_SPEED == int(500 / mult)
    assert tetris.FAST_FALL_SPEED == int(50 / mult)

    reset_difficulties()
