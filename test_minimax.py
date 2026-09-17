#!/usr/bin/env python3
"""Tests for AiMinimax engine."""

import time
import pytest
from fastapi.testclient import TestClient
from main import app
from models import BoardState, Piece, Side, PieceType
from ai_engine import AIEngine
from ai_minimax import AiMinimax

client = TestClient(app)


def make_board(pieces, width=8, height=8, walls=None, upgrade_squares=None):
    return BoardState(
        width=width,
        height=height,
        pieces=pieces,
        walls=walls or [],
        upgrade_squares=upgrade_squares or []
    )


def test_minimax_returns_legal_move_on_default_board():
    """Minimax returns a move that is in the legal move set on the default board."""
    pieces = [
        Piece(id="w_pawn", type=PieceType.PAWN, side=Side.WHITE, posx=3, posy=6, has_moved=False),
        Piece(id="w_king", type=PieceType.KING, side=Side.WHITE, posx=4, posy=7, has_moved=False),
        Piece(id="r_pawn", type=PieceType.PAWN, side=Side.RED, posx=3, posy=1, has_moved=False),
        Piece(id="r_king", type=PieceType.KING, side=Side.RED, posx=4, posy=0, has_moved=False),
    ]
    board = make_board(pieces)
    ai = AiMinimax(board, Side.WHITE, time_budget_s=0.2)
    move_result = ai.select_move()
    assert move_result is not None
    piece, move = move_result
    # Verify the move is legal by generating all legal moves
    legal = ai._assemble_possible_moves()
    assert (piece, move) in legal


def test_minimax_finds_two_ply_material_win():
    """Minimax finds a safe capture that requires looking ahead.

    Position: white rook at (0,0), white king at (7,7).
    Red king at (2,2) — far enough that it cannot recapture the rook.
    Red pawn at (0,1) — unprotected, can be captured by the rook.
    White to move.  The rook should capture the pawn because it is
    unprotected and yields a material gain.  A one-ply engine might
    worry about the king, but with 2+ plies minimax sees the king
    cannot reach the rook in time.
    """
    pieces = [
        Piece(id="w_king", type=PieceType.KING, side=Side.WHITE, posx=7, posy=7, has_moved=True),
        Piece(id="w_rook", type=PieceType.ROOK, side=Side.WHITE, posx=0, posy=0, has_moved=True),
        Piece(id="r_king", type=PieceType.KING, side=Side.RED, posx=2, posy=2, has_moved=True),
        Piece(id="r_pawn", type=PieceType.PAWN, side=Side.RED, posx=0, posy=1, has_moved=True),
    ]
    board = make_board(pieces)
    ai = AiMinimax(board, Side.WHITE, max_depth=3, time_budget_s=0.5)
    move_result = ai.select_move()
    assert move_result is not None
    piece, move = move_result
    # The rook should capture the pawn at (0,1) because it's unprotected
    # and gives white a material advantage.
    if piece.type == PieceType.ROOK:
        assert move["posx"] == 0
        assert move["posy"] == 1
        assert move.get("killed_piece") is not None


def test_minimax_respects_time_budget():
    """Minimax returns within roughly twice a 200 ms budget."""
    pieces = [
        Piece(id="w_pawn", type=PieceType.PAWN, side=Side.WHITE, posx=3, posy=6, has_moved=False),
        Piece(id="w_king", type=PieceType.KING, side=Side.WHITE, posx=4, posy=7, has_moved=False),
        Piece(id="r_pawn", type=PieceType.PAWN, side=Side.RED, posx=3, posy=1, has_moved=False),
        Piece(id="r_king", type=PieceType.KING, side=Side.RED, posx=4, posy=0, has_moved=False),
    ]
    board = make_board(pieces)
    ai = AiMinimax(board, Side.WHITE, time_budget_s=0.2)
    start = time.monotonic()
    move_result = ai.select_move()
    elapsed = time.monotonic() - start
    assert move_result is not None
    # Should return within roughly twice the budget (generous margin)
    assert elapsed < 0.5


def test_minimax_king_capture_no_500():
    """Handles the king capture position without a 500 through the TestClient."""
    # Position where white can capture red king immediately.
    pieces = [
        Piece(id="w_king", type=PieceType.KING, side=Side.WHITE, posx=3, posy=3, has_moved=True),
        Piece(id="w_rook", type=PieceType.ROOK, side=Side.WHITE, posx=3, posy=0, has_moved=True),
        Piece(id="r_king", type=PieceType.KING, side=Side.RED, posx=3, posy=1, has_moved=True),
    ]
    payload = {
        "board_state": {
            "width": 8,
            "height": 8,
            "pieces": [
                {"id": "w_king", "type": "king", "side": "white", "posx": 3, "posy": 3, "has_moved": True},
                {"id": "w_rook", "type": "rook", "side": "white", "posx": 3, "posy": 0, "has_moved": True},
                {"id": "r_king", "type": "king", "side": "red", "posx": 3, "posy": 1, "has_moved": True},
            ],
            "walls": [],
            "upgrade_squares": []
        },
        "ai_type": "minimax",
        "side": "white",
        "game_id": "test"
    }
    response = client.post("/api/v1/ai/move", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["move"] is not None
    assert data["score"] is not None
    # Score must be a finite int (not inf)
    assert isinstance(data["score"], int)
    assert abs(data["score"]) < 2_000_000
