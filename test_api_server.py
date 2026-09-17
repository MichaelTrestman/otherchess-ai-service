#!/usr/bin/env python3
"""
Test script to verify the AI API server works correctly.
"""

import requests
import json
from models import BoardState, Piece, Wall, UpgradeSquare, Side, PieceType

def create_test_request():
    """Create a test request for the AI API."""
    pieces = [
        # White pieces
        {"id": "w_pawn_1", "type": "pawn", "side": "white", "posx": 0, "posy": 1, "has_moved": False},
        {"id": "w_knight_1", "type": "knight", "side": "white", "posx": 1, "posy": 0, "has_moved": False},
        {"id": "w_king", "type": "king", "side": "white", "posx": 4, "posy": 0, "has_moved": False},
        
        # Red pieces
        {"id": "r_pawn_1", "type": "pawn", "side": "red", "posx": 0, "posy": 6, "has_moved": False},
        {"id": "r_knight_1", "type": "knight", "side": "red", "posx": 1, "posy": 7, "has_moved": False},
        {"id": "r_king", "type": "king", "side": "red", "posx": 4, "posy": 7, "has_moved": False},
    ]
    
    return {
        "board_state": {
            "width": 8,
            "height": 8,
            "pieces": pieces,
            "walls": [{"posx": 3, "posy": 3}],
            "upgrade_squares": [{"posx": 0, "posy": 0}, {"posx": 7, "posy": 7}]
        },
        "ai_type": "smart2",
        "side": "white",
        "game_id": "test_game"
    }

def test_api_endpoints():
    """Test the AI API endpoints."""
    base_url = "http://localhost:8000"
    
    print("Testing AI API Server")
    print("=" * 40)
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/health")
        if response.status_code == 200:
            print("✓ Health check passed")
            print(f"  Response: {response.json()}")
        else:
            print(f"✗ Health check failed: {response.status_code}")
    except Exception as e:
        print(f"✗ Health check error: {e}")
        return False
    
    # Test AI types endpoint
    try:
        response = requests.get(f"{base_url}/api/v1/ai/types")
        if response.status_code == 200:
            print("✓ AI types endpoint passed")
            print(f"  Response: {response.json()}")
        else:
            print(f"✗ AI types endpoint failed: {response.status_code}")
    except Exception as e:
        print(f"✗ AI types endpoint error: {e}")
    
    # Test AI move endpoint
    try:
        test_request = create_test_request()
        response = requests.post(
            f"{base_url}/api/v1/ai/move", 
            json=test_request,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            print("✓ AI move endpoint passed")
            move_response = response.json()
            print(f"  AI Type: {move_response['ai_type']}")
            print(f"  Side: {move_response['side']}")
            print(f"  Piece: {move_response['move']['piece_id']}")
            print(f"  From: ({move_response['move']['from_posx']}, {move_response['move']['from_posy']})")
            print(f"  To: ({move_response['move']['to_posx']}, {move_response['move']['to_posy']})")
            print(f"  Score: {move_response['score']}")
            print(f"  Thinking time: {move_response['thinking_time_ms']}ms")
        else:
            print(f"✗ AI move endpoint failed: {response.status_code}")
            print(f"  Error: {response.text}")
    except Exception as e:
        print(f"✗ AI move endpoint error: {e}")
    
    return True

if __name__ == "__main__":
    test_api_endpoints()
