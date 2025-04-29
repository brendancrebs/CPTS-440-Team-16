from __future__ import annotations

import copy
from typing import List, Tuple, Dict
import math
import time
import zlib

from checkers import Board, WHITE, RED

PIECE_VALUE = 1.0
KING_VALUE = 2.5 
POSITION_WEIGHTS = [
    [0, 1, 0, 1, 0, 1, 0, 1],
    [1, 0, 2, 0, 2, 0, 1, 0],
    [0, 2, 0, 3, 0, 2, 0, 1],
    [2, 0, 3, 0, 3, 0, 2, 0],
    [0, 3, 0, 4, 0, 3, 0, 2],
    [3, 0, 4, 0, 4, 0, 3, 0],
    [0, 5, 0, 6, 0, 5, 0, 4],
    [7, 0, 7, 0, 7, 0, 7, 0] 
]
EXACT = 0
LOWERBOUND = 1
UPPERBOUND = 2


def evaluate_board(board: Board) -> float:
    """Evaluate the board position from WHITE's perspective with improved heuristics."""
    # 1. First priority - detect winning positions
    winner = board.winner()
    if winner == "White":
        return float("inf")
    if winner == "Red":
        return float("-inf")
    
    # Give score for more material value
    white_material = board.white_left * PIECE_VALUE + board.white_kings * KING_VALUE
    red_material = board.red_left * PIECE_VALUE + board.red_kings * KING_VALUE
    material_score = white_material - red_material

    white_pieces = board.get_all_pieces(WHITE)
    red_pieces = board.get_all_pieces(RED)
    white_kings = [p for p in white_pieces if p.king]
    red_kings = [p for p in red_pieces if p.king]
    
    # Track and punish position repetition
    board_str = board_to_string(board)
    repetition_count = position_history.get(board_str, 0)
    repetition_penalty = repetition_count * 2.0
    
    # Endgame pursuit logic
    endgame_score = 0
    is_endgame = (board.white_left + board.red_left) <= 10
    
    if is_endgame:
        # Center control incentive
        white_centrality = sum(7 - (abs(k.row-3.5) + abs(k.col-3.5)) for k in white_kings) / len(white_kings) if white_kings else 0
        red_centrality = sum(7 - (abs(k.row-3.5) + abs(k.col-3.5)) for k in red_kings) / len(red_kings) if red_kings else 0
        endgame_score += 0.2 * (red_centrality - white_centrality)
        
        # Pursue enemy pieces when ahead in material
        if white_material > red_material:
            material_advantage = white_material - red_material
            
            total_distance = 0
            min_distance = float('inf')
            for wp in white_pieces:
                piece_min_distance = float('inf')
                for rp in red_pieces:
                    distance = abs(wp.row - rp.row) + abs(wp.col - rp.col)
                    piece_min_distance = min(piece_min_distance, distance)
                    total_distance += distance
                min_distance = min(min_distance, piece_min_distance)
            
            endgame_score -= min_distance * material_advantage
            
            # Penalize total distance to encourage all pieces to pursue
            avg_distance = total_distance / (len(white_pieces) * len(red_pieces)) if red_pieces and white_pieces else 0
            endgame_score -= avg_distance * 0.5 * material_advantage
            
            # We give a huge inceptive for capturing a piece in the late game
            endgame_score += 5.0 * material_advantage * (12 - board.red_left)
        
        elif red_material > white_material:
            material_advantage = red_material - white_material
            
            total_distance = 0
            min_distance = float('inf')
            for rp in red_pieces:
                piece_min_distance = float('inf')
                for wp in white_pieces:
                    distance = abs(rp.row - wp.row) + abs(rp.col - wp.col)
                    piece_min_distance = min(piece_min_distance, distance)
                    total_distance += distance
                min_distance = min(min_distance, piece_min_distance)
            
            endgame_score += min_distance * material_advantage
            
            avg_distance = total_distance / (len(white_pieces) * len(red_pieces)) if red_pieces and white_pieces else 0
            endgame_score += avg_distance * 0.5 * material_advantage
        
            endgame_score -= 5.0 * material_advantage * (12 - board.white_left)
        
        # Additional tempo consideration - punish moves that don't make progress
        remaining_pieces = board.white_left + board.red_left
        if remaining_pieces < 6:
            aggression_multiplier = (8 - remaining_pieces) * 2.0
            endgame_score *= (1.0 + aggression_multiplier)
    
    # Special case for kings-only endgames
    if board.white_kings > 0 and board.white_left == board.white_kings and board.red_kings > 0 and board.red_left == board.red_kings:
        # Centralization of the kigs
        white_kings = [p for p in board.get_all_pieces(WHITE) if p.king]
        red_kings = [p for p in board.get_all_pieces(RED) if p.king]
        
        white_centrality = sum(7 - (abs(k.row-3.5) + abs(k.col-3.5)) for k in white_kings) / len(white_kings) if white_kings else 0
        red_centrality = sum(7 - (abs(k.row-3.5) + abs(k.col-3.5)) for k in red_kings) / len(red_kings) if red_kings else 0
        
        # Add strong centralization bonus in king vs king endgames
        endgame_score += (white_centrality - red_centrality) * 3.0
        
        # Distance between kings
        min_king_distance = float('inf')
        for wk in white_kings:
            for rk in red_kings:
                distance = abs(wk.row - rk.row) + abs(wk.col - rk.col)
                min_king_distance = min(min_king_distance, distance)
        
        # White wants to minimize distance in king endgames (hunt down red kings)
        if len(white_kings) >= len(red_kings):
            endgame_score -= min_king_distance * 2.0
        else:
            endgame_score += min_king_distance * 2.0
    
    # Final weighted score
    final_score = material_score + endgame_score - repetition_penalty
    
    return final_score

def simulate_move(board: Board, piece, move: Tuple[int, int], skips):
    new_board = board.copy()
    new_piece = new_board.get_piece(piece.row, piece.col)
    new_board.move(new_piece, move[0], move[1])
    if skips:
        new_board.remove([new_board.get_piece(p.row, p.col) for p in skips])
    return new_board

def get_all_moves(board: Board, color) -> List[Board]:
    """Get all possible moves, enforcing mandatory captures."""
    all_pieces = board.get_all_pieces(color)
    all_moves = []
    capture_moves = []
    
    for piece in all_pieces:
        valid_moves = board.get_valid_moves(piece)
        for move, skipped in valid_moves.items():
            if skipped:
                capture_moves.append(simulate_move(board, piece, move, skipped))

    if capture_moves:
        return capture_moves
    
    for piece in all_pieces:
        valid_moves = board.get_valid_moves(piece)
        for move, skipped in valid_moves.items():
            all_moves.append(simulate_move(board, piece, move, skipped))
    
    return all_moves

def zobrist_hash(board: Board) -> int:
    board_str = board_to_string(board)
    return zlib.adler32(board_str.encode())

transposition_table = {}

def minimax_with_timeout(position: Board, depth: int, maximizing_color, 
                         start_time: float, time_limit: float,
                         alpha=float("-inf"), beta=float("inf")):
    """Minimax search with transposition table and timeout checks"""
    # Check if we've exceeded the time limit
    if time.time() - start_time > time_limit * 0.95:  # 95% of time limit
        raise TimeoutError("Search time limit exceeded")
    
    # Check if position is a terminal state
    winner = position.winner()
    if depth == 0 or winner:
        if winner == "White":
            return float("inf"), position
        if winner == "Red":
            return float("-inf"), position
        return evaluate_board(position), position

    # Generate unique hash for the board position
    position_hash = zobrist_hash(position)
    
    # Check transposition table
    if position_hash in transposition_table:
        tt_entry = transposition_table[position_hash]
        if tt_entry['depth'] >= depth:
            if tt_entry['node_type'] == EXACT:
                return tt_entry['score'], tt_entry['best_board']
            elif tt_entry['node_type'] == LOWERBOUND and tt_entry['score'] >= beta:
                return tt_entry['score'], tt_entry['best_board']
            elif tt_entry['node_type'] == UPPERBOUND and tt_entry['score'] <= alpha:
                return tt_entry['score'], tt_entry['best_board']
    
    # Regular alpha-beta search if not found in table or insufficient depth
    orig_alpha = alpha  # Store original alpha for node type determination
    
    if maximizing_color == WHITE:
        max_eval = float("-inf")
        best_board = None
        for child in get_all_moves(position, WHITE):
            eval_score, _ = minimax_with_timeout(child, depth - 1, RED, start_time, time_limit, alpha, beta)
            if eval_score > max_eval:
                max_eval, best_board = eval_score, child
            alpha = max(alpha, max_eval)
            if beta <= alpha:
                break
        
        # Determine node type and store in transposition table
        node_type = EXACT
        if max_eval <= orig_alpha:
            node_type = UPPERBOUND
        elif max_eval >= beta:
            node_type = LOWERBOUND
            
        transposition_table[position_hash] = {
            'score': max_eval,
            'best_board': best_board,
            'depth': depth,
            'node_type': node_type
        }
        
        return max_eval, best_board
    else:
        min_eval = float("inf")
        best_board = None
        for child in get_all_moves(position, RED):
            eval_score, _ = minimax_with_timeout(child, depth - 1, WHITE, start_time, time_limit, alpha, beta)
            if eval_score < min_eval:
                min_eval, best_board = eval_score, child
            beta = min(beta, min_eval)
            if beta <= alpha:
                break
                
        # Determine node type and store in transposition table
        node_type = EXACT
        if min_eval <= orig_alpha:
            node_type = UPPERBOUND
        elif min_eval >= beta:
            node_type = LOWERBOUND
            
        transposition_table[position_hash] = {
            'score': min_eval,
            'best_board': best_board,
            'depth': depth,
            'node_type': node_type
        }
        
        return min_eval, best_board
    
# increase depth in the late game to prevent draws
def get_dynamic_depth(board: Board, base_depth: int) -> int:
    total_pieces = board.white_left + board.red_left
    
    if total_pieces <= 4:
        return base_depth + 4
    elif total_pieces <= 6:
        return base_depth + 3
    elif total_pieces <= 8:
        return base_depth + 2
    elif total_pieces <= 12:
        return base_depth + 1
    else:
        return base_depth

position_history: Dict[str, int] = {}

def board_to_string(board: Board) -> str:
    """Convert a board to a string for position tracking."""
    result = ""
    for row in range(8):
        for col in range(8):
            piece = board.get_piece(row, col)
            if piece == 0:
                result += "0"
            elif piece.color == WHITE:
                result += "W" if not piece.king else "K"
            else:
                result += "R" if not piece.king else "Q"
    return result

def best_move(board: Board, depth: int, color, time_limit: float = 500.0) -> Board:
    global position_history
    
    start_time = time.time()
    best_board = None
    
    # Start with iterative deepening from depth 1
    for current_depth in range(1, depth + 5):
        if time.time() - start_time > time_limit * 0.8:
            break
        
        # Get dynamic depth based on pieces remaining
        actual_depth = min(current_depth, get_dynamic_depth(board, current_depth))
        
        try:
            # Run minimax with a time check
            _, new_board = minimax_with_timeout(board, actual_depth, color, start_time, time_limit)
            if new_board is not None:
                best_board = new_board
        except TimeoutError:
            break
    
    # Return the original board if no move found
    if best_board is None:
        return board
    
    # Track position for repetition detection
    board_str = board_to_string(best_board)
    position_history[board_str] = position_history.get(board_str, 0) + 1
    
    # Clean up history if it gets too large
    if len(position_history) > 500:
        keys = list(position_history.keys())
        for key in keys[:250]:
            position_history.pop(key)
            
    return best_board
