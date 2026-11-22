"""Board layout and rules for Police et voleur."""

import math


def build_board():
    nodes = {"C": (0.0, 0.0)}
    adjacency = {"C": set()}

    def add_node(name, point):
        nodes[name] = point
        adjacency[name] = set()

    def connect(first, second):
        adjacency[first].add(second)
        adjacency[second].add(first)

    directions = {
        "N": (0.0, -1.0, 1.0, 0.0),
        "E": (1.0, 0.0, 0.0, 1.0),
        "S": (0.0, 1.0, -1.0, 0.0),
        "W": (-1.0, 0.0, 0.0, -1.0),
    }

    for direction, (dx, dy, tx, ty) in directions.items():
        inner = (dx * 0.28, dy * 0.28)
        curve = (dx * 0.76, dy * 0.76)
        outer = (dx, dy)
        add_node("I_" + direction, inner)
        add_node("X_" + direction, curve)
        add_node("O_" + direction, outer)
        connect("C", "I_" + direction)
        connect("I_" + direction, "X_" + direction)
        connect("X_" + direction, "O_" + direction)

    boundary_nodes = ["O_" + direction for direction in directions]
    endpoint_offset = 0.37
    endpoint_depth = math.sqrt(1 - endpoint_offset**2)

    for direction, (dx, dy, tx, ty) in directions.items():
        for side, sign in (("L", -1), ("R", 1)):
            name = "B_" + direction + side
            point = (
                dx * endpoint_depth + tx * sign * endpoint_offset,
                dy * endpoint_depth + ty * sign * endpoint_offset,
            )
            add_node(name, point)
            connect(name, "X_" + direction)
            boundary_nodes.append(name)

    boundary_nodes.sort(
        key=lambda name: math.atan2(nodes[name][1], nodes[name][0])
    )
    for index, name in enumerate(boundary_nodes):
        connect(name, boundary_nodes[(index + 1) % len(boundary_nodes)])

    inner_nodes = ["I_" + direction for direction in directions]
    inner_nodes.sort(key=lambda name: math.atan2(nodes[name][1], nodes[name][0]))
    for index, name in enumerate(inner_nodes):
        connect(name, inner_nodes[(index + 1) % len(inner_nodes)])

    return nodes, adjacency, set(inner_nodes), set(boundary_nodes), directions


class GameState:
    def __init__(self):
        (
            self.nodes,
            self.adjacency,
            self.inner_nodes,
            self.boundary_nodes,
            self.directions,
        ) = build_board()
        self.cops = [None, None, None]
        self.thief = "C"
        self.phase = "setup"
        self.current_player = "police"
        self.winner = None

    def occupied_nodes(self):
        occupied = {self.thief}
        occupied.update(node for node in self.cops if node is not None)
        return occupied

    def place_cop(self, node):
        if self.phase != "setup" or node in self.occupied_nodes():
            return False

        placed = sum(cop is not None for cop in self.cops)
        allowed_nodes = self.inner_nodes if placed == 0 else self.boundary_nodes
        if node not in allowed_nodes:
            return False

        self.cops[placed] = node
        if placed == 2:
            self.phase = "play"
            self.current_player = "thief"
        return True

    def legal_destinations(self, player, origin):
        if player == "thief":
            owns_origin = self.thief == origin
        else:
            owns_origin = origin in self.cops

        if not owns_origin:
            return set()
        return self.adjacency[origin] - self.occupied_nodes()

    def move(self, player, origin, destination):
        if self.phase != "play" or player != self.current_player:
            return False
        if destination not in self.legal_destinations(player, origin):
            return False

        if player == "thief":
            self.thief = destination
            if self.thief == "C":
                self.phase = "finished"
                self.winner = "thief"
            elif not self.legal_destinations("thief", self.thief):
                self.phase = "finished"
                self.winner = "police"
            else:
                self.current_player = "police"
        else:
            cop_index = self.cops.index(origin)
            self.cops[cop_index] = destination
            if not self.legal_destinations("thief", self.thief):
                self.phase = "finished"
                self.winner = "police"
            else:
                self.current_player = "thief"
        return True
