from typing import Dict, List, Optional, Tuple, Any
import logging
from models import BoardState, Piece, Move, Side, PieceType
from ai_smart2 import AiSmart2
from ai_greedy import AiGreedy
from ai_smart_fast import AiSmartFast
from ai_random import AiRandom

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
            "random": AiRandom
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
        This is a basic validation - more complex chess rules would need to be implemented.
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
            
            # Basic piece movement validation (simplified)
            if not self._is_valid_piece_move(piece, move, board_state):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating move: {str(e)}")
            return False
    
    def _is_valid_piece_move(self, piece: Piece, move: Move, board_state: BoardState) -> bool:
        """Validate piece movement according to variant rules."""
        dx = abs(move.to_posx - move.from_posx)
        dy = abs(move.to_posy - move.from_posy)
        
        if piece.type == PieceType.PAWN:
            # Variant pawn rules: no direction, cardinal step or diagonal capture
            # Two-square first move in cardinal direction
            if dx == 0 and dy == 2 and not piece.has_moved:
                # Must be cardinal direction and path clear
                mid_y = (move.from_posy + move.to_posy) // 2
                mid_x = move.from_posx
                if board_state.is_square_occupied(mid_x, mid_y):
                    return False
                if move.killed_piece:
                    return False
                return True
            elif dx == 2 and dy == 0 and not piece.has_moved:
                mid_x = (move.from_posx + move.to_posx) // 2
                mid_y = move.from_posy
                if board_state.is_square_occupied(mid_x, mid_y):
                    return False
                if move.killed_piece:
                    return False
                return True
            elif dx == 1 and dy == 0:
                # Cardinal step - must not capture
                return not move.killed_piece
            elif dx == 0 and dy == 1:
                # Cardinal step - must not capture
                return not move.killed_piece
            elif dx == 1 and dy == 1:
                # Diagonal - must capture
                return bool(move.killed_piece)
            else:
                return False
        
        elif piece.type == PieceType.KNIGHT:
            # Knights move in L-shape
            return (dx == 2 and dy == 1) or (dx == 1 and dy == 2)
        
        elif piece.type == PieceType.BISHOP:
            # Bishops move diagonally
            if dx != dy:
                return False
            # Check if path is blocked
            return not self._is_path_blocked(move.from_posx, move.from_posy, 
                                           move.to_posx, move.to_posy, board_state)
        
        elif piece.type == PieceType.ROOK:
            # Rooks move horizontally or vertically
            if dx != 0 and dy != 0:
                return False
            # Check if path is blocked
            return not self._is_path_blocked(move.from_posx, move.from_posy, 
                                           move.to_posx, move.to_posy, board_state)
        
        elif piece.type == PieceType.QUEEN:
            # Queens move like rooks or bishops
            if dx != 0 and dy != 0 and dx != dy:
                return False
            # Check if path is blocked
            return not self._is_path_blocked(move.from_posx, move.from_posy, 
                                           move.to_posx, move.to_posy, board_state)
        
        elif piece.type == PieceType.KING:
            # Kings move one square in any direction
            return dx <= 1 and dy <= 1
        
        return True
    
    def _is_path_blocked(self, from_x: int, from_y: int, to_x: int, to_y: int, 
                         board_state: BoardState) -> bool:
        """Check if path between two points is blocked."""
        dx = 1 if to_x > from_x else -1 if to_x < from_x else 0
        dy = 1 if to_y > from_y else -1 if to_y < from_y else 0
        
        x, y = from_x + dx, from_y + dy
        while x != to_x or y != to_y:
            if board_state.is_square_occupied(x, y):
                return True
            x += dx
            y += dy
        
        return False
