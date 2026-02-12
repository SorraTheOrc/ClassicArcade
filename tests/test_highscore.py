import json
import os

import pytest

# Import the highscore module
import games.highscore as hs


@pytest.fixture(autouse=True)
def reset_hs_dir(tmp_path, monkeypatch):
    """Ensure the highscore directory is isolated per test."""
    # Monkeypatch the _HIGHSCORE_DIR to the temporary path
    monkeypatch.setattr(hs, "_HIGHSCORE_DIR", str(tmp_path))
    # Ensure directory exists
    os.makedirs(str(tmp_path), exist_ok=True)
    yield
    # Cleanup: remove any created files
    for f in os.listdir(str(tmp_path)):
        os.remove(os.path.join(str(tmp_path), f))


def test_add_score_creates_and_sorts(tmp_path):
    # Ensure no file exists initially
    game_name = "testgame"
    file_path = os.path.join(str(tmp_path), f"highscore_{game_name}.json")
    assert not os.path.exists(file_path)

    # Add a score
    scores = hs.add_score(game_name, 150)
    # File should be created
    assert os.path.isfile(file_path)
    # Scores list should contain one entry
    assert len(scores) == 1
    assert scores[0]["score"] == 150

    # Add a higher score and a lower score
    scores = hs.add_score(game_name, 200)
    scores = hs.add_score(game_name, 100)
    # Should be sorted descending: 200,150,100
    assert [e["score"] for e in scores] == [200, 150, 100]

    # Load directly and verify same order
    loaded = hs.load_highscores(game_name)
    assert [e["score"] for e in loaded] == [200, 150, 100]


def test_load_missing_returns_empty(tmp_path):
    # Load a game that has no file yet
    missing = hs.load_highscores("no_file_game")
    assert missing == []


def test_malformed_file_returns_empty(tmp_path, monkeypatch):
    game_name = "badgame"
    file_path = os.path.join(str(tmp_path), f"highscore_{game_name}.json")
    # Write malformed JSON
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("{ not a valid json }")
    # Loading should return empty list, not raise
    result = hs.load_highscores(game_name)
    assert result == []


def test_record_highscore_records_once(monkeypatch, tmp_path):
    class DummyState:
        highscore_recorded = False
        highscores = []

    state = DummyState()
    monkeypatch.setattr(hs, "_HIGHSCORE_DIR", str(tmp_path))

    scores = hs.record_highscore(state, "dummy", 42)
    assert state.highscore_recorded is True
    assert scores
    assert scores[0]["score"] == 42

    scores_again = hs.record_highscore(state, "dummy", 10)
    assert scores_again == scores
