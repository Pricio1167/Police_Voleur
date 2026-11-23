"""Coordinates user input, game rules, and the Tkinter view."""

from queue import Empty
from tkinter import messagebox, simpledialog

from controller.lan_session import LAN_PORT, LanSession
from controller.minimax import MinimaxAI
from model.game_state import GameState
from view.game_view import PoliceVoleurView


class GameController:
    def __init__(self, root):
        self.root = root
        self.lan = None
        self.lan_role = None
        self.lan_status = ""
        self.local_role = None
        self.local_multiplayer = False
        self.restart_requested = False
        self.peer_restart_requested = False
        self.ai = MinimaxAI()
        self.game = GameState()
        self.selected_node = None
        self.notice = ""
        self.view = PoliceVoleurView(root, self.game, self)
        self.root.protocol("WM_DELETE_WINDOW", self.quit)

    def new_game(self):
        role = messagebox.askyesnocancel(
            "Nouvelle partie",
            "Jouer la police ?\n\nOui : Police    Non : Voleur",
            parent=self.root,
        )
        if role is None:
            return
        self.close_lan()
        self.local_role = "police" if role else "thief"
        self.local_multiplayer = False
        self.reset_board()

    def start_local_multiplayer(self):
        self.close_lan()
        self.local_role = None
        self.local_multiplayer = True
        self.reset_board()

    def reset_board(self):
        self.restart_requested = False
        self.peer_restart_requested = False
        self.game = GameState()
        self.selected_node = None
        self.notice = ""
        self.view.present_game(self.game, self.selected_node, self.notice)
        if self.lan is None:
            self.root.after(0, self.run_ai_turn)

    def show_menu(self):
        self.close_lan()
        self.local_role = None
        self.local_multiplayer = False
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
        role = messagebox.askyesnocancel(
            "Héberger une partie LAN",
            "Jouer la police ?\n\nOui : Police    Non : Voleur",
            parent=self.root,
        )
        if role is not None:
            self.start_lan(None, "police" if role else "thief")

    def join_game(self):
        address = simpledialog.askstring(
            "Rejoindre en LAN",
            "Adresse IPv4 du PC de l’hébergeur",
            parent=self.root,
        )
        if address and address.strip():
            self.start_lan(address.strip())

    def start_lan(self, address, role=None):
        self.close_lan()
        self.local_role = None
        self.local_multiplayer = False
        if address is None and role is None:
            role = "police"
        try:
            session = LanSession(address, role=role)
        except OSError as error:
            messagebox.showerror(
                "Partie LAN", f"Impossible d’héberger sur le port {LAN_PORT}.\n{error}",
                parent=self.root,
            )
            return
        self.lan = session
        self.lan_role = role if address is None else None
        self.lan_status = (
            "En attente de l’autre joueur. Saisissez l’adresse IPv4 de ce PC (ipconfig)."
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
                    if value == session.role:
                        self.end_lan("Le rôle LAN annoncé est incohérent.")
                        return
                    self.lan_role = session.role
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
        if self.restart_requested or self.peer_restart_requested:
            return False
        if self.lan is not None:
            return bool(
                self.lan_role
                and not self.lan_status
                and self.game.current_player == self.lan_role
            )
        if self.local_role is None:
            return True
        player = "police" if self.game.phase == "setup" else self.game.current_player
        return player == self.local_role

    def receive_action(self, action):
        if isinstance(action, dict) and action.get("type") == "restart":
            self.peer_restart_requested = True
            if self.restart_requested:
                self.reset_board()
            else:
                self.notice = "L’autre joueur propose de recommencer."
            return True
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

    def request_restart(self):
        if self.lan is None:
            self.reset_board()
            return
        self.restart_requested = True
        self.lan.send({"type": "restart"})
        self.notice = "En attente de l’accord de l’autre joueur."
        if self.peer_restart_requested:
            self.reset_board()
        else:
            self.refresh()

    def run_ai_turn(self):
        if self.lan is not None or self.local_role is None:
            return
        for _ in range(3):
            if self.game.phase == "finished":
                break
            player = "police" if self.game.phase == "setup" else self.game.current_player
            if player == self.local_role:
                break
            action = self.ai.choose_action(self.game)
            if action is None:
                break
            self.ai.apply_action(self.game, player, action)
        self.selected_node = None
        self.notice = ""
        self.refresh()

    def handle_board_click(self, node):
        if self.game.phase == "finished" or not self.can_play:
            return

        if self.game.phase == "setup":
            if self.game.place_cop(node):
                self.send_action(node)
                self.notice = ""
                if self.lan is None and self.local_role is not None:
                    self.root.after(0, self.run_ai_turn)
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
            if self.lan is None and self.local_role is not None:
                self.root.after(0, self.run_ai_turn)
        else:
            self.notice = "Déplacement impossible."

        self.refresh()

    def refresh(self):
        self.view.set_game_feedback(self.selected_node, self.notice)
