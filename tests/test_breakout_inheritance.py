import unittest
from games.game_base import Game
from games.breakout import BreakoutState


class TestBreakoutInheritance(unittest.TestCase):
    def test_breakout_is_game_subclass(self):
        self.assertTrue(
            issubclass(BreakoutState, Game), "BreakoutState should subclass Game"
        )


if __name__ == "__main__":
    unittest.main()
