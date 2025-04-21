from __future__ import annotations

import itertools, random, sys, time, argparse
from typing import Dict, Callable, Tuple, Optional

import pygame  # type: ignore

from checkers import Board, RED, WHITE, ROWS, COLS, SQUARE_SIZE
from minimax import best_move as minimax_move
from mcts import best_move as mcts_move

K_FACTOR = 32
ROUNDS = 10
MOVE_DELAY = 0.1
VISUALIZE = False

def expected(r_a: float, r_b: float) -> float:
    return 1.0 / (1 + 10 ** ((r_b - r_a) / 400))

def rate(rating_a: float, rating_b: float, score_a: float) -> Tuple[float, float]:
    ra_new = rating_a + K_FACTOR * (score_a - expected(rating_a, rating_b))
    rb_new = rating_b + K_FACTOR * ((1 - score_a) - expected(rating_b, rating_a))
    return ra_new, rb_new

MAX_PLIES = 160  # 80 moves

def play_game(move_fn_a: Callable, move_fn_b: Callable, *, swap_colors: bool, win: Optional[pygame.Surface]):
    board = Board()
    turn = RED
    ply = 0

    clock: Optional[pygame.time.Clock] = pygame.time.Clock() if win else None

    def draw_board():
        if win is None:
            return
        board.draw(win)
        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        if MOVE_DELAY:
            time.sleep(MOVE_DELAY)
        if clock:
            clock.tick(60)

    draw_board()

    while ply < MAX_PLIES and board.winner() is None:
        if (turn == RED) ^ swap_colors:
            board = move_fn_a(board, turn)
        else:
            board = move_fn_b(board, turn)
        turn = WHITE if turn == RED else RED
        ply += 1
        draw_board()

    winner = board.winner()
    if winner == "Red":
        return 1 if not swap_colors else 0
    if winner == "White":
        return 0 if not swap_colors else 1
    return 0.5

# Registering the bots here.
BOTS: Dict[str, Callable] = {
    "minimax_d4": lambda b, c: minimax_move(b, 4, c),
    "minimax_d12": lambda b, c: minimax_move(b, 6, c),
    # "mcts_1k":    lambda b, c: mcts_move(b, c, simulations=1000),
}
ratings: Dict[str, float] = {name: 1500.0 for name in BOTS}

def main():
    global VISUALIZE
    parser = argparse.ArgumentParser()
    parser.add_argument("--visual", action="store_true", help="Show Pygame board during games")
    args = parser.parse_args()
    if args.visual:
        VISUALIZE = True

    win = None
    if VISUALIZE:
        pygame.init()
        win = pygame.display.set_mode((COLS * SQUARE_SIZE, ROWS * SQUARE_SIZE))
        pygame.display.set_caption("AI Tournament Viewer")

    pairs = list(itertools.combinations(BOTS.items(), 2))
    for rnd in range(ROUNDS):
        random.shuffle(pairs)
        for (name_a, bot_a), (name_b, bot_b) in pairs:
            # Game 1 (A = Red)
            result = play_game(bot_a, bot_b, swap_colors=False, win=win)
            ratings[name_a], ratings[name_b] = rate(ratings[name_a], ratings[name_b], result)
            # Game 2 (A = White)
            result = play_game(bot_a, bot_b, swap_colors=True, win=win)
            ratings[name_a], ratings[name_b] = rate(ratings[name_a], ratings[name_b], result)

    if win:
        pygame.quit()

    print("\nFinal Elo ratings:")
    for name, rating in sorted(ratings.items(), key=lambda x: x[1], reverse=True):
        print(f"{name:12}  {rating:7.1f}")

if __name__ == "__main__":
    main()
