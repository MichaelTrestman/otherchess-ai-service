from typing import List, Dict, Any, Optional, Tuple
import time
from models import BoardState, Piece, Side, PieceType
from ai_base import AIBase


class AiMinimax(AIBase):
    """
    Variable-depth minimax engine with alpha-beta pruning and a time budget.

    Supports any number of sides.  The side that asks for a move is the
    *root* side; at its ply we *maximise* the evaluation.  Every opponent
    ply is treated as a *minimising* ply (all opponents cooperate to
    hurt the root player).  This keeps the classic alpha-beta mechanics
    intact.

    Ply convention:
        * ``current_depth`` counts plies from the root (0 = root position).
        * The side to move at each ply is determined by
          ``_side_to_move_at_depth``, which cycles through the sides
          actually present on the board.  It is **not** derived from
          parity (even/odd), so the engine correctly handles games
          with more than two sides or sides eliminated mid-search.
    """

    # Large finite mate score, scaled by depth so faster wins score higher.
    MATE_SCORE = 1_000_000

    # How far the engine may search when no time budget is given.
    # The time budget is the primary limit; the depth cap is a safety rail.
    DEFAULT_MAX_DEPTH = 20

    # Time budget in seconds (None => no limit).
    DEFAULT_TIME_BUDGET_S = 2.0

    def __init__(
        self,
        board_state: BoardState,
        side: Side,
        max_depth: Optional[int] = None,
        time_budget_s: Optional[float] = None,
    ):
        super().__init__(board_state, side)
        self.root_side = side
        self.max_depth = max_depth if max_depth is not None else self.DEFAULT_MAX_DEPTH
        self.time_budget_s = (
            time_budget_s if time_budget_s is not None else self.DEFAULT_TIME_BUDGET_S
        )
        self._cutoff_time: Optional[float] = None
        self._last_depth_reached: int = 0

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def select_move(self) -> Optional[Tuple[Piece, Dict[str, Any]]]:
        """Return the best move found within the time/depth budget."""
        legal = self._assemble_possible_moves()
        if not legal:
            return None

        # Start the clock.
        self._cutoff_time = time.monotonic() + self.time_budget_s
        self._last_depth_reached = 0

        best_move: Optional[Tuple[Piece, Dict[str, Any]]] = None
        best_score = -float("inf")

        # Iterative deepening – try depth 1, 2, … up to max_depth.
        # After each completed depth the best move is *guaranteed* to be at
        # least that good; if the clock runs out we still have a move.
        for depth in range(1, self.max_depth + 1):
            if self._out_of_time():
                break

            iteration_best: Optional[Tuple[Piece, Dict[str, Any]]] = None
            iteration_score = -float("inf")
            alpha = -float("inf")
            beta = float("inf")

            for piece, move in legal:
                if self._out_of_time():
                    break

                child = self._simulate_move(piece, move)
                score = self._minimax(
                    child,
                    depth - 1,
                    alpha,
                    beta,
                    current_depth=1,
                )

                if score > iteration_score:
                    iteration_score = score
                    iteration_best = (piece, move)

                alpha = max(alpha, score)

            # Only commit the iteration result if we finished it (or at
            # least examined *some* moves this depth).
            if iteration_best is not None and not self._out_of_time():
                best_move = iteration_best
                best_score = iteration_score
                self._last_depth_reached = depth

        # Fallback: if we never finished a single iteration, just use the
        # first legal move (should never happen on reasonable boards).
        if best_move is None:
            best_move = legal[0]
            best_score = self._evaluate_board(self._simulate_move(best_move[0], best_move[1]))

        self._best_score = best_score
        return best_move

    def get_move_score(self, move_result: Tuple[Piece, Dict[str, Any]]) -> int:
        """Score of the *current* move result (called by AIEngine)."""
        score = getattr(self, "_best_score", 0)
        return int(max(min(score, self.MATE_SCORE), -self.MATE_SCORE))

    # ------------------------------------------------------------------
    # Minimax core
    # ------------------------------------------------------------------

    def _minimax(
        self,
        board_state: BoardState,
        depth: int,
        alpha: float,
        beta: float,
        current_depth: int,
    ) -> float:
        """Recursive minimax with alpha-beta pruning."""

        # Time-out check – return a safe heuristic when the clock runs out.
        if self._out_of_time():
            return self._evaluate_board(board_state)

        side_to_move = self._side_to_move_at_depth(current_depth, board_state)
        maximizing = side_to_move == self.root_side

        # Terminal: root king gone = losing (score scaled by depth)
        if self._find_king(board_state, self.root_side) is None:
            return -(self.MATE_SCORE - current_depth)

        # Terminal: all opponent kings gone = winning (score scaled by depth)
        if not any(p.side != self.root_side and p.type == PieceType.KING for p in board_state.pieces):
            return self.MATE_SCORE - current_depth

        # Generate legal moves once for this node
        legal = self._all_legal_moves_for_side(board_state, side_to_move)

        # Stalemate: side to move has no legal moves
        if not legal:
            return 0.0

        # Leaf – static evaluation
        if depth <= 0:
            return self._evaluate_board(board_state)

        if maximizing:
            value = -float("inf")
            for piece, move in legal:
                child = self._simulate_move_on_board(board_state, piece, move)
                score = self._minimax(
                    child,
                    depth - 1,
                    alpha,
                    beta,
                    current_depth=current_depth + 1,
                )
                value = max(value, score)
                alpha = max(alpha, value)
                if beta <= alpha:
                    break
            return value
        else:
            value = float("inf")
            for piece, move in legal:
                child = self._simulate_move_on_board(board_state, piece, move)
                score = self._minimax(
                    child,
                    depth - 1,
                    alpha,
                    beta,
                    current_depth=current_depth + 1,
                )
                value = min(value, score)
                beta = min(beta, value)
                if beta <= alpha:
                    break
            return value

    # ------------------------------------------------------------------
    # Terminal / leaf evaluation helpers
    # ------------------------------------------------------------------

    def _evaluate_board(self, board_state: BoardState) -> float:
        """
        Static evaluation from the root side's perspective.
        Positive = good for root, negative = bad for root.
        Uses AIBase material scoring for consistency.
        """
        score = 0.0

        root_material = 0
        opp_material = 0

        for piece in board_state.pieces:
            piece_type = piece.type.value if hasattr(piece.type, 'value') else piece.type
            value = self.piece_values.get(piece_type, 100)
            if piece.side == self.root_side:
                root_material += value
            else:
                opp_material += value

        # Material balance is the dominant term
        score += (root_material - opp_material)

        # King proximity bonus (king closer to enemy pieces = slight threat)
        # This is a tiny term so it doesn't override material.
        root_king = self._find_king(board_state, self.root_side)
        if root_king:
            for piece in board_state.pieces:
                if piece.side != self.root_side:
                    dist = abs(piece.posx - root_king.posx) + abs(piece.posy - root_king.posy)
                    if dist <= 2:
                        score -= 10  # enemy near our king is slightly bad

        # Pawn advancement toward upgrade squares (small bonus)
        for piece in board_state.pieces:
            if piece.type == PieceType.PAWN and board_state.upgrade_squares:
                dist = self._nearest_upgrade_distance(
                    piece.posx, piece.posy, board_state.upgrade_squares
                )
                bonus = max(0, (8 - dist)) * 5
                if piece.side == self.root_side:
                    score += bonus
                else:
                    score -= bonus

        # Development bonus for undeveloped minors on back rank (tiny)
        for piece in board_state.pieces:
            if piece.type in (PieceType.KNIGHT, PieceType.BISHOP, PieceType.ROOK):
                if piece.side == self.root_side:
                    starting_rank = 0 if self.root_side == Side.WHITE else board_state.height - 1
                    if piece.posy == starting_rank:
                        score -= 3

        return score

    # ------------------------------------------------------------------
    # Move generation helpers
    # ------------------------------------------------------------------

    def _all_legal_moves_for_side(
        self, board_state: BoardState, side: Side
    ) -> List[Tuple[Piece, Dict[str, Any]]]:
        """Generate all legal moves for *side* on *board_state* (king-safe)."""
        ai = AIBase(board_state, side)
        return ai._assemble_possible_moves()

    def _side_to_move_at_depth(self, depth: int, board_state: BoardState) -> Side:
        """
        Determine which side moves at ply *depth*.
        The move order is the fixed cycle white -> red -> blue.
        Depth 0 = root side's turn, depth 1 = next side, etc.
        Reads *board_state* so sides eliminated mid-search are dropped.
        """
        cycle = [Side.WHITE, Side.RED, Side.BLUE]
        # Build the list of *actually present* sides in cycle order
        present_sides = [s for s in cycle if any(p.side == s for p in board_state.pieces)]

        if not present_sides:
            return self.root_side

        # Find root side's index in the present-sides list
        try:
            root_idx = present_sides.index(self.root_side)
        except ValueError:
            root_idx = 0

        idx = (root_idx + depth) % len(present_sides)
        return present_sides[idx]

    # ------------------------------------------------------------------
    # Small helpers
    # ------------------------------------------------------------------

    def _find_king(self, board_state: BoardState, side: Side) -> Optional[Piece]:
        for p in board_state.pieces:
            if p.side == side and p.type == PieceType.KING:
                return p
        return None

    def _nearest_upgrade_distance(
        self, x: int, y: int, squares: List[Any]
    ) -> float:
        if not squares:
            return float("inf")
        min_d = float("inf")
        for sq in squares:
            sx = sq.posx if hasattr(sq, "posx") else sq["posx"]
            sy = sq.posy if hasattr(sq, "posy") else sq["posy"]
            min_d = min(min_d, abs(x - sx) + abs(y - sy))
        return min_d

    def _out_of_time(self) -> bool:
        if self._cutoff_time is None:
            return False
        return time.monotonic() >= self._cutoff_time
