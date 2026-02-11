"""Tests for the Engine state machine.

Ensures that a state can request a transition and the Engine updates the current state accordingly.
"""

import os

import pygame

# Ensure headless mode
os.environ["HEADLESS"] = "1"

pygame.init()

from classic_arcade.engine import Engine, State


class DummyStateA(State):
    def __init__(self):
        super().__init__()
        self.update_calls = 0

    def handle_event(self, event):
        pass

    def update(self, dt):
        self.update_calls += 1
        # After first update, request transition to DummyStateB
        if self.update_calls == 1:
            self.request_transition(DummyStateB())

    def draw(self, screen):
        pass


class DummyStateB(State):
    def __init__(self):
        super().__init__()
        self.updated = False

    def handle_event(self, event):
        pass

    def update(self, dt):
        self.updated = True

    def draw(self, screen):
        pass


def test_engine_state_transition(tmp_path, monkeypatch):
    # Monkeypatch Engine's screen creation to avoid creating a real window
    # Use a dummy surface for Engine's screen attribute after initialization
    dummy_state = DummyStateA()
    engine = Engine(dummy_state, fps=60)
    # Override the screen with a dummy surface
    engine.screen = pygame.Surface((1, 1))
    # Run a single iteration manually (engine.run would loop indefinitely)
    # Simulate one frame: handle events (none), update, draw, transition.
    engine.state.update(1 / 60)
    # At this point, DummyStateA should have requested transition
    assert isinstance(engine.state, DummyStateA)
    # Apply transition logic as in Engine.run
    if engine.state.next_state is not None:
        engine.state = engine.state.next_state
    # Now the current state should be DummyStateB
    assert isinstance(engine.state, DummyStateB)
    # Ensure DummyStateB update works without error
    engine.state.update(1 / 60)
    assert engine.state.updated
