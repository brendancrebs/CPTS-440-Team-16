from __future__ import annotations

import math, random
from typing import List, Tuple

from checkers import Board, WHITE, RED
from minimax import get_all_moves

C_PUCT = 1.4    
ROLLOUT_LIMIT = 60 

class Node:
    __slots__ = ("board", "color", "parent", "children", "N", "W")

    def __init__(self, board: Board, color, parent=None):
        self.board: Board = board
        self.color = color
        self.parent: Node | None = parent
        self.children: List[Node] = []
        self.N = 0
        self.W = 0.0

    @property
    def Q(self) -> float:
        return self.W / self.N if self.N else 0.0


def uct_select(node: Node) -> Node:
    log_N = math.log(node.N + 1)  # +1 avoids log(0)
    def ucb(n: Node):
        if n.N == 0:
            return float("inf")
        return n.Q + C_PUCT * math.sqrt(log_N / n.N)
    return max(node.children, key=ucb)


def expand(node: Node):
    for child_board in get_all_moves(node.board, node.color):
        child = Node(child_board, WHITE if node.color == RED else RED, parent=node)
        node.children.append(child)


def rollout(board: Board, color) -> float:
    turn, ply = color, 0
    b = board.copy()
    while ply < ROLLOUT_LIMIT and not b.winner():
        moves = get_all_moves(b, turn)
        if not moves:
            break
        b = random.choice(moves)
        turn = WHITE if turn == RED else RED
        ply += 1
    winner = b.winner()
    if winner == "White":
        return 1.0
    if winner == "Red":
        return 0.0
    return 0.5  # draw


def backpropagate(path: List[Node], value: float):
    for node in reversed(path):
        node.N += 1
        node.W += value
        value = 1.0 - value


def best_move(board: Board, color, simulations: int = 800) -> Board:
    """Return a *new* Board after *color* plays, using given simulations."""
    root = Node(board, color)
    expand(root)

    for _ in range(simulations):
        node, path = root, [root]
        while node.children:
            node = uct_select(node)
            path.append(node)
        if node.N > 0 and not node.board.winner():
            expand(node)
            if node.children:
                node = random.choice(node.children)
                path.append(node)
        value = rollout(node.board, node.color)
        backpropagate(path, value)

    best_child = max(root.children, key=lambda n: n.N)
    return best_child.board
