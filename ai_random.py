from typing import Optional, Tuple, Dict, Any
import random
from ai_base import AIBase
from models import BoardState, Piece, Side

class AiRandom(AIBase):
    """
    Random AI that selects a random valid move.
    """
    
    def select_move(self) -> Optional[Tuple[Piece, Dict[str, Any]]]:
        """Select a random valid move."""
        all_moves = self._assemble_possible_moves()
        if not all_moves:
            return None
        
        return random.choice(all_moves)
