import pygame
from engine import Engine, State


class DummyState(State):
    def __init__(self):
        super().__init__()

    def handle_event(self, event: pygame.event.Event) -> None:
        # No special handling needed
        pass

    def update(self, dt: float) -> None:
        # No game logic needed for this test
        pass

    def draw(self, screen: pygame.Surface) -> None:
        # No drawing needed for this test
        pass


def test_engine_quit_cleans_up(monkeypatch):
    """Ensure that closing the window triggers a clean shutdown.

    The Engine should exit its loop, set ``running`` to ``False`` and
    ``pygame.quit()`` should be called (``pygame.get_init()`` becomes ``False``).
    """
    # Initialise pygame – the Engine expects it to be initialised
    pygame.init()
    # Simulate a single QUIT event, then no further events
    quit_event = pygame.event.Event(pygame.QUIT)
    events = [quit_event]

    def fake_get():
        if events:
            return [events.pop(0)]
        return []

    monkeypatch.setattr(pygame.event, "get", fake_get)
    # Run the engine with a dummy state
    engine = Engine(DummyState())
    engine.run()
    # After run the pygame module should be uninitialised
    assert not pygame.get_init()
    # The engine's running flag should be cleared
    assert engine.running is False
