from typing import Dict, List, Optional, Tuple, Any
import logging
from models import BoardState, Piece, Move, Side, PieceType
from ai_smart2 import AiSmart2
from ai_greedy import AiGreedy
from ai_smart_fast import AiSmartFast
from ai_random import AiRandom
from ai_minimax import AiMinimax

logger = logging.getLogger(__name__)

class AIEngine:
    """
    Main AI engine that manages different AI types and calculates moves.
    """
    
    def __init__(self):
        self.ai_types = {
            "smart2": AiSmart2,
            "greedy": AiGreedy,
            "smart_fast": AiSmartFast,
            "random": AiRandom,
            "minimax": AiMinimax
        }
        logger.info("AI Engine initialized with AI types: %s", list(self.ai_types.keys()))
    
    def get_available_ai_types(self) -> List[str]:
        """Get list of available AI types."""
        return list(self.ai_types.keys())
    
    def calculate_move(self, board_state: BoardState, ai_type: str, side: Side) -> Optional[Dict[str, Any]]:
        """
        Calculate the best move for the given board state and AI type.
        
        Args:
            board_state: Current board state
            ai_type: Type of AI to use
            side: Side to play for
            
        Returns:
            Dictionary with 'move' and 'score' keys, or None if calculation fails
        """
        try:
            if ai_type not in self.ai_types:
                logger.error(f"Unknown AI type: {ai_type}")
                return None
            
            # Get AI class
            ai_class = self.ai_types[ai_type]
            
            # Create AI instance
            ai = ai_class(board_state, side)
            
            # Calculate move
            move_result = ai.select_move()
            
            if not move_result:
                logger.warning(f"AI {ai_type} failed to find a move")
                return None
            
            piece, move = move_result
            
            # Convert to Move model
            move_model = Move(
                piece_id=piece.id,
                from_posx=piece.posx,
                from_posy=piece.posy,
                to_posx=move["posx"],
                to_posy=move["posy"],
                killed_piece=move.get("killed_piece"),
                promotion_type=move.get("promotion_type")
            )
            
            # Get score (AI-specific scoring)
            score = ai.get_move_score(move_result) if hasattr(ai, 'get_move_score') else 0
            
            return {
                "move": move_model,
                "score": score
            }
            
        except Exception as e:
            logger.error(f"Error calculating move with AI {ai_type}: {str(e)}")
            return None
    
    def validate_move(self, board_state: BoardState, move: Move) -> bool:
        """
        Validate if a move is legal for the given board state.
        Delegates to the move generator for a single source of truth.
        """
        try:
            # Check if piece exists
            piece = board_state.get_piece_at(move.from_posx, move.from_posy)
            if not piece or piece.id != move.piece_id:
                return False
            
            # Check if destination is within bounds
            if (move.to_posx < 0 or move.to_posx >= board_state.width or
                move.to_posy < 0 or move.to_posy >= board_state.height):
                return False
            
            # Check if destination is occupied by friendly piece
            dest_piece = board_state.get_piece_at(move.to_posx, move.to_posy)
            if dest_piece and dest_piece.side == piece.side:
                return False
            
            # Delegate to the move generator for the single source of truth
            from ai_base import AIBase
            ai = AIBase(board_state, piece.side)
            generated_moves = ai._calculate_moves_for_piece(piece)
            
            for gen_move in generated_moves:
                if (gen_move['posx'] == move.to_posx and gen_move['posy'] == move.to_posy):
                    # Match destination; also verify killed_piece matches board reality
                    if move.killed_piece:
                        if not gen_move.get('killed_piece'):
                            return False
                        if gen_move['killed_piece']['id'] != move.killed_piece['id']:
                            return False
                    else:
                        if gen_move.get('killed_piece'):
                            return False
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error validating move: {str(e)}")
            return False
