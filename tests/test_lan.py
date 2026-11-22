import unittest
from unittest.mock import Mock, patch

from controller.game_controller import GameController
from controller.lan_session import LanSession


class LanGameTest(unittest.TestCase):
    def test_two_players_share_placements_and_moves(self):
        with patch("controller.game_controller.PoliceVoleurView"):
            police = GameController(Mock())
            thief = GameController(Mock())

        police.lan = LanSession(port=0)
        self.addCleanup(police.close_lan)
        port = police.lan.listener.getsockname()[1]
        thief.lan = LanSession("127.0.0.1", port)
        self.addCleanup(thief.close_lan)
        police.lan_role = "police"
        thief.lan_role = "thief"
        for player in (police, thief):
            self.assertEqual(player.lan.events.get(timeout=3), ("ready", None))

        thief.handle_board_click("I_S")
        self.assertEqual(thief.game.cops, [None, None, None])
        for node in ("I_N", "O_N", "O_E"):
            police.handle_board_click(node)
            self.deliver_action(thief)
        self.assertEqual(police.game.cops, thief.game.cops)
        self.assertFalse(police.can_play)

        thief.handle_board_click("C")
        thief.handle_board_click("I_S")
        self.deliver_action(police)
        police.handle_board_click("I_N")
        police.handle_board_click("X_N")
        self.deliver_action(thief)
        self.assertEqual(police.game.cops, thief.game.cops)
        self.assertEqual(police.game.thief, thief.game.thief)
        self.assertTrue(thief.can_play)

        police.close_lan()
        self.assertEqual(thief.lan.events.get(timeout=3)[0], "error")

    def deliver_action(self, player):
        event, action = player.lan.events.get(timeout=3)
        self.assertEqual(event, "action")
        self.assertTrue(player.receive_action(action))
