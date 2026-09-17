#!/usr/bin/env python3
"""
Simple test script for AiSmartFast agent.
Demonstrates the fast heuristic evaluation without recursion.
"""

import time
from models import BoardState, Piece, Side, PieceType
from ai_smart_fast import AiSmartFast

def create_test_board():
    """Create a simple test board with a few pieces."""
    pieces = [
        Piece(
            id="w_pawn_1",
            type=PieceType.PAWN,
            side=Side.WHITE,
            posx=3,
            posy=6,
            has_moved=False
        ),
        Piece(
            id="w_king_1",
            type=PieceType.KING,
            side=Side.WHITE,
            posx=4,
            posy=7,
            has_moved=False
        ),
        Piece(
            id="b_pawn_1",
            type=PieceType.PAWN,
            side=Side.BLACK,
            posx=3,
            posy=1,
            has_moved=False
        ),
        Piece(
            id="b_king_1",
            type=PieceType.KING,
            side=Side.BLACK,
            posx=4,
            posy=0,
            has_moved=False
        )
    ]
    
    upgrade_squares = [
        {"posx": 0, "posy": 0},
        {"posx": 7, "posy": 7}
    ]
    
    return BoardState(
        width=8,
        height=8,
        pieces=pieces,
        walls=[],
        upgrade_squares=upgrade_squares
    )

def test_ai_smart_fast():
    """Test the AiSmartFast agent."""
    print("Testing AiSmartFast Agent")
    print("=" * 40)
    
    # Create test board
    board_state = create_test_board()
    
    # Create AI instance
    ai = AiSmartFast(board_state, Side.WHITE)
    
    # Test move calculation speed
    print("Calculating move...")
    start_time = time.time()
    
    move_result = ai.select_move()
    
    end_time = time.time()
    calculation_time = (end_time - start_time) * 1000  # Convert to milliseconds
    
    print(f"Move calculation time: {calculation_time:.2f}ms")
    
    if move_result:
        piece, move = move_result
        print(f"Selected move: {piece.type.value} from ({piece.posx}, {piece.posy}) to ({move['posx']}, {move['posy']})")
        
        # Get move score
        score = ai.get_move_score(move_result)
        print(f"Move score: {score}")
        
        # Show evaluation details
        print("\nMove evaluation details:")
        print(f"- Capture: {'Yes' if move.get('killed_piece') else 'No'}")
        print(f"- Target square threatened: {(move['posx'], move['posy']) in ai.threatened_squares}")
        print(f"- Target square defended: {(move['posx'], move['posy']) in ai.defended_squares}")
        
        if piece.type == PieceType.PAWN:
            current_dist = ai._distance_to_upgrade_square(piece.posx, piece.posy)
            new_dist = ai._distance_to_upgrade_square(move['posx'], move['posy'])
            print(f"- Pawn advancement: {current_dist} -> {new_dist} (closer to upgrade)")
    else:
        print("No valid moves found")
    
    # Performance check
    if calculation_time < 100:
        print(f"\n✅ Performance target met: {calculation_time:.2f}ms < 100ms")
    else:
        print(f"\n❌ Performance target missed: {calculation_time:.2f}ms >= 100ms")

def test_threat_maps():
    """Test threat map calculation."""
    print("\nTesting Threat Maps")
    print("=" * 40)
    
    board_state = create_test_board()
    ai = AiSmartFast(board_state, Side.WHITE)
    
    print(f"Threatened squares: {len(ai.threatened_squares)}")
    print(f"Defended squares: {len(ai.defended_squares)}")
    
    # Show some threatened squares
    print("\nSample threatened squares:")
    for i, square in enumerate(list(ai.threatened_squares)[:5]):
        print(f"  {i+1}. {square}")
    
    print("\nSample defended squares:")
    for i, square in enumerate(list(ai.defended_squares)[:5]):
        print(f"  {i+1}. {square}")

if __name__ == "__main__":
    test_ai_smart_fast()
    test_threat_maps()
