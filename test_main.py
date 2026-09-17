#!/usr/bin/env python3
"""FastAPI TestClient tests for main.py endpoints."""

import pytest
from fastapi.testclient import TestClient
from main import app
from models import BoardState, Piece, Side, PieceType

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "ai_engine": "ready"}


def test_ai_types():
    response = client.get("/api/v1/ai/types")
    assert response.status_code == 200
    data = response.json()
    assert set(data["ai_types"]) == {"smart2", "greedy", "smart_fast", "random"}
    assert data["default"] == "smart2"


def test_ai_move():
    payload = {
        "board_state": {
            "width": 8,
            "height": 8,
            "pieces": [
                {"id": "w_pawn", "type": "pawn", "side": "white", "posx": 3, "posy": 6, "has_moved": False},
                {"id": "w_king", "type": "king", "side": "white", "posx": 4, "posy": 7, "has_moved": False},
                {"id": "r_pawn", "type": "pawn", "side": "red", "posx": 3, "posy": 1, "has_moved": False},
                {"id": "r_king", "type": "king", "side": "red", "posx": 4, "posy": 0, "has_moved": False},
            ],
            "walls": [],
            "upgrade_squares": []
        },
        "ai_type": "random",
        "side": "white",
        "game_id": "test"
    }
    response = client.post("/api/v1/ai/move", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["move"] is not None
    assert data["ai_type"] == "random"
    assert data["side"] == "white"


def test_ai_move_invalid_ai_type():
    payload = {
        "board_state": {
            "width": 8,
            "height": 8,
            "pieces": [],
            "walls": [],
            "upgrade_squares": []
        },
        "ai_type": "nonexistent",
        "side": "white",
        "game_id": "test"
    }
    response = client.post("/api/v1/ai/move", json=payload)
    assert response.status_code == 422


def test_ai_move_invalid_board():
    payload = {
        "board_state": {
            "width": 8,
            "height": 8,
            "pieces": [
                {"id": "p1", "type": "pawn", "side": "white", "posx": 0, "posy": 0, "has_moved": False},
                {"id": "p2", "type": "pawn", "side": "white", "posx": 0, "posy": 0, "has_moved": False},
            ],
            "walls": [],
            "upgrade_squares": []
        },
        "ai_type": "random",
        "side": "white",
        "game_id": "test"
    }
    response = client.post("/api/v1/ai/move", json=payload)
    assert response.status_code == 400
