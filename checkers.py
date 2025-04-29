from __future__ import annotations
import copy
from typing import Dict, List, Tuple, Union

try:
    import pygame # type: ignore
except ImportError:
    pygame = None

ROWS = COLS = 8
SQUARE_SIZE = 100

RED: Tuple[int, int, int]   = (255, 0,   0)
WHITE: Tuple[int, int, int] = (255, 255, 255)

HUMAN  = RED
AI_WHITE = WHITE
GOLD = (255, 215, 0)
GREY = (128, 128, 128)
LIGHT = (238, 238, 210)
DARK = (118, 150, 86)

class Piece:
    PADDING = 15
    OUTLINE = 2

    def __init__(self, row: int, col: int, color: Tuple[int, int, int]):
        self.row = row
        self.col = col
        self.color = color
        self.king = False

    def make_king(self):
        self.king = True

    def move(self, row: int, col: int):
        self.row, self.col = row, col

    def draw(self, win):  # type: ignore[no-self]
        if pygame is None:
            raise RuntimeError("pygame not available; cannot draw")
        radius = SQUARE_SIZE // 2 - self.PADDING
        x = self.col * SQUARE_SIZE + SQUARE_SIZE // 2
        y = self.row * SQUARE_SIZE + SQUARE_SIZE // 2
        pygame.draw.circle(win, GREY, (x, y), radius + self.OUTLINE)
        pygame.draw.circle(win, self.color, (x, y), radius)
        if self.king:
            pygame.draw.circle(win, GOLD, (x, y), radius - 4, width=3)

    def __repr__(self):
        c = "W" if self.color == WHITE else "R"
        return f"{c}{'K' if self.king else ''}({self.row},{self.col})"


class Board:
    def __init__(self):
        self.board: List[List[Union[Piece, int]]] = []
        self.red_left = self.white_left = 12
        self.red_kings = self.white_kings = 0
        self._init_board()

    def _init_board(self):
        self.board.clear()
        for row in range(ROWS):
            self.board.append([])
            for col in range(COLS):
                if (row + col) % 2 == 1:
                    if row < 3:
                        self.board[row].append(Piece(row, col, RED))
                    elif row > 4:
                        self.board[row].append(Piece(row, col, WHITE))
                    else:
                        self.board[row].append(0)
                else:
                    self.board[row].append(0)

    def copy(self) -> "Board":
        return copy.deepcopy(self)

    def get_piece(self, row: int, col: int) -> Union[Piece, int]:
        return self.board[row][col]

    def get_all_pieces(self, color: Tuple[int, int, int]) -> List[Piece]:
        return [p for row in self.board for p in row if p != 0 and p.color == color]

    def move(self, piece: Piece, row: int, col: int):
        self.board[piece.row][piece.col], self.board[row][col] = 0, piece
        piece.move(row, col)
        if (row == ROWS - 1 and piece.color == RED) or (row == 0 and piece.color == WHITE):
            if not piece.king:
                piece.make_king()
                if piece.color == RED:
                    self.red_kings += 1
                else:
                    self.white_kings += 1

    def remove(self, pieces: List[Piece]):
        for p in pieces:
            self.board[p.row][p.col] = 0
            if p.color == RED:
                self.red_left -= 1
            else:
                self.white_left -= 1

    def winner(self) -> Union[str, None]:
        if self.red_left <= 0:
            return "White"
        if self.white_left <= 0:
            return "Red"

        # Second win condition is to check if there are no legal moves for a player.
        if not self.has_legal_moves(RED):
            return "White"
        if not self.has_legal_moves(WHITE):
            return "Red"

        return None

    def has_legal_moves(self, color: Tuple[int, int, int]) -> bool:
        pieces = self.get_all_pieces(color)
        for piece in pieces:
            if self.get_valid_moves(piece):
                return True
        return False

    def get_valid_moves(self, piece: Piece) -> Dict[Tuple[int, int], List[Piece]]:
        moves: Dict[Tuple[int, int], List[Piece]] = {}
        left, right = piece.col - 1, piece.col + 1
        row = piece.row
        if piece.color == RED or piece.king:
            moves.update(self._traverse_left(row + 1, ROWS, 1, piece.color, left))
            moves.update(self._traverse_right(row + 1, ROWS, 1, piece.color, right))
        if piece.color == WHITE or piece.king:
            moves.update(self._traverse_left(row - 1, -1, -1, piece.color, left))
            moves.update(self._traverse_right(row - 1, -1, -1, piece.color, right))
        return moves

    def _traverse_left(self, start, stop, step, color, left, skipped=None):
        if skipped is None:
            skipped = []
        moves, last = {}, []
        for r in range(start, stop, step):
            if left < 0:
                break
            current = self.board[r][left]
            if current == 0:
                if skipped and not last:
                    break
                moves[(r, left)] = skipped + last
                if last:
                    moves.update(
                        self._traverse_left(r + step, stop, step, color, left - 1, skipped + last)
                    )
                    moves.update(
                        self._traverse_right(r + step, stop, step, color, left + 1, skipped + last)
                    )
                break
            elif current.color == color:
                break
            else:
                if last:
                    break
                last = [current]
            left -= 1
        return moves

    def _traverse_right(self, start, stop, step, color, right, skipped=None):
        if skipped is None:
            skipped = []
        moves, last = {}, []
        for r in range(start, stop, step):
            if right >= COLS:
                break
            current = self.board[r][right]
            if current == 0:
                if skipped and not last:
                    break
                moves[(r, right)] = skipped + last
                if last:
                    moves.update(
                        self._traverse_left(r + step, stop, step, color, right - 1, skipped + last)
                    )
                    moves.update(
                        self._traverse_right(r + step, stop, step, color, right + 1, skipped + last)
                    )
                break
            elif current.color == color:
                break
            else:
                if last:
                    break
                last = [current]
            right += 1
        return moves

    def draw(self, win):  # type: ignore[no-self]
        if pygame is None:
            raise RuntimeError("pygame not available; cannot draw")
        for row in range(ROWS):
            for col in range(COLS):
                color = LIGHT if (row + col) % 2 == 0 else DARK
                pygame.draw.rect(
                    win, color, (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
                )
        for row in range(ROWS):
            for col in range(COLS):
                piece = self.board[row][col]
                if piece != 0:
                    piece.draw(win)
