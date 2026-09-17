# OtherChess rules

The rules this service must implement. The game server (the Rails application) is authoritative for play; this document is the reference for the AI's move generator and evaluator.

## Board

- Any `width` by `height`, rectangular boards allowed. Coordinates are integer `(posx, posy)`, zero based, `0 <= posx < width`, `0 <= posy < height`.
- There is no fixed starting position. The starting piece array for each side is part of the board configuration, so there is no home row and no notion of "forward".
- Two special square types can be placed anywhere:
  - **Wall.** Impassable and unoccupiable. Cannot be captured, moved, or landed on. Blocks the rays of sliding pieces. Knights jump over walls but cannot land on one.
  - **Upgrade square.** A pawn that ends its move on an upgrade square is promoted to a queen immediately, as part of the same move. There is no choice of piece. Other pieces are unaffected by upgrade squares.

## Sides

- Sides are named colors: `white`, `red`, `blue`. A board uses two or more of them.
- Sides move in a fixed cycle. With all three present the order is white, red, blue.
- Every side is an enemy of every other side; any piece may capture any piece of a different side.

## Pieces

Knight, bishop, rook, queen, and king move as in standard chess, with these interactions:

- A sliding piece (bishop, rook, queen) moves along its ray until it reaches the board edge, a wall, or a piece. It may capture the first enemy piece on the ray and stops there. It cannot pass a wall or a friendly piece.
- A knight moves in the usual L shape and ignores whatever is between; it cannot land on a wall or a friendly piece.
- A king moves one square in any of the eight directions.

Captures replace the enemy piece on the destination square.

## Pawns

Pawns have no direction.

- **Step.** One square in any of the four cardinal directions (north, south, east, west) onto an empty square. Never a capture.
- **Capture.** One square in any of the four diagonal directions onto a square holding an enemy piece. Never onto an empty square.
- **First move.** A pawn that has not moved yet (`has_moved` is false) may instead move two squares in one cardinal direction, if both squares are empty. This is a non capturing move.
- **Promotion.** Only by ending a move on an upgrade square; the pawn becomes a queen as part of that move. A pawn can otherwise reach any square on the board without promoting.

## Castling

Supported by the game server. Neither the king nor the rook has moved, the rook is three or four squares from the king in a straight cardinal line, and every square between them is empty. The king moves two squares toward the rook and the rook is placed on the square the king passed over. Castling through or into a wall is impossible because the path must be clear.

{/* TODO: confirm with the game server whether the AI is expected to generate castling moves in v1, or only to accept them from opponents */}

## Not in the rules

- No en passant.
- No check or checkmate detection by the game server: a move that leaves your own king attacked is accepted, and a king can be captured. A side with no king is out of the game.

## Rule for the AI

The AI must never produce a move that leaves its own king capturable on the next opponent turn. Treat such moves as if they were illegal: filter them out of the candidate set before evaluation, not merely score them low.

## Data model

The service receives the board as `BoardState` (see `models.py`): `width`, `height`, `pieces[]` with `id`, `type`, `side`, `posx`, `posy`, `has_moved`, plus `walls[]` and `upgrade_squares[]` as coordinate lists. It returns one `Move`: the piece id, from and to coordinates, the captured piece if any, and `promotion_type` when the move promotes.
