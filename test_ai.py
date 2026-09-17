#!/usr/bin/env python3
"""
Test script for the AI API.
Creates sample board states and tests AI move generation.
"""

import json
from models import BoardState, Piece, Wall, UpgradeSquare, Side, PieceType
from ai_engine import AIEngine

def create_sample_board():
    """Create a sample board state for testing."""
    pieces = [
        # White pieces
        Piece(id="w_pawn_1", type=PieceType.PAWN, side=Side.WHITE, posx=0, posy=1, has_moved=False),
        Piece(id="w_knight_1", type=PieceType.KNIGHT, side=Side.WHITE, posx=1, posy=0, has_moved=False),
        Piece(id="w_bishop_1", type=PieceType.BISHOP, side=Side.WHITE, posx=2, posy=0, has_moved=False),
        Piece(id="w_rook_1", type=PieceType.ROOK, side=Side.WHITE, posx=0, posy=0, has_moved=False),
        Piece(id="w_queen", type=PieceType.QUEEN, side=Side.WHITE, posx=3, posy=0, has_moved=False),
        Piece(id="w_king", type=PieceType.KING, side=Side.WHITE, posx=4, posy=0, has_moved=False),
        
        # Red pieces
        Piece(id="r_pawn_1", type=PieceType.PAWN, side=Side.RED, posx=0, posy=6, has_moved=False),
        Piece(id="r_knight_1", type=PieceType.KNIGHT, side=Side.RED, posx=1, posy=7, has_moved=False),
        Piece(id="r_bishop_1", type=PieceType.BISHOP, side=Side.RED, posx=2, posy=7, has_moved=False),
        Piece(id="r_rook_1", type=PieceType.ROOK, side=Side.RED, posx=0, posy=7, has_moved=False),
        Piece(id="r_queen", type=PieceType.QUEEN, side=Side.RED, posx=3, posy=7, has_moved=False),
        Piece(id="r_king", type=PieceType.KING, side=Side.RED, posx=4, posy=7, has_moved=False),
        
        # Blue pieces (moved to different positions to avoid conflicts)
        Piece(id="b_pawn_1", type=PieceType.PAWN, side=Side.BLUE, posx=7, posy=6, has_moved=False),
        Piece(id="b_knight_1", type=PieceType.KNIGHT, side=Side.BLUE, posx=6, posy=7, has_moved=False),
        Piece(id="b_bishop_1", type=PieceType.BISHOP, side=Side.BLUE, posx=5, posy=7, has_moved=False),
        Piece(id="b_rook_1", type=PieceType.ROOK, side=Side.BLUE, posx=7, posy=7, has_moved=False),
        Piece(id="b_queen", type=PieceType.QUEEN, side=Side.BLUE, posx=6, posy=6, has_moved=False),
        Piece(id="b_king", type=PieceType.KING, side=Side.BLUE, posx=5, posy=6, has_moved=False),
    ]
    
    walls = [
        Wall(posx=3, posy=3),
        Wall(posx=4, posy=4)
    ]
    
    upgrade_squares = [
        UpgradeSquare(posx=3, posy=7),
        UpgradeSquare(posx=4, posy=7),
        UpgradeSquare(posx=0, posy=0),
        UpgradeSquare(posx=1, posy=0)
    ]
    
    return BoardState(
        width=8,
        height=8,
        pieces=pieces,
        walls=walls,
        upgrade_squares=upgrade_squares
    )

def test_ai_engine():
    """Test the AI engine with different AI types."""
    print("Testing AI Engine...")
    
    # Create AI engine
    ai_engine = AIEngine()
    
    # Test available AI types
    print(f"Available AI types: {ai_engine.get_available_ai_types()}")
    
    # Create sample board
    board = create_sample_board()
    print(f"Created board: {board.width}x{board.height} with {len(board.pieces)} pieces")
    
    # Test each AI type
    for ai_type in ["smart2", "greedy"]:
        print(f"\n--- Testing {ai_type.upper()} AI ---")
        
        # Test for each side
        for side in [Side.WHITE, Side.RED, Side.BLUE]:
            print(f"  Testing {side} side...")
            
            try:
                result = ai_engine.calculate_move(board, ai_type, side)
                
                if result:
                    move = result["move"]
                    score = result["score"]
                    print(f"    Move: {move.piece_id} from ({move.from_posx},{move.from_posy}) to ({move.to_posx},{move.to_posy})")
                    print(f"    Score: {score}")
                    
                    # Validate the move
                    is_valid = ai_engine.validate_move(board, move)
                    print(f"    Valid move: {is_valid}")
                else:
                    print(f"    No move found")
                    
            except Exception as e:
                print(f"    Error: {str(e)}")

def test_board_validation():
    """Test board state validation."""
    print("\n--- Testing Board Validation ---")
    
    # Valid board
    valid_board = create_sample_board()
    print(f"Valid board validation: {valid_board.is_valid()}")
    
    # Debug: check what's wrong with the board
    print(f"Board dimensions: {valid_board.width}x{valid_board.height}")
    print(f"Number of pieces: {len(valid_board.pieces)}")
    
    # Check each piece position
    for piece in valid_board.pieces:
        if piece.posx >= valid_board.width or piece.posy >= valid_board.height:
            print(f"Piece {piece.id} at invalid position: ({piece.posx}, {piece.posy})")
    
    # Check walls
    for wall in valid_board.walls:
        if wall.posx >= valid_board.width or wall.posy >= valid_board.height:
            print(f"Wall at invalid position: ({wall.posx}, {wall.posy})")
    
    # Check upgrade squares
    for square in valid_board.upgrade_squares:
        if square.posx >= valid_board.width or square.posy >= valid_board.height:
            print(f"Upgrade square at invalid position: ({square.posx}, {square.posy})")
    
    # Check for duplicate piece positions
    positions = [(p.posx, p.posy) for p in valid_board.pieces]
    if len(positions) != len(set(positions)):
        print("Duplicate piece positions found!")
        from collections import Counter
        duplicates = [pos for pos, count in Counter(positions).items() if count > 1]
        print(f"Duplicate positions: {duplicates}")
    
    # Invalid board (piece outside bounds)
    invalid_board = BoardState(
        width=8,
        height=8,
        pieces=[Piece(id="test", type=PieceType.PAWN, side=Side.WHITE, posx=10, posy=10)]
    )
    print(f"Invalid board validation: {invalid_board.is_valid()}")

if __name__ == "__main__":
    print("AI API Test Suite")
    print("=" * 50)
    
    test_board_validation()
    test_ai_engine()
    
    print("\n" + "=" * 50)
    print("Test completed!")
