"""Minimax opponent for Police et voleur."""

from copy import deepcopy


class MinimaxAI:
    def __init__(self, depth=4):
        self.depth = depth

    def choose_action(self, game):
        player = "police" if game.phase == "setup" else game.current_player
        actions = self.legal_actions(game, player)
        if not actions:
            return None

        maximizing = player == "police"
        best_action = actions[0]
        best_score = float("-inf") if maximizing else float("inf")
        for action in actions:
            next_game = deepcopy(game)
            self.apply_action(next_game, player, action)
            score = self._search(
                next_game,
                self.depth - 1,
                float("-inf"),
                float("inf"),
            )
            if (maximizing and score > best_score) or (
                not maximizing and score < best_score
            ):
                best_score = score
                best_action = action
        return best_action

    def _search(self, game, depth, alpha, beta):
        if game.phase == "finished":
            return 10_000 if game.winner == "police" else -10_000
        if depth == 0:
            return self.evaluate(game)

        player = "police" if game.phase == "setup" else game.current_player
        actions = self.legal_actions(game, player)
        if not actions:
            return 10_000 if player == "thief" else -10_000

        if player == "police":
            value = float("-inf")
            for action in actions:
                next_game = deepcopy(game)
                self.apply_action(next_game, player, action)
                value = max(value, self._search(next_game, depth - 1, alpha, beta))
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return value

        value = float("inf")
        for action in actions:
            next_game = deepcopy(game)
            self.apply_action(next_game, player, action)
            value = min(value, self._search(next_game, depth - 1, alpha, beta))
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value

    @staticmethod
    def legal_actions(game, player):
        if game.phase == "setup":
            placed = sum(cop is not None for cop in game.cops)
            allowed = game.inner_nodes if placed == 0 else game.boundary_nodes
            return [
                ("place", node)
                for node in sorted(allowed - game.occupied_nodes())
            ]

        pieces = [game.thief] if player == "thief" else [
            node for node in game.cops if node is not None
        ]
        return [
            ("move", origin, destination)
            for origin in pieces
            for destination in sorted(game.legal_destinations(player, origin))
        ]

    @staticmethod
    def apply_action(game, player, action):
        if action[0] == "place":
            game.place_cop(action[1])
        else:
            game.move(player, action[1], action[2])

    @staticmethod
    def evaluate(game):
        center_distances = MinimaxAI._distances_from(game, "C")
        thief_distances = MinimaxAI._distances_from(game, game.thief)

        thief_moves = len(game.legal_destinations("thief", game.thief))
        cop_distances = [
            thief_distances.get(cop, len(game.nodes))
            for cop in game.cops if cop is not None
        ]
        nearest_cop = min(cop_distances, default=len(game.nodes))
        return (
            center_distances.get(game.thief, len(game.nodes)) * 12
            - nearest_cop * 2
            - thief_moves * 3
        )

    @staticmethod
    def _distances_from(game, start):
        distances = {start: 0}
        frontier = [start]
        while frontier:
            node = frontier.pop(0)
            for neighbor in game.adjacency[node]:
                if neighbor not in distances:
                    distances[neighbor] = distances[node] + 1
                    frontier.append(neighbor)
        return distances
