#!/usr/bin/env python3
"""
Tests for OtherChess variant rules.
Covers pawn movement, promotion, king safety, and AI registration.
"""

import pytest
from models import BoardState, Piece, Side, PieceType, Wall, UpgradeSquare
from ai_engine import AIEngine
from ai_base import AIBase
from ai_random import AiRandom
from ai_smart_fast import AiSmartFast


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def engine():
    return AIEngine()


def make_board(pieces, width=8, height=8, walls=None, upgrade_squares=None):
    return BoardState(
        width=width,
        height=height,
        pieces=pieces,
        walls=walls or [],
        upgrade_squares=upgrade_squares or []
    )


# ---------------------------------------------------------------------------
# AI Registration
# ---------------------------------------------------------------------------

def test_all_ai_types_registered(engine):
    types = engine.get_available_ai_types()
    assert set(types) == {"smart2", "greedy", "smart_fast", "random"}


def test_smart_fast_calculates_move(engine):
    pieces = [
        Piece(id="w_pawn", type=PieceType.PAWN, side=Side.WHITE, posx=3, posy=6, has_moved=False),
        Piece(id="w_king", type=PieceType.KING, side=Side.WHITE, posx=4, posy=7, has_moved=False),
        Piece(id="r_pawn", type=PieceType.PAWN, side=Side.RED, posx=3, posy=1, has_moved=False),
        Piece(id="r_king", type=PieceType.KING, side=Side.RED, posx=4, posy=0, has_moved=False),
    ]
    board = make_board(pieces)
    result = engine.calculate_move(board, "smart_fast", Side.WHITE)
    assert result is not None
    assert result["move"] is not None


def test_random_calculates_move(engine):
    pieces = [
        Piece(id="w_pawn", type=PieceType.PAWN, side=Side.WHITE, posx=3, posy=6, has_moved=False),
        Piece(id="w_king", type=PieceType.KING, side=Side.WHITE, posx=4, posy=7, has_moved=False),
        Piece(id="r_pawn", type=PieceType.PAWN, side=Side.RED, posx=3, posy=1, has_moved=False),
        Piece(id="r_king", type=PieceType.KING, side=Side.RED, posx=4, posy=0, has_moved=False),
    ]
    board = make_board(pieces)
    result = engine.calculate_move(board, "random", Side.WHITE)
    assert result is not None
    assert result["move"] is not None


# ---------------------------------------------------------------------------
# Pawn Movement (variant rules)
# ---------------------------------------------------------------------------

def test_pawn_cardinal_step():
    """Pawn can step one square in any cardinal direction."""
    pieces = [
        Piece(id="wp", type=PieceType.PAWN, side=Side.WHITE, posx=3, posy=3, has_moved=True),
    ]
    board = make_board(pieces)
    ai = AIBase(board, Side.WHITE)
    moves = ai._calculate_moves_for_piece(pieces[0])
    coords = {(m["posx"], m["posy"]) for m in moves}
    assert coords == {(3, 2), (3, 4), (2, 3), (4, 3)}


def test_pawn_diagonal_capture():
    """Pawn captures diagonally."""
    pieces = [
        Piece(id="wp", type=PieceType.PAWN, side=Side.WHITE, posx=3, posy=3, has_moved=True),
        Piece(id="rp", type=PieceType.PAWN, side=Side.RED, posx=4, posy=4, has_moved=True),
    ]
    board = make_board(pieces)
    ai = AIBase(board, Side.WHITE)
    moves = ai._calculate_moves_for_piece(pieces[0])
    capture_moves = [m for m in moves if m.get("killed_piece")]
    assert len(capture_moves) == 1
    assert capture_moves[0]["posx"] == 4
    assert capture_moves[0]["posy"] == 4


def test_pawn_cannot_step_diagonally_onto_empty():
    """Pawn cannot move diagonally to an empty square."""
    pieces = [
        Piece(id="wp", type=PieceType.PAWN, side=Side.WHITE, posx=3, posy=3, has_moved=True),
    ]
    board = make_board(pieces)
    ai = AIBase(board, Side.WHITE)
    moves = ai._calculate_moves_for_piece(pieces[0])
    diagonal_coords = {(m["posx"], m["posy"]) for m in moves
                       if abs(m["posx"] - 3) == 1 and abs(m["posy"] - 3) == 1}
    assert diagonal_coords == set()


def test_pawn_two_square_first_move():
    """Pawn that has not moved can move two squares in a cardinal direction."""
    pieces = [
        Piece(id="wp", type=PieceType.PAWN, side=Side.WHITE, posx=3, posy=3, has_moved=False),
    ]
    board = make_board(pieces)
    ai = AIBase(board, Side.WHITE)
    moves = ai._calculate_moves_for_piece(pieces[0])
    coords = {(m["posx"], m["posy"]) for m in moves}
    # Cardinal single steps + two-square first moves
    assert (3, 1) in coords  # north 2
    assert (3, 5) in coords  # south 2
    assert (1, 3) in coords  # west 2
    assert (5, 3) in coords  # east 2


def test_pawn_two_square_blocked_by_piece():
    """Two-square move is blocked if intermediate square is occupied."""
    pieces = [
        Piece(id="wp", type=PieceType.PAWN, side=Side.WHITE, posx=3, posy=3, has_moved=False),
        Piece(id="rp", type=PieceType.PAWN, side=Side.RED, posx=3, posy=4, has_moved=True),
    ]
    board = make_board(pieces)
    ai = AIBase(board, Side.WHITE)
    moves = ai._calculate_moves_for_piece(pieces[0])
    coords = {(m["posx"], m["posy"]) for m in moves}
    assert (3, 5) not in coords  # blocked by piece at (3,4)


def test_pawn_two_square_blocked_by_wall():
    """Two-square move is blocked if intermediate square is a wall."""
    pieces = [
        Piece(id="wp", type=PieceType.PAWN, side=Side.WHITE, posx=3, posy=3, has_moved=False),
    ]
    walls = [Wall(posx=3, posy=4)]
    board = make_board(pieces, walls=walls)
    ai = AIBase(board, Side.WHITE)
    moves = ai._calculate_moves_for_piece(pieces[0])
    coords = {(m["posx"], m["posy"]) for m in moves}
    assert (3, 5) not in coords  # blocked by wall at (3,4)


# ---------------------------------------------------------------------------
# Promotion
# ---------------------------------------------------------------------------

def test_pawn_promotion_on_upgrade_square():
    """Pawn ending on upgrade square promotes to queen."""
    pieces = [
        Piece(id="wp", type=PieceType.PAWN, side=Side.WHITE, posx=3, posy=1, has_moved=True),
    ]
    upgrade_squares = [UpgradeSquare(posx=3, posy=0)]
    board = make_board(pieces, upgrade_squares=upgrade_squares)
    ai = AIBase(board, Side.WHITE)
    moves = ai._calculate_moves_for_piece(pieces[0])
    north_move = [m for m in moves if m["posx"] == 3 and m["posy"] == 0]
    assert len(north_move) == 1
    assert north_move[0].get("promotion_type") == PieceType.QUEEN


def test_no_promotion_off_upgrade_square():
    """Pawn not on upgrade square does not promote."""
    pieces = [
        Piece(id="wp", type=PieceType.PAWN, side=Side.WHITE, posx=3, posy=2, has_moved=True),
    ]
    upgrade_squares = [UpgradeSquare(posx=3, posy=0)]
    board = make_board(pieces, upgrade_squares=upgrade_squares)
    ai = AIBase(board, Side.WHITE)
    moves = ai._calculate_moves_for_piece(pieces[0])
    for m in moves:
        assert m.get("promotion_type") is None


# ---------------------------------------------------------------------------
# King Safety
# ---------------------------------------------------------------------------

def test_king_safety_filters_move_leaving_king_exposed():
    """Moving a blocking piece away that exposes the king is filtered out."""
    pieces = [
        Piece(id="wk", type=PieceType.KING, side=Side.WHITE, posx=4, posy=4, has_moved=True),
        Piece(id="wp", type=PieceType.PAWN, side=Side.WHITE, posx=4, posy=3, has_moved=True),
        Piece(id="rq", type=PieceType.QUEEN, side=Side.RED, posx=4, posy=0, has_moved=True),
    ]
    board = make_board(pieces)
    ai = AIBase(board, Side.WHITE)
    moves = ai._assemble_possible_moves()
    pawn_moves = [m for p, m in moves if p.id == "wp"]
    coords = {(m["posx"], m["posy"]) for m in pawn_moves}
    # Pawn can move to (4,2) which still blocks the queen
    assert (4, 2) in coords
    # Pawn cannot move to (3,3) or (5,3) as that exposes the king
    assert (3, 3) not in coords
    assert (5, 3) not in coords


def test_king_safety_blocks_move_into_check():
    """King cannot move into a square attacked by opponent."""
    pieces = [
        Piece(id="wk", type=PieceType.KING, side=Side.WHITE, posx=4, posy=4, has_moved=True),
        Piece(id="rq", type=PieceType.QUEEN, side=Side.RED, posx=4, posy=6, has_moved=True),
    ]
    board = make_board(pieces)
    ai = AIBase(board, Side.WHITE)
    all_moves = ai._assemble_possible_moves()
    # King should not be able to move to (4,5) because queen attacks it
    bad_move = [m for p, m in all_moves if p.id == "wk" and m["posx"] == 4 and m["posy"] == 5]
    assert len(bad_move) == 0


def test_king_safety_allows_safe_moves():
    """King can move to safe squares."""
    pieces = [
        Piece(id="wk", type=PieceType.KING, side=Side.WHITE, posx=4, posy=4, has_moved=True),
        Piece(id="rq", type=PieceType.QUEEN, side=Side.RED, posx=4, posy=6, has_moved=True),
    ]
    board = make_board(pieces)
    ai = AIBase(board, Side.WHITE)
    all_moves = ai._assemble_possible_moves()
    # King should be able to move to (3,3) which is not attacked by queen
    safe_move = [m for p, m in all_moves if p.id == "wk" and m["posx"] == 3 and m["posy"] == 3]
    assert len(safe_move) == 1


# ---------------------------------------------------------------------------
# Sliding Pieces and Walls
# ---------------------------------------------------------------------------

def test_rook_stopped_by_wall():
    """Rook cannot move through or onto a wall."""
    pieces = [
        Piece(id="wr", type=PieceType.ROOK, side=Side.WHITE, posx=3, posy=3, has_moved=True),
    ]
    walls = [Wall(posx=3, posy=5)]
    board = make_board(pieces, walls=walls)
    ai = AIBase(board, Side.WHITE)
    moves = ai._calculate_moves_for_piece(pieces[0])
    coords = {(m["posx"], m["posy"]) for m in moves}
    assert (3, 5) not in coords  # cannot land on wall
    assert (3, 6) not in coords  # cannot pass through wall


def test_bishop_stopped_by_wall():
    """Bishop cannot move through or onto a wall."""
    pieces = [
        Piece(id="wb", type=PieceType.BISHOP, side=Side.WHITE, posx=3, posy=3, has_moved=True),
    ]
    walls = [Wall(posx=5, posy=5)]
    board = make_board(pieces, walls=walls)
    ai = AIBase(board, Side.WHITE)
    moves = ai._calculate_moves_for_piece(pieces[0])
    coords = {(m["posx"], m["posy"]) for m in moves}
    assert (5, 5) not in coords  # cannot land on wall
    assert (6, 6) not in coords  # cannot pass through wall


def test_knight_jumps_over_wall():
    """Knight can jump over walls."""
    pieces = [
        Piece(id="wn", type=PieceType.KNIGHT, side=Side.WHITE, posx=3, posy=3, has_moved=True),
    ]
    walls = [Wall(posx=3, posy=4)]
    board = make_board(pieces, walls=walls)
    ai = AIBase(board, Side.WHITE)
    moves = ai._calculate_moves_for_piece(pieces[0])
    coords = {(m["posx"], m["posy"]) for m in moves}
    assert (4, 5) in coords  # knight jumps over wall at (3,4)


def test_knight_cannot_land_on_wall():
    """Knight cannot land on a wall."""
    pieces = [
        Piece(id="wn", type=PieceType.KNIGHT, side=Side.WHITE, posx=3, posy=3, has_moved=True),
    ]
    walls = [Wall(posx=4, posy=5)]
    board = make_board(pieces, walls=walls)
    ai = AIBase(board, Side.WHITE)
    moves = ai._calculate_moves_for_piece(pieces[0])
    coords = {(m["posx"], m["posy"]) for m in moves}
    assert (4, 5) not in coords


# ---------------------------------------------------------------------------
# Move Validation (AIEngine)
# ---------------------------------------------------------------------------

def test_validate_move_pawn_cardinal_step():
    """Engine validates pawn cardinal step."""
    engine = AIEngine()
    pieces = [
        Piece(id="wp", type=PieceType.PAWN, side=Side.WHITE, posx=3, posy=3, has_moved=True),
    ]
    board = make_board(pieces)
    from models import Move
    move = Move(piece_id="wp", from_posx=3, from_posy=3, to_posx=3, to_posy=4)
    assert engine.validate_move(board, move)


def test_validate_move_pawn_diagonal_without_capture_invalid():
    """Engine rejects diagonal pawn move without capture."""
    engine = AIEngine()
    pieces = [
        Piece(id="wp", type=PieceType.PAWN, side=Side.WHITE, posx=3, posy=3, has_moved=True),
    ]
    board = make_board(pieces)
    from models import Move
    move = Move(piece_id="wp", from_posx=3, from_posy=3, to_posx=4, to_posy=4)
    assert not engine.validate_move(board, move)


def test_validate_move_pawn_two_square_first():
    """Engine validates two-square first move."""
    engine = AIEngine()
    pieces = [
        Piece(id="wp", type=PieceType.PAWN, side=Side.WHITE, posx=3, posy=3, has_moved=False),
    ]
    board = make_board(pieces)
    from models import Move
    move = Move(piece_id="wp", from_posx=3, from_posy=3, to_posx=3, to_posy=5)
    assert engine.validate_move(board, move)


def test_validate_move_pawn_two_square_not_first_invalid():
    """Engine rejects two-square move when pawn has moved."""
    engine = AIEngine()
    pieces = [
        Piece(id="wp", type=PieceType.PAWN, side=Side.WHITE, posx=3, posy=3, has_moved=True),
    ]
    board = make_board(pieces)
    from models import Move
    move = Move(piece_id="wp", from_posx=3, from_posy=3, to_posx=3, to_posy=5)
    assert not engine.validate_move(board, move)


# ---------------------------------------------------------------------------
# Multi-side games
# ---------------------------------------------------------------------------

def test_three_sides_can_capture_each_other():
    """Any side can capture any other side."""
    pieces = [
        Piece(id="wp", type=PieceType.PAWN, side=Side.WHITE, posx=3, posy=3, has_moved=True),
        Piece(id="rp", type=PieceType.PAWN, side=Side.RED, posx=4, posy=4, has_moved=True),
        Piece(id="bp", type=PieceType.PAWN, side=Side.BLUE, posx=2, posy=2, has_moved=True),
    ]
    board = make_board(pieces)
    ai = AIBase(board, Side.WHITE)
    moves = ai._calculate_moves_for_piece(pieces[0])
    # White pawn should be able to capture both red and blue pawns
    captures = [m for m in moves if m.get("killed_piece")]
    assert len(captures) == 2


# ---------------------------------------------------------------------------
# Edge Cases
# ---------------------------------------------------------------------------

def test_no_moves_when_king_is_only_piece_and_surrounded():
    """If king is surrounded by walls, no moves available."""
    pieces = [
        Piece(id="wk", type=PieceType.KING, side=Side.WHITE, posx=3, posy=3, has_moved=True),
    ]
    walls = [
        Wall(posx=2, posy=2), Wall(posx=3, posy=2), Wall(posx=4, posy=2),
        Wall(posx=2, posy=3), Wall(posx=4, posy=3),
        Wall(posx=2, posy=4), Wall(posx=3, posy=4), Wall(posx=4, posy=4),
    ]
    board = make_board(pieces, walls=walls)
    ai = AIBase(board, Side.WHITE)
    moves = ai._assemble_possible_moves()
    assert len(moves) == 0


def test_pawn_at_edge_cannot_move_off_board():
    """Pawn at board edge cannot move off board."""
    pieces = [
        Piece(id="wp", type=PieceType.PAWN, side=Side.WHITE, posx=0, posy=0, has_moved=True),
    ]
    board = make_board(pieces)
    ai = AIBase(board, Side.WHITE)
    moves = ai._calculate_moves_for_piece(pieces[0])
    coords = {(m["posx"], m["posy"]) for m in moves}
    assert coords == {(0, 1), (1, 0)}
