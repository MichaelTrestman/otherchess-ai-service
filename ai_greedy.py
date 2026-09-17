from typing import List, Dict, Any, Optional, Tuple
from ai_base import AIBase

class AiGreedy(AIBase):
    """
    Greedy AI that always chooses the move with the highest material value.
    """
    
    def select_move(self) -> Optional[Tuple[Any, Dict[str, Any]]]:
        """Select the move with the highest material value."""
        all_moves = self._assemble_possible_moves()
        if not all_moves:
            return None
        
        # Evaluate moves by material value
        evaluated_moves = []
        for piece, move in all_moves:
            score = self._value_for_move(piece, move)
            evaluated_moves.append((piece, move, score))
        
        # Sort by score (highest first)
        evaluated_moves.sort(key=lambda x: x[2], reverse=True)
        
        # Select best move
        selected_move = evaluated_moves[0]
        return selected_move[0], selected_move[1]
