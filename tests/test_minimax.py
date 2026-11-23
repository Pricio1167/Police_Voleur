import unittest
from unittest.mock import Mock, patch

from controller.game_controller import GameController
from controller.minimax import MinimaxAI
from model.game_state import GameState


class MinimaxTests(unittest.TestCase):
    def test_setup_action_is_legal_and_does_not_change_the_game(self):
        game = GameState()
        action = MinimaxAI(depth=2).choose_action(game)

        self.assertIn(action[1], game.inner_nodes)
        self.assertEqual(game.cops, [None, None, None])
        self.assertEqual(game.phase, "setup")

    def test_thief_takes_an_immediate_winning_move(self):
        game = GameState()
        for node in ("I_S", "O_S", "O_E"):
            self.assertTrue(game.place_cop(node))
        game.thief = "I_N"

        action = MinimaxAI(depth=2).choose_action(game)

        self.assertEqual(action, ("move", "I_N", "C"))
        self.assertEqual(game.phase, "play")

    def test_local_thief_starts_after_minimax_places_the_police(self):
        with patch("controller.game_controller.PoliceVoleurView"):
            controller = GameController(Mock())
        controller.local_role = "thief"

        controller.run_ai_turn()

        self.assertEqual(controller.game.phase, "play")
        self.assertEqual(controller.game.current_player, "thief")
        self.assertTrue(all(cop is not None for cop in controller.game.cops))

    def test_local_multiplayer_starts_without_an_ai_turn(self):
        with patch("controller.game_controller.PoliceVoleurView"):
            controller = GameController(Mock())

        controller.start_local_multiplayer()

        self.assertTrue(controller.local_multiplayer)
        self.assertIsNone(controller.local_role)
        self.assertTrue(controller.can_play)
        self.assertEqual(controller.game.phase, "setup")


if __name__ == "__main__":
    unittest.main()
