# CPTS-440-Team-16
This is the CPTS 440 semester project for team 16. The project is a interactive checkers playing agent.

## Files

### Checkers.py

This file contains the game logic for checkers. It contains objects for the board and the pieces. The board
is represented by an 2D array. Each place in the 2D array can be occupied by a piece object or a zero to
indicate an empty spot on the board.

Each Piece object maintains its own color, board position, and king status. The draw method of the Piece class takes care of rendering the piece on the screen, including a visual outline and a crown if the piece has been promoted to a king. Movement is animated by updating a piece's row and column, and the board class handles the logic of moving a piece on the grid, including detecting when a piece reaches the opposite end and should be promoted.

### tournament.py

### minimax.py

### mcts.py