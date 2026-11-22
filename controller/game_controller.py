"""Coordinates user input, game rules, and the Tkinter view."""

from queue import Empty
from tkinter import messagebox, simpledialog

from controller.lan_session import LAN_PORT, LanSession
from model.game_state import GameState
from view.game_view import PoliceVoleurView


class GameController:
    def __init__(self, root):
        self.root = root
        self.lan = None
        self.lan_role = None
        self.lan_status = ""
        self.game = GameState()
        self.selected_node = None
        self.notice = ""
        self.view = PoliceVoleurView(root, self.game, self)
        self.root.protocol("WM_DELETE_WINDOW", self.quit)

    def new_game(self):
        self.close_lan()
        self.reset_board()

    def reset_board(self):
        self.game = GameState()
        self.selected_node = None
        self.notice = ""
        self.view.present_game(self.game, self.selected_node, self.notice)

    def show_menu(self):
        self.close_lan()
        self.selected_node = None
        self.notice = ""
        self.view.show_menu(self.selected_node, self.notice)

    def quit(self):
        self.close_lan()
        self.root.destroy()

    def close_lan(self):
        if self.lan is not None:
            self.lan.close()
        self.lan = None
        self.lan_role = None
        self.lan_status = ""

    def host_game(self):
        self.start_lan(None)

    def join_game(self):
        address = simpledialog.askstring(
            "Rejoindre en LAN", "Adresse IPv4 du PC du policier",
            parent=self.root,
        )
        if address and address.strip():
            self.start_lan(address.strip())

    def start_lan(self, address):
        self.close_lan()
        try:
            session = LanSession(address)
        except OSError as error:
            messagebox.showerror(
                "Partie LAN", f"Impossible d’héberger sur le port {LAN_PORT}.\n{error}",
                parent=self.root,
            )
            return
        self.lan = session
        self.lan_role = "police" if address is None else "thief"
        self.lan_status = (
            "En attente du voleur. Sur son PC, saisissez l’adresse IPv4 de ce PC (ipconfig)."
            if address is None else f"Connexion à {address}…"
        )
        self.reset_board()
        self.root.after(40, self.poll_lan, session)

    def poll_lan(self, session):
        if self.lan is not session:
            return
        try:
            while True:
                event, value = session.events.get_nowait()
                if event == "error":
                    self.end_lan(value)
                    return
                if event == "ready":
                    self.lan_status = ""
                elif not self.receive_action(value):
                    self.end_lan("Action reçue invalide.")
                    return
                self.selected_node = None
                self.notice = ""
                self.refresh()
        except Empty:
            self.root.after(40, self.poll_lan, session)

    def end_lan(self, reason):
        self.lan.close()
        self.lan_status = f"Connexion interrompue. {reason}"
        self.selected_node = None
        self.notice = ""
        self.refresh()

    @property
    def can_play(self):
        return self.lan_role is None or (
            not self.lan_status and self.game.current_player == self.lan_role
        )

    def receive_action(self, action):
        if self.can_play or self.lan_status or not isinstance(action, list):
            return False
        if not all(isinstance(node, str) and node in self.game.nodes for node in action):
            return False
        if len(action) == 1 and self.game.current_player == "police":
            return self.game.place_cop(action[0])
        if len(action) == 2:
            return self.game.move(self.game.current_player, *action)
        return False

    def send_action(self, *nodes):
        if self.lan is not None:
            self.lan.send(nodes)

    def handle_board_click(self, node):
        if self.game.phase == "finished" or not self.can_play:
            return

        if self.game.phase == "setup":
            if self.game.place_cop(node):
                self.send_action(node)
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
            self.send_action(self.selected_node, node)
            self.selected_node = None
            self.notice = ""
        else:
            self.notice = "Déplacement impossible."

        self.refresh()

    def refresh(self):
        self.view.set_game_feedback(self.selected_node, self.notice)
