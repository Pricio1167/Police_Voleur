"""Coordinates user input, game rules, and the Tkinter view."""

from model.game_state import GameState
from view.game_view import PoliceVoleurView


class GameController:
    def __init__(self, root):
        self.game = GameState()
        self.selected_node = None
        self.notice = ""
        self.view = PoliceVoleurView(root, self.game, self)

    def new_game(self):
        self.game = GameState()
        self.selected_node = None
        self.notice = ""
        self.view.present_game(self.game, self.selected_node, self.notice)

    def show_menu(self):
        self.selected_node = None
        self.notice = ""
        self.view.show_menu(self.selected_node, self.notice)

    def handle_board_click(self, node):
        if self.game.phase == "finished":
            return

        if self.game.phase == "setup":
            if self.game.place_cop(node):
                self.notice = ""
            else:
                self.notice = "Choisissez un point libre indiqué sur le plateau."
            self.selected_node = None
            self.refresh()
            return

        own_nodes = (
            [self.game.thief]
            if self.game.current_player == "thief"
            else [cop for cop in self.game.cops if cop is not None]
        )

        if self.selected_node is None:
            if node in own_nodes:
                self.selected_node = node
                self.notice = ""
            else:
                self.notice = "Sélectionnez l'un de vos pions."
        elif node == self.selected_node:
            self.selected_node = None
            self.notice = ""
        elif node in own_nodes:
            self.selected_node = node
            self.notice = ""
        elif self.game.move(self.game.current_player, self.selected_node, node):
            self.selected_node = None
            self.notice = ""
        else:
            self.notice = "Déplacement impossible."

        self.refresh()

    def refresh(self):
        self.view.set_game_feedback(self.selected_node, self.notice)
