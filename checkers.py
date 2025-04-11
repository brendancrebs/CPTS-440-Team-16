import sys
import copy

EMPTY, PLAYER1, PLAYER2, KING1, KING2 = '.', 'x', 'o', 'X', 'O'

def create_board():
    board = [[EMPTY]*8 for _ in range(8)]
    for row in range(3):
        for col in range((row+1)%2, 8, 2):
            board[row][col] = PLAYER2
    for row in range(5,8):
        for col in range((row+1)%2, 8, 2):
            board[row][col] = PLAYER1
    return board

def print_board(board):
    print("  0 1 2 3 4 5 6 7")
    for idx, row in enumerate(board):
        print(idx, ' '.join(row))
    print()

def opponent(player):
    return [PLAYER2, KING2] if player in [PLAYER1, KING1] else [PLAYER1, KING1]

def is_king(piece):
    return piece in [KING1, KING2]

def valid_moves(board, player):
    moves = []
    directions = [(-1,-1), (-1,1)] if player in [PLAYER1] else [(1,-1), (1,1)]
    if is_king(player):
        directions += [(-d[0], -d[1]) for d in directions]

    for r in range(8):
        for c in range(8):
            if board[r][c].lower() == player.lower():
                for dr, dc in directions:
                    nr, nc = r+dr, c+dc
                    if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] == EMPTY:
                        moves.append(((r,c),(nr,nc)))
                    elif 0 <= nr+dr < 8 and 0 <= nc+dc < 8:
                        if board[nr][nc] in opponent(player) and board[nr+dr][nc+dc] == EMPTY:
                            moves.append(((r,c),(nr+dr,nc+dc)))
    return moves

def move_piece(board, move):
    (r1,c1),(r2,c2) = move
    piece = board[r1][c1]
    board[r1][c1] = EMPTY
    board[r2][c2] = piece
    if abs(r2-r1) == 2:
        board[(r1+r2)//2][(c1+c2)//2] = EMPTY
    if piece == PLAYER1 and r2 == 0:
        board[r2][c2] = KING1
    if piece == PLAYER2 and r2 == 7:
        board[r2][c2] = KING2

def has_won(board, player):
    opponent_pieces = opponent(player)
    for row in board:
        for cell in row:
            if cell in opponent_pieces:
                return False
    return True

def heuristic(board, player):
    opponent_pieces = opponent(player)
    player_score = opponent_score = 0
    for row in board:
        for cell in row:
            if cell.lower() == player.lower():
                player_score += 3 if is_king(cell) else 1
            elif cell.lower() in [p.lower() for p in opponent_pieces]:
                opponent_score += 3 if is_king(cell) else 1
    return player_score - opponent_score

def minimax(board, depth, alpha, beta, maximizing_player, player):
    if depth == 0 or has_won(board, player) or has_won(board, opponent(player)[0]):
        return heuristic(board, player), None

    moves = valid_moves(board, player if maximizing_player else opponent(player)[0])
    if not moves:
        return heuristic(board, player), None

    best_move = None
    if maximizing_player:
        max_eval = float('-inf')
        for move in moves:
            new_board = copy.deepcopy(board)
            move_piece(new_board, move)
            eval, _ = minimax(new_board, depth-1, alpha, beta, False, player)
            if eval > max_eval:
                max_eval = eval
                best_move = move
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in moves:
            new_board = copy.deepcopy(board)
            move_piece(new_board, move)
            eval, _ = minimax(new_board, depth-1, alpha, beta, True, player)
            if eval < min_eval:
                min_eval = eval
                best_move = move
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval, best_move

def main():
    board = create_board()
    human_player = PLAYER1
    ai_player = PLAYER2
    current_player = PLAYER1

    while True:
        print_board(board)
        moves = valid_moves(board, current_player)
        if not moves:
            winner = opponent(current_player)[0]
            print(f"Player {winner} wins!")
            break

        if current_player == human_player:
            print(f"Your turn ({human_player}). Available moves:")
            for idx, move in enumerate(moves):
                print(f"{idx}: {move[0]} -> {move[1]}")
            try:
                choice = int(input("Select move number: "))
                if choice < 0 or choice >= len(moves):
                    raise ValueError
            except ValueError:
                print("Invalid input, try again.")
                continue
            move_piece(board, moves[choice])
        else:
            print("AI is thinking...")
            _, ai_move = minimax(board, 4, float('-inf'), float('inf'), True, ai_player)
            if ai_move:
                print(f"AI moves: {ai_move[0]} -> {ai_move[1]}")
                move_piece(board, ai_move)
            else:
                print("AI has no moves left!")
                break

        if has_won(board, current_player):
            print_board(board)
            print(f"Player {current_player} wins!")
            break

        current_player = opponent(current_player)[0]

if __name__ == "__main__":
    main()