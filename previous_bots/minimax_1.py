from __future__ import annotations

import copy
from typing import List, Tuple

from checkers import Board, WHITE, RED

def evaluate_board(board: Board) -> float:
    # Simple piece counting heuristic. Kings worth 1.5
    return (
        (board.white_left + 0.5 * board.white_kings)
        - (board.red_left + 0.5 * board.red_kings)
    )

def simulate_move(board: Board, piece, move: Tuple[int, int], skips):
    new_board = board.copy()
    new_piece = new_board.get_piece(piece.row, piece.col)
    new_board.move(new_piece, move[0], move[1])
    if skips:
        new_board.remove([new_board.get_piece(p.row, p.col) for p in skips])
    return new_board

def get_all_moves(board: Board, color) -> List[Board]:
    moves = []
    for piece in board.get_all_pieces(color):
        for move, skips in board.get_valid_moves(piece).items():
            moves.append(simulate_move(board, piece, move, skips))
    return moves

def minimax(position: Board, depth: int, maximizing_color, alpha=float("-inf"), beta=float("inf")):
    winner = position.winner()
    if depth == 0 or winner:
        # terminal score, infinite if checkmate, else heuristic
        if winner == "White":
            return float("inf"), position
        if winner == "Red":
            return float("-inf"), position
        return evaluate_board(position), position

    if maximizing_color == WHITE:
        max_eval = float("-inf")
        best_board = None
        for child in get_all_moves(position, WHITE):
            eval_score, _ = minimax(child, depth - 1, RED, alpha, beta)
            if eval_score > max_eval:
                max_eval, best_board = eval_score, child
            alpha = max(alpha, max_eval)
            if beta <= alpha:
                break
        return max_eval, best_board
    else:
        min_eval = float("inf")
        best_board = None
        for child in get_all_moves(position, RED):
            eval_score, _ = minimax(child, depth - 1, WHITE, alpha, beta)
            if eval_score < min_eval:
                min_eval, best_board = eval_score, child
            beta = min(beta, min_eval)
            if beta <= alpha:
                break
        return min_eval, best_board

def best_move(board: Board, depth: int, color) -> Board:
    _, new_board = minimax(board, depth, color)
    if new_board is None:
        # no legal moves, return original board so caller can detect loss
        return board
    return new_board
