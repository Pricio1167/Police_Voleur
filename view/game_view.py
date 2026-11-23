"""Tkinter screens and rendering for Police et voleur."""

import json
import math
import os
from pathlib import Path
import threading
import tkinter as tk
from tkinter import colorchooser, messagebox

from assets.pawn_assets import PawnAssetCache, PawnAssetDownloadError


class PoliceVoleurView:
    THEMES = {
        "Nuit": {
            "background": "#0b1020",
            "surface": "#121b2e",
            "surface_alt": "#1a2740",
            "line": "#486080",
            "text": "#f2f5fa",
            "muted": "#9baac0",
            "accent": "#f2b84b",
            "good": "#73d6a0",
            "bad": "#ff7b76",
        },
        "Classique": {
            "background": "#f2efe8",
            "surface": "#fffdf8",
            "surface_alt": "#e9e3d8",
            "line": "#344356",
            "text": "#202c3b",
            "muted": "#687789",
            "accent": "#d99b2b",
            "good": "#378451",
            "bad": "#b8453d",
        },
        "Forêt": {
            "background": "#101d1a",
            "surface": "#182a25",
            "surface_alt": "#223a32",
            "line": "#668c79",
            "text": "#edf5ec",
            "muted": "#a7bdad",
            "accent": "#d5b45b",
            "good": "#75d49a",
            "bad": "#f07869",
        },
    }
    SKINS = ("Insigne", "Néon", "Sceau")
    BOARD_STYLES = ("Classique", "Bois", "Ardoise")
    ONLINE_SKINS = {
        "kenney_pawn": "Pion",
        "kenney_chess": "Échecs",
        "kenney_character": "Personnage",
    }
    COLOR_CHOICES = {
        "Bleu": "#438bdf",
        "Cyan": "#20b9c9",
        "Violet": "#a46be0",
        "Rouge": "#e36357",
        "Orange": "#ed8b42",
        "Rose": "#e46e9a",
        "Vert": "#55ae76",
        "Or": "#d6a941",
    }

    def __init__(self, root, game, controller):
        self.root = root
        self.game = game
        self.controller = controller
        self.root.title("Police et voleur")
        self.root.geometry("1180x780")
        self.root.minsize(980, 680)
        self.preferences_path = (
            Path(os.environ.get("APPDATA", str(Path.home())))
            / "PoliceVoleur"
            / "settings.json"
        )
        self.pawn_assets = PawnAssetCache(self.preferences_path.parent / "pawns")
        self.photo_cache = {}
        self.download_in_progress = False
        self.download_status = ""
        self.pending_skin = None
        self.preferences = self.load_preferences()
        self.palette = self.THEMES[self.preferences["theme"]]
        self.selected_node = None
        self.notice = ""
        self.canvas = tk.Canvas(
            self.root,
            bg=self.palette["background"],
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.on_board_click)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        self.screen = "menu"
        self.hitboxes = []
        self.hovered = None
        self.center_x = 0
        self.center_y = 0
        self.radius = 1
        self.draw_screen()

    def load_preferences(self):
        defaults = {
            "theme": "Nuit",
            "police_color": "#438bdf",
            "thief_color": "#ed7950",
            "skin": "Insigne",
            "board_style": "Classique",
        }
        try:
            with self.preferences_path.open("r", encoding="utf-8") as settings_file:
                saved = json.load(settings_file)
        except FileNotFoundError:
            return defaults
        except (OSError, json.JSONDecodeError) as error:
            messagebox.showwarning(
                "Paramètres",
                "Les paramètres sauvegardés n'ont pas pu être lus. "
                "Les valeurs par défaut seront utilisées.\n\n" + str(error),
            )
            return defaults

        if not isinstance(saved, dict):
            messagebox.showwarning(
                "Paramètres",
                "Le fichier de paramètres est invalide. Les valeurs par défaut "
                "seront utilisées.",
            )
            return defaults
        if saved.get("theme") in self.THEMES:
            defaults["theme"] = saved["theme"]
        available_skins = set(self.SKINS) | set(self.ONLINE_SKINS)
        if saved.get("skin") in available_skins:
            if (
                saved["skin"] in self.ONLINE_SKINS
                and not self.pawn_assets.is_ready()
            ):
                messagebox.showwarning(
                    "Pions personnalisés",
                    "Les images de pions sauvegardées ne sont pas dans le cache. "
                    "Le style Insigne sera utilisé.",
                )
            else:
                defaults["skin"] = saved["skin"]
        if saved.get("board_style") in self.BOARD_STYLES:
            defaults["board_style"] = saved["board_style"]
        for key in ("police_color", "thief_color"):
            value = saved.get(key)
            if isinstance(value, str) and value.startswith("#") and len(value) == 7:
                try:
                    int(value[1:], 16)
                except ValueError:
                    continue
                defaults[key] = value
        return defaults

    def save_preferences(self):
        try:
            self.preferences_path.parent.mkdir(parents=True, exist_ok=True)
            with self.preferences_path.open("w", encoding="utf-8") as settings_file:
                json.dump(self.preferences, settings_file, indent=2)
        except OSError as error:
            messagebox.showerror(
                "Paramètres",
                "Impossible de sauvegarder les paramètres.\n\n" + str(error),
            )

    def on_canvas_resize(self, _event):
        self.draw_screen()

    def on_mouse_move(self, event):
        previous = self.hovered
        self.hovered = next(
            (
                index
                for index, (x1, y1, x2, y2, _action) in enumerate(self.hitboxes)
                if x1 <= event.x <= x2 and y1 <= event.y <= y2
            ),
            None,
        )
        if previous != self.hovered:
            self.draw_screen()

    def draw_screen(self):
        if not hasattr(self, "canvas"):
            return
        self.width = max(self.canvas.winfo_width(), 800)
        self.height = max(self.canvas.winfo_height(), 600)
        self.hitboxes = []
        self.canvas.delete("all")
        self.canvas.configure(bg=self.palette["background"])
        self.draw_background()
        if self.screen == "menu":
            self.draw_menu()
        elif self.screen == "local_modes":
            self.draw_local_modes()
        elif self.screen == "settings":
            self.draw_settings()
        elif self.screen == "appearance":
            self.draw_appearance()
        elif self.screen == "pawn_gallery":
            self.draw_pawn_gallery()
        elif self.screen == "how_to_play":
            self.draw_how_to_play()
        else:
            self.draw_game()

    def draw_background(self):
        self.canvas.create_rectangle(
            0, 0, self.width, 3,
            fill=self.palette["accent"], outline="",
        )
        if self.screen == "menu":
            split = self.width * 0.50
            self.canvas.create_polygon(
                split, 3,
                self.width, 3,
                self.width, self.height,
                self.width * 0.56, self.height,
                fill=self.palette["surface"],
                outline="",
            )
            self.canvas.create_line(
                split, 3, self.width * 0.56, self.height,
                fill=self.palette["surface_alt"],
                width=2,
            )
        elif self.screen == "game":
            self.canvas.create_line(
                28, self.height - 76, self.width - 28, self.height - 76,
                fill=self.palette["surface_alt"],
                width=1,
            )

    def draw_rounded_rectangle(
        self, x, y, width, height, radius, fill, outline="", line_width=1
    ):
        radius = min(radius, width / 2, height / 2)
        corners = (
            (x + width - radius, y + radius, -90, 0),
            (x + width - radius, y + height - radius, 0, 90),
            (x + radius, y + height - radius, 90, 180),
            (x + radius, y + radius, 180, 270),
        )
        points = []
        for center_x, center_y, start_angle, end_angle in corners:
            for step in range(6):
                angle = math.radians(start_angle + (end_angle - start_angle) * step / 5)
                points.extend(
                    (
                        center_x + math.cos(angle) * radius,
                        center_y + math.sin(angle) * radius,
                    )
                )
        return self.canvas.create_polygon(
            *points,
            fill=fill,
            outline=outline,
            width=line_width,
        )

    def draw_menu(self):
        left = self.width * 0.1
        self.draw_text(
            left, self.height * 0.22, "JEU DE PLATEAU  /  2 JOUEURS",
            size=11, color=self.palette["accent"], weight="bold", anchor="w",
        )
        self.draw_text(
            left, self.height * 0.32, "POLICE", size=52, weight="bold", anchor="w"
        )
        self.draw_text(
            left, self.height * 0.41, "ET VOLEUR", size=52,
            color=self.palette["accent"], weight="bold", anchor="w",
        )
        self.draw_text(
            left, self.height * 0.48,
            "Contre l’ordinateur ou sur le même réseau.",
            size=15, color=self.palette["muted"], anchor="w",
        )

        menu_x = left
        menu_y = self.height * 0.62
        gap = 58
        self.draw_button(
            menu_x, menu_y, 260, 52, "JOUER SUR CE PC", self.show_local_modes,
            primary=True, font_size=13,
        )
        self.draw_button(
            menu_x + 276, menu_y, 180, 52, "HÉBERGER",
            self.controller.host_game,
        )
        self.draw_button(
            menu_x + 276, menu_y + gap, 180, 48, "REJOINDRE",
            self.controller.join_game,
        )
        self.draw_button(
            menu_x, menu_y + gap, 260, 48, "PARAMÈTRES", self.show_settings,
        )
        self.draw_button(
            menu_x, menu_y + gap * 2, 260, 48, "COMMENT JOUER", self.show_how_to_play,
        )
        self.draw_button(
            menu_x, menu_y + gap * 3, 260, 48, "QUITTER", self.controller.quit,
        )

        board_x = self.width * 0.73
        board_y = self.height * 0.49
        board_radius = min(self.width * 0.19, self.height * 0.31)
        self.draw_decorative_board(board_x, board_y, board_radius)
        self.draw_text(
            board_x, self.height * 0.88, "DEUX JOUEURS  /  UN PLATEAU",
            size=10, color=self.palette["muted"], anchor="center",
        )

    def draw_local_modes(self):
        self.draw_button(32, 34, 128, 42, "←  RETOUR", self.show_menu)
        center_x = self.width / 2
        self.draw_text(
            center_x, self.height * 0.22, "CHOISISSEZ VOTRE MODE",
            size=24, weight="bold",
        )
        self.draw_text(
            center_x, self.height * 0.28,
            "Jouez seul contre l’ordinateur ou à deux sur cet écran.",
            size=12, color=self.palette["muted"],
        )

        card_width = min(300, self.width * 0.36)
        card_height = 230
        gap = 28
        left = (self.width - card_width * 2 - gap) / 2
        top = self.height * 0.37
        for x, title, description, label, action in (
            (
                left,
                "SOLO",
                "Affrontez l’ordinateur, qui choisit ses coups avec minimax.",
                "JOUER EN SOLO",
                self.controller.new_game,
            ),
            (
                left + card_width + gap,
                "MULTIJOUEUR",
                "Deux joueurs se partagent le même ordinateur et jouent à tour de rôle.",
                "JOUER À DEUX",
                self.controller.start_local_multiplayer,
            ),
        ):
            self.draw_card(x, top, card_width, card_height, self.palette["surface"])
            self.draw_text(
                x + card_width / 2, top + 55, title,
                size=17, weight="bold", color=self.palette["accent"],
            )
            self.draw_text(
                x + card_width / 2, top + 105, description,
                size=11, color=self.palette["muted"], width=card_width - 42,
            )
            self.draw_button(
                x + 24, top + 160, card_width - 48, 46, label,
                action, primary=title == "SOLO",
            )

    def draw_decorative_board(self, cx, cy, radius):
        self.center_x, self.center_y, self.radius = cx, cy, radius
        self.draw_board_lines()
        self.draw_piece_at(cx, cy, "V", self.preferences["thief_color"], 17)
        for angle in (math.pi, -math.pi / 4, math.pi / 4):
            x = cx + math.cos(angle) * radius
            y = cy + math.sin(angle) * radius
            self.draw_piece_at(x, y, "P", self.preferences["police_color"], 15)

    def draw_settings(self):
        self.draw_header("PARAMÈTRES", "Personnalisez votre plateau.")
        x = self.width * 0.12
        y = self.height * 0.24
        self.draw_text(
            x, y, "STYLE DE L'INTERFACE", size=11,
            color=self.palette["muted"], weight="bold", anchor="w",
        )
        themes = list(self.THEMES)
        card_w = min(210, self.width * 0.23)
        for index, theme in enumerate(themes):
            card_x = x + index * (card_w + 20)
            selected = theme == self.preferences["theme"]
            fill = self.palette["surface_alt"] if selected else self.palette["surface"]
            self.draw_card(card_x, y + 28, card_w, 105, fill, selected)
            theme_palette = self.THEMES[theme]
            self.draw_rounded_rectangle(
                card_x + 16, y + 45, card_w - 32, 37, 7,
                fill=theme_palette["background"],
                outline=theme_palette["line"],
                line_width=2,
            )
            self.canvas.create_oval(
                card_x + 27, y + 56, card_x + 45, y + 74,
                fill=theme_palette["accent"], outline="",
            )
            self.draw_text(
                card_x + card_w / 2, y + 111, theme.upper(),
                size=10, color=self.palette["text"], weight="bold",
            )
            self.add_hitbox(
                card_x, y + 28, card_x + card_w, y + 133,
                lambda choice=theme: self.set_theme(choice),
            )

        section_y = y + 190
        self.draw_text(
            x, section_y, "COULEURS DES PIONS", size=11,
            color=self.palette["muted"], weight="bold", anchor="w",
        )
        self.draw_text(
            x, section_y + 47, "POLICE", size=10,
            color=self.palette["text"], weight="bold", anchor="w",
        )
        self.draw_color_choices(
            x + 135, section_y + 47, "police_color", self.preferences["police_color"]
        )
        self.draw_text(
            x, section_y + 101, "VOLEUR", size=10,
            color=self.palette["text"], weight="bold", anchor="w",
        )
        self.draw_color_choices(
            x + 135, section_y + 101, "thief_color", self.preferences["thief_color"]
        )

        customization_y = section_y + 160
        self.draw_text(
            x, customization_y, "AUTRES OPTIONS", size=11,
            color=self.palette["muted"], weight="bold", anchor="w",
        )
        self.draw_button(
            x, customization_y + 24, 242, 40,
            "PLATEAU ET PIONS", self.show_appearance,
        )
        self.draw_button(32, 34, 128, 42, "←  RETOUR", self.controller.show_menu)

    def draw_appearance(self):
        self.draw_header("PLATEAU ET PIONS", "Choisissez le style du plateau et des pions.")
        x = self.width * 0.12
        y = self.height * 0.24
        self.draw_text(
            x, y, "STYLE DU PLATEAU", size=11,
            color=self.palette["muted"], weight="bold", anchor="w",
        )
        card_w = min(210, self.width * 0.23)
        for index, style in enumerate(self.BOARD_STYLES):
            card_x = x + index * (card_w + 20)
            selected = self.preferences["board_style"] == style
            card_y = y + 24
            self.draw_card(
                card_x, card_y, card_w, 105,
                self.palette["surface"], selected,
            )
            sample_fill, sample_line = self.board_colors(style)
            self.canvas.create_oval(
                card_x + 18, card_y + 13,
                card_x + card_w - 18, card_y + 78,
                fill=sample_fill, outline=sample_line, width=2,
            )
            self.canvas.create_line(
                card_x + card_w / 2, card_y + 15,
                card_x + card_w / 2, card_y + 76,
                fill=sample_line, width=2,
            )
            self.draw_text(
                card_x + card_w / 2, card_y + 91, style.upper(),
                size=9, color=self.palette["text"], weight="bold",
            )
            self.add_hitbox(
                card_x, card_y, card_x + card_w, card_y + 105,
                lambda choice=style: self.set_board_style(choice),
            )

        skin_y = y + 164
        self.draw_text(
            x, skin_y, "STYLE DES PIONS", size=11,
            color=self.palette["muted"], weight="bold", anchor="w",
        )
        skin_w = min(145, self.width * 0.15)
        for index, skin in enumerate(self.SKINS):
            skin_x = x + index * (skin_w + 16)
            selected = self.preferences["skin"] == skin
            self.draw_button(
                skin_x, skin_y + 24, skin_w, 40, skin.upper(),
                lambda choice=skin: self.set_skin(choice),
                primary=selected, font_size=9,
            )

        self.draw_button(
            x, skin_y + 84, 242, 42,
            "GALERIE DE PIONS CC0", self.show_pawn_gallery,
        )
        self.draw_button(
            32, 34, 142, 42, "←  PARAMÈTRES", self.show_settings,
        )

    def draw_pawn_gallery(self):
        self.draw_header(
            "GALERIE DE PIONS",
            "Pack Kenney • CC0 • Téléchargé une fois, gardé hors ligne.",
        )
        self.draw_button(
            self.width - 252, 34, 220, 42,
            "TÉLÉCHARGEMENT…" if self.download_in_progress
            else "PACK EN CACHE" if self.pawn_assets.is_ready()
            else "TÉLÉCHARGER LE PACK",
            self.download_online_skins,
            primary=not self.pawn_assets.is_ready(),
            font_size=9,
        )

        x = self.width * 0.08
        y = self.height * 0.27
        card_width = self.width * 0.26
        gap = self.width * 0.03
        card_height = 260
        for index, (skin, label) in enumerate(self.ONLINE_SKINS.items()):
            card_x = x + index * (card_width + gap)
            selected = self.preferences["skin"] == skin
            self.draw_card(
                card_x, y, card_width, card_height,
                self.palette["surface"], selected,
            )
            self.draw_text(
                card_x + card_width / 2, y + 30, label.upper(),
                size=12, color=self.palette["text"], weight="bold",
            )
            self.draw_piece_at(
                card_x + card_width / 2, y + 112, "",
                self.preferences["thief_color"], 28, skin=skin,
            )
            self.draw_text(
                card_x + card_width / 2, y + 158,
                "SÉLECTIONNÉ" if selected else "KENNEY • CC0",
                size=9,
                color=self.palette["accent"] if selected else self.palette["muted"],
                weight="bold",
            )
            action = lambda choice=skin: self.choose_online_skin(choice)
            label_text = (
                "TÉLÉCHARGEMENT…" if self.download_in_progress
                else "CHOISIR" if self.pawn_assets.is_ready()
                else "TÉLÉCHARGER"
            )
            self.draw_button(
                card_x + 16, y + 195, card_width - 32, 40,
                label_text, action, primary=selected, font_size=9,
            )

        status = self.download_status or (
            "Source : kenney.nl/assets/board-game-icons • Licence CC0"
        )
        self.draw_text(
            self.width / 2, y + card_height + 28, status,
            size=9,
            color=self.palette["bad"] if status.startswith("Erreur") else self.palette["muted"],
            width=self.width * 0.78,
        )
        self.draw_button(
            32, 34, 142, 42, "←  APPARENCE", self.show_appearance,
        )

    def draw_color_choices(self, x, y, key, selected_color):
        swatch_size = 27
        gap = 10
        for index, color in enumerate(self.COLOR_CHOICES.values()):
            swatch_x = x + index * (swatch_size + gap)
            self.canvas.create_oval(
                swatch_x, y - 13, swatch_x + swatch_size, y + 14,
                fill=color,
                outline=self.palette["text"] if color == selected_color else "",
                width=3,
            )
            self.add_hitbox(
                swatch_x - 4, y - 17, swatch_x + swatch_size + 4, y + 18,
                lambda option=key, value=color: self.set_color(option, value),
            )
        custom_x = x + len(self.COLOR_CHOICES) * (swatch_size + gap) + 10
        self.draw_button(
            custom_x, y - 15, 112, 31, "SUR MESURE",
            lambda option=key: self.choose_custom_color(option),
            font_size=8,
        )

    def draw_how_to_play(self):
        self.draw_header("COMMENT JOUER", "Les règles, en quelques étapes.")
        x = self.width * 0.12
        top = self.height * 0.29
        card_w = self.width * 0.76
        steps = (
            ("01", "PLACEZ LA POLICE",
             "Un policier sur le cercle intérieur, puis deux policiers sur le bord."),
            ("02", "À VOUS DE JOUER",
             "Deux joueurs alternent. Sélectionnez un pion, puis une intersection voisine."),
            ("03", "SUIVEZ LES LIGNES",
             "Un pion avance d'un seul trait. Une intersection ne peut accueillir qu'un pion."),
            ("04", "DÉCROCHEZ LA VICTOIRE",
             "Le voleur gagne en revenant au centre. La police gagne si le voleur est bloqué."),
        )
        for index, (number, title, description) in enumerate(steps):
            card_y = top + index * 82
            self.draw_card(
                x, card_y, card_w, 66, self.palette["surface"], False
            )
            self.draw_text(
                x + 26, card_y + 33, number, size=17,
                color=self.palette["accent"], weight="bold", anchor="w",
            )
            self.draw_text(
                x + 82, card_y + 23, title, size=10,
                color=self.palette["text"], weight="bold", anchor="w",
            )
            self.draw_text(
                x + 82, card_y + 45, description, size=10,
                color=self.palette["muted"], anchor="w",
            )
        self.draw_button(32, 34, 128, 42, "←  RETOUR", self.leave_rules)

    def draw_game(self):
        self.width = max(self.canvas.winfo_width(), 800)
        self.height = max(self.canvas.winfo_height(), 600)
        self.center_x = self.width / 2
        self.center_y = self.height * 0.52
        self.radius = min(self.width * 0.24, self.height * 0.32)
        panel_width = min(232, self.width * 0.205)
        panel_height = 250
        panel_y = max(112, self.center_y - panel_height / 2)
        left_x = 28
        right_x = self.width - left_x - panel_width

        title = {
            "local": (
                "PARTIE SOLO  /  VS ORDINATEUR"
                if self.controller.local_role is not None
                else (
                    "MULTIJOUEUR LOCAL"
                    if self.controller.local_multiplayer else "PARTIE LOCALE"
                )
            ),
            "connecting": "PARTIE LAN  /  CONNEXION",
            "police": "PARTIE LAN  /  VOUS ÊTES LA POLICE",
            "thief": "PARTIE LAN  /  VOUS ÊTES LE VOLEUR",
        }[
            self.controller.lan_role or (
                "connecting" if self.controller.lan is not None else "local"
            )
        ]
        self.draw_text(
            self.center_x, 31, title, size=10,
            color=self.palette["muted"], weight="bold",
        )
        self.draw_text(
            self.center_x, 58, self.game_status(), size=13,
            color=self.palette["text"], weight="bold",
            width=self.width * 0.42,
        )

        self.draw_board_lines()
        self.draw_board_nodes()
        if self.selected_node:
            x, y = self.point_on_canvas(self.selected_node)
            self.canvas.create_oval(
                x - 19, y - 19, x + 19, y + 19,
                outline=self.palette["accent"], width=3,
            )
        for index, node in enumerate(self.game.cops):
            if node is not None:
                self.draw_piece_at(
                    *self.point_on_canvas(node),
                    "P" + str(index + 1),
                    self.preferences["police_color"],
                    16,
                )
        self.draw_piece_at(
            *self.point_on_canvas(self.game.thief),
            "V",
            self.preferences["thief_color"],
            16,
        )

        self.draw_player_panel(
            left_x,
            panel_y,
            panel_width,
            panel_height,
            "VOLEUR",
            self.preferences["thief_color"],
            "thief",
        )
        self.draw_police_panel(
            right_x, panel_y, panel_width, panel_height
        )

        controls_width = 434
        controls_x = self.center_x - controls_width / 2
        controls_y = self.height - 58
        self.draw_button(
            controls_x, controls_y, 144, 40,
            "ACCEPTER" if self.controller.peer_restart_requested else "RECOMMENCER",
            self.controller.request_restart,
        )
        self.draw_button(
            controls_x + 154, controls_y, 100, 40, "MENU",
            self.controller.show_menu,
        )
        self.draw_button(
            controls_x + 264, controls_y, 170, 40, "COMMENT JOUER",
            self.show_how_to_play,
        )

    def draw_player_panel(
        self, x, y, width, height, title, color, player
    ):
        self.draw_card(x, y, width, height, self.palette["surface"])
        center_x = x + width / 2
        self.draw_text(
            center_x, y + 32, title, size=14,
            color=color, weight="bold",
        )
        self.draw_piece_at(
            center_x, y + 104, "V", color, 28
        )
        position = "AU CENTRE" if self.game.thief == "C" else "SUR LE PLATEAU"
        self.draw_text(
            center_x, y + 151, position, size=9,
            color=self.palette["muted"], weight="bold",
        )
        if self.game.phase == "finished":
            status = "VAINQUEUR" if self.game.winner == player else "EN ATTENTE"
        elif self.game.phase == "setup":
            status = "EN ATTENTE"
        elif self.game.current_player == player and not self.controller.lan_status:
            status = "À VOUS DE JOUER" if self.controller.can_play else "TOUR DU VOLEUR"
        else:
            status = "EN ATTENTE"
        self.draw_status_badge(center_x, y + 187, width - 28, status, color)
        if self.notice and self.game.current_player == player:
            self.draw_text(
                center_x, y + 229, self.notice, size=8,
                color=self.palette["bad"], width=width - 24,
            )

    def draw_police_panel(self, x, y, width, height):
        self.draw_card(x, y, width, height, self.palette["surface"])
        center_x = x + width / 2
        self.draw_text(
            center_x, y + 32, "POLICE", size=14,
            color=self.preferences["police_color"], weight="bold",
        )
        for index, node in enumerate(self.game.cops):
            token_x = x + width * (index + 0.5) / 3
            if node is None:
                token_y = y + 104
                self.canvas.create_oval(
                    token_x - 17, token_y - 17, token_x + 17, token_y + 17,
                    fill=self.palette["surface_alt"],
                    outline=self.palette["line"],
                    width=2,
                )
                self.draw_text(
                    token_x, token_y, "P" + str(index + 1),
                    size=8, color=self.palette["muted"], weight="bold",
                )
            else:
                self.draw_piece_at(
                    token_x, y + 104, "P" + str(index + 1),
                    self.preferences["police_color"], 17,
                )
        placed = sum(node is not None for node in self.game.cops)
        self.draw_text(
            center_x, y + 151, str(placed) + " / 3 PIONS PLACÉS",
            size=9, color=self.palette["muted"], weight="bold",
        )
        if self.game.phase == "finished":
            status = "VAINQUEUR" if self.game.winner == "police" else "EN ATTENTE"
        elif self.controller.lan_status:
            status = "EN ATTENTE"
        elif self.game.phase == "setup":
            status = "À VOUS DE PLACER" if self.controller.can_play else "PLACEMENT"
        elif self.game.current_player == "police":
            status = "À VOUS DE JOUER" if self.controller.can_play else "TOUR DE LA POLICE"
        else:
            status = "EN ATTENTE"
        self.draw_status_badge(
            center_x, y + 187, width - 28, status,
            self.preferences["police_color"],
        )
        if self.notice and (
            self.game.phase == "setup" or self.game.current_player == "police"
        ):
            self.draw_text(
                center_x, y + 229, self.notice, size=8,
                color=self.palette["bad"], width=width - 24,
            )

    def draw_status_badge(self, center_x, y, width, text, color):
        self.draw_rounded_rectangle(
            center_x - width / 2, y - 15,
            width, 30, 12,
            fill=self.palette["surface_alt"], outline="",
        )
        self.draw_text(
            center_x, y, text, size=9,
            color=color, weight="bold", width=width - 10,
        )

    def draw_board_lines(self):
        cx, cy, radius = self.center_x, self.center_y, self.radius
        board_fill, line_color = self.board_colors()
        inner_radius = radius * 0.28
        self.canvas.create_oval(
            cx - radius, cy - radius, cx + radius, cy + radius,
            fill=board_fill, outline=line_color, width=2,
        )
        self.canvas.create_line(
            cx - radius, cy, cx + radius, cy,
            fill=line_color, width=2,
        )
        self.canvas.create_line(
            cx, cy - radius, cx, cy + radius,
            fill=line_color, width=2,
        )
        self.canvas.create_oval(
            cx - inner_radius, cy - inner_radius,
            cx + inner_radius, cy + inner_radius,
            outline=line_color, width=2,
        )
        endpoint_offset = 0.37
        endpoint_depth = math.sqrt(1 - endpoint_offset**2)
        for dx, dy, tx, ty in self.game.directions.values():
            points = []
            for step in range(41):
                tangent = -endpoint_offset + (2 * endpoint_offset * step / 40)
                fraction = abs(tangent) / endpoint_offset
                depth = 0.76 + (endpoint_depth - 0.76) * fraction**2
                points.extend(
                    (
                        cx + (dx * depth + tx * tangent) * radius,
                        cy + (dy * depth + ty * tangent) * radius,
                    )
                )
            self.canvas.create_line(
                *points, fill=line_color, width=2,
                smooth=True, splinesteps=24,
            )

    def draw_board_nodes(self):
        destinations = set()
        if self.selected_node and self.game.phase == "play":
            destinations = self.game.legal_destinations(
                self.game.current_player, self.selected_node
            )
        for node in self.game.nodes:
            x, y = self.point_on_canvas(node)
            if node in destinations:
                fill, point_radius = self.palette["good"], 7
            elif self.game.phase == "setup" and self.controller.can_play:
                placed = sum(cop is not None for cop in self.game.cops)
                allowed = self.game.inner_nodes if placed == 0 else self.game.boundary_nodes
                fill = self.palette["accent"] if node in allowed else self.palette["line"]
                point_radius = 5
            else:
                fill, point_radius = self.palette["line"], 4
            self.canvas.create_oval(
                x - point_radius, y - point_radius,
                x + point_radius, y + point_radius,
                fill=fill, outline=self.palette["background"],
            )

    def draw_piece_at(self, x, y, label, color, size, skin=None):
        skin = skin or self.preferences["skin"]
        if skin in self.ONLINE_SKINS:
            self.canvas.create_oval(
                x - size, y - size, x + size, y + size,
                fill=color, outline=self.palette["text"], width=2,
            )
            image = self.pawn_image(skin, size * 2)
            if image is not None:
                self.canvas.create_image(x, y, image=image)
                return
            skin = "Insigne"
        if skin == "Néon":
            self.canvas.create_oval(
                x - size - 5, y - size - 5, x + size + 5, y + size + 5,
                outline=color, width=2,
            )
            self.canvas.create_oval(
                x - size, y - size, x + size, y + size,
                fill=self.palette["surface"], outline=color, width=3,
            )
        elif skin == "Sceau":
            points = []
            for index in range(10):
                angle = -math.pi / 2 + index * math.pi / 5
                radius = size if index % 2 == 0 else size * 0.78
                points.extend((x + math.cos(angle) * radius, y + math.sin(angle) * radius))
            self.canvas.create_polygon(
                *points, fill=color, outline=self.palette["text"], width=2,
            )
        else:
            self.canvas.create_oval(
                x - size, y - size, x + size, y + size,
                fill=color, outline=self.palette["text"], width=2,
            )
        self.canvas.create_text(
            x, y, text=label, fill="#ffffff",
            font=("Segoe UI", max(8, int(size * 0.68)), "bold"),
        )

    def pawn_image(self, skin, target_size):
        path = self.pawn_assets.image_path(skin)
        if path is None or not path.is_file():
            return None
        cache_key = (skin, target_size)
        if cache_key not in self.photo_cache:
            original = tk.PhotoImage(master=self.root, file=str(path))
            factor = max(
                1,
                math.ceil(max(original.width(), original.height()) / target_size),
            )
            self.photo_cache[cache_key] = (
                original,
                original.subsample(factor, factor),
            )
        return self.photo_cache[cache_key][1]

    def board_colors(self, style=None):
        style = style or self.preferences["board_style"]
        if style == "Bois":
            return "#75543b", "#d5b58a"
        if style == "Ardoise":
            return "#283744", "#bdc7cf"
        return self.palette["surface"], self.palette["line"]

    def point_on_canvas(self, node):
        x, y = self.game.nodes[node]
        return (
            self.center_x + x * self.radius,
            self.center_y + y * self.radius,
        )

    def node_at(self, x, y):
        closest = None
        closest_distance = max(15, self.radius * 0.08)
        for node in self.game.nodes:
            px, py = self.point_on_canvas(node)
            distance = math.hypot(px - x, py - y)
            if distance < closest_distance:
                closest = node
                closest_distance = distance
        return closest

    def game_status(self):
        if self.controller.restart_requested:
            return "En attente de l’accord de l’autre joueur."
        if self.controller.peer_restart_requested:
            return "L’autre joueur propose de recommencer."
        if self.game.phase == "finished":
            if self.game.winner == "thief":
                return "Le voleur remporte la partie."
            return "La police remporte la partie."
        if self.controller.lan_status:
            return self.controller.lan_status
        if self.game.phase == "setup" and self.controller.local_role == "thief":
            return "L’ordinateur place la police."
        if not self.controller.can_play:
            if self.controller.local_role is not None:
                return "L’ordinateur réfléchit…"
            return "En attente du coup de l’autre joueur."
        if self.game.phase == "setup":
            placed = sum(cop is not None for cop in self.game.cops)
            return "Placez le policier " + str(placed + 1) + " / 3"
        return "Sélectionnez un pion puis sa destination."

    def turn_hint(self):
        if self.game.phase == "setup":
            if self.controller.local_role == "thief":
                return "L’ordinateur place la police."
            return "Choisissez une intersection libre."
        if self.game.phase == "finished":
            return "Recommencez ou retournez au menu."
        return "Cliquez sur un pion, puis sur un point vert."

    def present_game(self, game, selected_node, notice):
        self.game = game
        self.selected_node = selected_node
        self.notice = notice
        self.screen = "game"
        self.draw_screen()

    def show_menu(self, selected_node=None, notice=""):
        self.selected_node = selected_node
        self.notice = notice
        self.screen = "menu"
        self.draw_screen()

    def show_local_modes(self):
        self.screen = "local_modes"
        self.draw_screen()

    def set_game_feedback(self, selected_node, notice):
        self.selected_node = selected_node
        self.notice = notice
        self.draw_screen()

    def show_settings(self):
        self.screen = "settings"
        self.draw_screen()

    def show_how_to_play(self):
        self.rules_return_screen = self.screen
        self.screen = "how_to_play"
        self.draw_screen()

    def leave_rules(self):
        self.screen = self.rules_return_screen
        self.draw_screen()

    def set_theme(self, theme):
        self.preferences["theme"] = theme
        self.palette = self.THEMES[theme]
        self.save_preferences()
        self.draw_screen()

    def show_appearance(self):
        self.screen = "appearance"
        self.draw_screen()

    def show_pawn_gallery(self):
        self.screen = "pawn_gallery"
        self.draw_screen()

    def set_board_style(self, style):
        self.preferences["board_style"] = style
        self.save_preferences()
        self.draw_screen()

    def set_skin(self, skin):
        self.preferences["skin"] = skin
        self.save_preferences()
        self.draw_screen()

    def choose_online_skin(self, skin):
        if self.pawn_assets.is_ready():
            self.set_skin(skin)
        else:
            self.download_online_skins(skin)

    def download_online_skins(self, selected_skin=None):
        if self.download_in_progress:
            return
        self.download_in_progress = True
        self.pending_skin = selected_skin
        self.download_status = "Téléchargement des pions CC0…"
        self.draw_screen()
        threading.Thread(
            target=self._download_online_skins_worker,
            daemon=True,
        ).start()

    def _download_online_skins_worker(self):
        try:
            self.pawn_assets.download()
        except PawnAssetDownloadError as error:
            callback = lambda message=str(error): self.finish_asset_download(message)
        else:
            callback = self.finish_asset_download
        try:
            self.root.after(0, callback)
        except tk.TclError:
            return

    def finish_asset_download(self, error_message=None):
        self.download_in_progress = False
        if error_message:
            self.download_status = "Erreur : " + error_message
            messagebox.showerror("Pions en ligne", error_message)
        else:
            self.download_status = "Pions téléchargés. Ils sont prêts hors ligne."
            self.photo_cache.clear()
            if self.pending_skin:
                self.preferences["skin"] = self.pending_skin
                self.save_preferences()
        self.pending_skin = None
        self.draw_screen()

    def set_color(self, key, color):
        self.preferences[key] = color
        self.save_preferences()
        self.draw_screen()

    def choose_custom_color(self, key):
        _rgb, color = colorchooser.askcolor(
            self.preferences[key], title="Choisir la couleur du pion"
        )
        if color:
            self.set_color(key, color)

    def draw_header(self, title, subtitle):
        self.draw_text(
            188, 42, title, size=22, color=self.palette["text"],
            weight="bold", anchor="w",
        )
        self.draw_text(
            188, 77, subtitle, size=11, color=self.palette["muted"], anchor="w",
        )
        self.canvas.create_line(
            188, 96, min(self.width - 40, 620), 96,
            fill=self.palette["surface_alt"], width=2,
        )

    def draw_text(
        self, x, y, text, size=11, color=None, weight="normal",
        anchor="center", width=None,
    ):
        options = {
            "text": text,
            "fill": color or self.palette["text"],
            "font": ("Segoe UI", size, weight),
            "anchor": anchor,
        }
        if width is not None:
            options["width"] = width
            options["justify"] = "left"
        return self.canvas.create_text(x, y, **options)

    def draw_card(self, x, y, width, height, fill, selected=False):
        outline = self.palette["accent"] if selected else self.palette["surface_alt"]
        self.draw_rounded_rectangle(
            x, y, width, height, 14,
            fill=fill,
            outline=outline,
            line_width=2 if selected else 1,
        )

    def draw_button(
        self, x, y, width, height, label, action, primary=False, font_size=10,
    ):
        index = len(self.hitboxes)
        is_hovered = self.hovered == index
        if primary:
            fill = self.palette["accent"] if not is_hovered else self.palette["text"]
            text_color = self.palette["background"]
            outline = fill
        else:
            fill = self.palette["surface_alt"] if is_hovered else self.palette["surface"]
            text_color = self.palette["text"]
            outline = self.palette["line"]
        self.draw_rounded_rectangle(
            x, y, width, height, 9,
            fill=fill,
            outline=outline,
            line_width=2 if is_hovered else 1,
        )
        self.draw_text(
            x + width / 2, y + height / 2, label,
            size=font_size, color=text_color, weight="bold",
        )
        self.add_hitbox(x, y, x + width, y + height, action)

    def add_hitbox(self, x1, y1, x2, y2, action):
        self.hitboxes.append((x1, y1, x2, y2, action))

    def on_board_click(self, event):
        for x1, y1, x2, y2, action in reversed(self.hitboxes):
            if x1 <= event.x <= x2 and y1 <= event.y <= y2:
                action()
                return

        if self.screen != "game":
            return
        node = self.node_at(event.x, event.y)
        if node is not None:
            self.controller.handle_board_click(node)
