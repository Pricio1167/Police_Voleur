import unittest

from model.game_state import GameState


class GameStateTests(unittest.TestCase):
    def make_started_game(self):
        game = GameState()
        self.assertTrue(game.place_cop("I_S"))
        self.assertTrue(game.place_cop("O_S"))
        self.assertTrue(game.place_cop("O_E"))
        return game

    def test_setup_requires_one_inner_and_two_outer_positions(self):
        game = GameState()

        self.assertFalse(game.place_cop("O_N"))
        self.assertTrue(game.place_cop("I_N"))
        self.assertFalse(game.place_cop("I_E"))
        self.assertTrue(game.place_cop("O_N"))
        self.assertTrue(game.place_cop("O_E"))
        self.assertEqual(game.phase, "play")
        self.assertEqual(game.current_player, "thief")

    def test_thief_wins_by_returning_to_the_center(self):
        game = self.make_started_game()

        self.assertFalse(game.move("thief", "C", "O_N"))
        self.assertTrue(game.move("thief", "C", "I_N"))
        self.assertTrue(game.move("police", "O_S", "X_S"))
        self.assertTrue(game.move("thief", "I_N", "C"))
        self.assertEqual(game.winner, "thief")

    def test_police_win_when_they_block_every_thief_move(self):
        game = self.make_started_game()
        game.thief = "O_N"
        game.cops = ["B_NL", "B_NR", "I_N"]
        game.current_player = "police"

        self.assertTrue(game.move("police", "I_N", "X_N"))
        self.assertEqual(game.winner, "police")


if __name__ == "__main__":
    unittest.main()
