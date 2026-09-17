from typing import List, Dict, Any, Optional, Tuple
import math
from models import BoardState, Piece, Side, PieceType
from ai_base import AIBase

class AiSmart2(AIBase):
    """
    Smart AI that evaluates moves based on piece type, position, and protection.
    Ported from Ruby AiSmart2 class.
    """
    
    def __init__(self, board_state: BoardState, side: Side):
        super().__init__(board_state, side)
        self.upgrade_squares = board_state.upgrade_squares
        self.board_width = board_state.width
        self.board_height = board_state.height
        self.walls = board_state.walls
        
        # Pre-calculate distance matrix for upgrade squares
        self.distance_to_upgrade_matrix = self._calculate_distance_to_upgrade_matrix()
        
        # Piece values for evaluation
        self.piece_values = {
            'pawn': 100,
            'knight': 320,
            'bishop': 330,
            'rook': 500,
            'queen': 900,
            'king': 20000
        }
    
    def select_move(self) -> Optional[Tuple[Piece, Dict[str, Any]]]:
        """Select the best move based on comprehensive evaluation."""
        all_moves = self._assemble_possible_moves()
        if not all_moves:
            return None
        
        # Evaluate all moves by piece type
        evaluated_moves = []
        for piece, move in all_moves:
            # Base material evaluation
            base_value = self._value_for_move(piece, move)
            
            # Piece-specific evaluation
            piece_score = self._evaluate_piece_move(piece, move)
            
            # Protection evaluation (applies to all pieces)
            protection_score = self._evaluate_protection_impact(piece, move)
            
            total_score = base_value + piece_score + protection_score
            
            evaluated_moves.append((piece, move, total_score))
        
        # Sort by score (best first)
        evaluated_moves.sort(key=lambda x: x[2], reverse=True)
        
        # Select best move
        selected_move = evaluated_moves[0]
        return selected_move[0], selected_move[1]
    
    def get_move_score(self, move_result: Tuple[Piece, Dict[str, Any]]) -> int:
        """Get the score for a specific move."""
        piece, move = move_result
        base_value = self._value_for_move(piece, move)
        piece_score = self._evaluate_piece_move(piece, move)
        protection_score = self._evaluate_protection_impact(piece, move)
        return base_value + piece_score + protection_score
    
    def _evaluate_piece_move(self, piece: Piece, move: Dict[str, Any]) -> int:
        """Route to the appropriate piece-specific evaluation method."""
        if piece.type == PieceType.PAWN:
            return self._evaluate_pawn_move(piece, move)
        elif piece.type == PieceType.KNIGHT:
            return self._evaluate_knight_move(piece, move)
        elif piece.type == PieceType.BISHOP:
            return self._evaluate_bishop_move(piece, move)
        elif piece.type == PieceType.ROOK:
            return self._evaluate_rook_move(piece, move)
        elif piece.type == PieceType.QUEEN:
            return self._evaluate_queen_move(piece, move)
        elif piece.type == PieceType.KING:
            return self._evaluate_king_move(piece, move)
        else:
            return 0
    
    def _evaluate_pawn_move(self, piece: Piece, move: Dict[str, Any]) -> int:
        """Evaluate pawn moves with focus on advancement and captures."""
        score = 0
        
        # 1. CAPTURES (highest priority)
        if move.get('killed_piece'):
            captured_value = self.piece_values.get(move['killed_piece']['type'], 100)
            score += captured_value + 300  # Capture bonus + piece value
        
        # 2. UPGRADE SQUARE ADVANCEMENT (main goal)
        current_distance = self._distance_to_upgrade_square(piece.posx, piece.posy)
        new_distance = self._distance_to_upgrade_square(move['posx'], move['posy'])
        
        if new_distance == 0:
            score += 1000  # Promotion!
        elif new_distance < current_distance:
            improvement = current_distance - new_distance
            score += improvement * 150  # Strong bonus for getting closer
        elif new_distance > current_distance:
            loss = new_distance - current_distance
            score -= loss * 50  # Penalty for moving away
        
        return score
    
    def _evaluate_knight_move(self, piece: Piece, move: Dict[str, Any]) -> int:
        """Evaluate knight moves with focus on centralization and development."""
        score = 0
        
        # 1. CAPTURES
        if move.get('killed_piece'):
            captured_value = self.piece_values.get(move['killed_piece']['type'], 100)
            score += captured_value + 200
        
        # 2. CENTRALIZATION (knights are better in center)
        center_x, center_y = self.board_width // 2, self.board_height // 2
        current_center_dist = self._distance_to_center(piece.posx, piece.posy, center_x, center_y)
        new_center_dist = self._distance_to_center(move['posx'], move['posy'], center_x, center_y)
        
        if new_center_dist < current_center_dist:
            score += 30  # Bonus for moving toward center
        
        # 3. DEVELOPMENT (move from starting position)
        starting_rank = 0 if piece.side == Side.WHITE else self.board_height - 1
        if piece.posy == starting_rank:
            score += 50  # Development bonus
        
        return score
    
    def _evaluate_bishop_move(self, piece: Piece, move: Dict[str, Any]) -> int:
        """Evaluate bishop moves with focus on long diagonals and development."""
        score = 0
        
        # 1. CAPTURES
        if move.get('killed_piece'):
            captured_value = self.piece_values.get(move['killed_piece']['type'], 100)
            score += captured_value + 200
        
        # 2. LONG DIAGONALS (bishops like long diagonals)
        edge_distance = min(move['posx'], move['posy'], 
                           self.board_width - 1 - move['posx'], 
                           self.board_height - 1 - move['posy'])
        if edge_distance < 3:
            score += (5 - edge_distance) * 10
        
        # 3. DEVELOPMENT
        starting_rank = 0 if piece.side == Side.WHITE else self.board_height - 1
        if piece.posy == starting_rank:
            score += 40
        
        return score
    
    def _evaluate_rook_move(self, piece: Piece, move: Dict[str, Any]) -> int:
        """Evaluate rook moves with focus on open files/ranks and development."""
        score = 0
        
        # 1. CAPTURES
        if move.get('killed_piece'):
            captured_value = self.piece_values.get(move['killed_piece']['type'], 100)
            score += captured_value + 200
        
        # 2. OPEN FILES/RANKS (simplified: prefer edges and center lines)
        if (move['posx'] == 0 or move['posx'] == self.board_width - 1 or
            move['posy'] == 0 or move['posy'] == self.board_height - 1):
            score += 25  # Edge files/ranks
        
        # 3. DEVELOPMENT
        starting_rank = 0 if piece.side == Side.WHITE else self.board_height - 1
        if piece.posy == starting_rank and move['posy'] != starting_rank:
            score += 30
        
        return score
    
    def _evaluate_queen_move(self, piece: Piece, move: Dict[str, Any]) -> int:
        """Evaluate queen moves with focus on captures and avoiding early development."""
        score = 0
        
        # 1. CAPTURES (queens are great at capturing)
        if move.get('killed_piece'):
            captured_value = self.piece_values.get(move['killed_piece']['type'], 100)
            score += captured_value + 250
        
        # 2. AVOID EARLY DEVELOPMENT (queens shouldn't come out too early)
        starting_rank = 0 if piece.side == Side.WHITE else self.board_height - 1
        if piece.posy == starting_rank and move['posy'] != starting_rank:
            score -= 100  # Penalty for early queen development
        
        # 3. CENTRALIZATION (but not too early)
        center_x, center_y = self.board_width // 2, self.board_height // 2
        center_dist = self._distance_to_center(move['posx'], move['posy'], center_x, center_y)
        if center_dist < 3:
            score += 20  # Modest bonus for centralization
        
        return score
    
    def _evaluate_king_move(self, piece: Piece, move: Dict[str, Any]) -> int:
        """Evaluate king moves with focus on safety and staying near starting position."""
        score = 0
        
        # 1. CAPTURES (only if safe)
        if move.get('killed_piece'):
            captured_value = self.piece_values.get(move['killed_piece']['type'], 100)
            score += captured_value + 100  # More cautious than other pieces
        
        # 2. SAFETY (stay near starting position early game)
        starting_rank = 0 if piece.side == Side.WHITE else self.board_height - 1
        if piece.posy == starting_rank:
            score += 50  # Bonus for staying on back rank
        
        # 3. AVOID CENTER (kings should stay safe)
        center_x, center_y = self.board_width // 2, self.board_height // 2
        center_dist = self._distance_to_center(move['posx'], move['posy'], center_x, center_y)
        if center_dist > 3:
            score += 30  # Bonus for staying away from center
        
        return score
    
    def _evaluate_protection_impact(self, piece: Piece, move: Dict[str, Any]) -> int:
        """Evaluate how a move affects piece protection."""
        protection_score = 0
        
        # 1. PROTECTING OTHER PIECES
        friendly_pieces = [p for p in self.board_state.pieces if p.side == piece.side and p.id != piece.id]
        
        for friendly in friendly_pieces:
            friendly_value = self.piece_values.get(friendly.type, 100)
            
            # Check if this piece currently protects the friendly piece
            currently_protecting = self._piece_protects_square(piece, friendly.posx, friendly.posy)
            
            # Check if this piece will protect the friendly piece after the move
            will_protect_after_move = self._piece_protects_square_after_move(piece, move, friendly.posx, friendly.posy)
            
            # Score changes in protection
            if not currently_protecting and will_protect_after_move:
                # Started protecting a piece
                protection_bonus = self._calculate_protection_value(friendly_value)
                protection_score += protection_bonus
            elif currently_protecting and not will_protect_after_move:
                # Stopped protecting a piece
                protection_penalty = int(self._calculate_protection_value(friendly_value) * 0.7)
                protection_score -= protection_penalty
        
        # 2. BEING PROTECTED (self-protection)
        piece_value = self.piece_values.get(piece.type, 100)
        
        # Check if moving piece is currently protected
        currently_protected = self._piece_is_protected(piece)
        
        # Check if moving piece will be protected after the move
        will_be_protected = self._piece_will_be_protected_after_move(piece, move)
        
        if not currently_protected and will_be_protected:
            # Moving to a protected square
            self_protection_bonus = self._calculate_self_protection_value(piece_value)
            protection_score += self_protection_bonus
        elif currently_protected and not will_be_protected:
            # Leaving a protected square - penalty varies by piece type
            penalty_multiplier = {
                'pawn': 0.3,    # Light penalty for pawns (they need to advance)
                'queen': 0.8,   # Heavy penalty for queen (very dangerous to leave unprotected)
                'king': 0.9,    # Very heavy penalty for king
            }.get(piece.type, 0.5)  # Moderate penalty for other pieces
            
            self_protection_penalty = int(self._calculate_self_protection_value(piece_value) * penalty_multiplier)
            protection_score -= self_protection_penalty
        
        return protection_score
    
    def _calculate_protection_value(self, piece_value: int) -> int:
        """Calculate protection bonus based on piece value."""
        if piece_value >= 900:  # Queen
            return 80
        elif piece_value >= 500:  # Rook
            return 60
        elif piece_value >= 300:  # Bishop/Knight
            return 40
        elif piece_value >= 100:  # Pawn
            return 20
        else:
            return 30  # Default
    
    def _calculate_self_protection_value(self, piece_value: int) -> int:
        """Calculate self-protection bonus based on piece value."""
        if piece_value >= 900:  # Queen
            return 120  # Very important for queen to be safe
        elif piece_value >= 500:  # Rook
            return 90
        elif piece_value >= 300:  # Bishop/Knight
            return 60
        elif piece_value >= 100:  # Pawn
            return 25
        else:
            return 40  # Default
    
    def _piece_protects_square(self, piece: Piece, target_x: int, target_y: int) -> bool:
        """Check if piece can attack the target square (thus protecting it)."""
        try:
            # Get possible moves for this piece
            possible_moves = self._get_piece_possible_moves(piece)
            
            # See if any move would capture something at the target square
            return any(move['posx'] == target_x and move['posy'] == target_y 
                      for move in possible_moves)
        except:
            return False  # If we can't calculate moves, assume no protection
    
    def _piece_protects_square_after_move(self, piece: Piece, move: Dict[str, Any], 
                                         target_x: int, target_y: int) -> bool:
        """Check if piece would protect target square after making this move."""
        try:
            # Create a hypothetical piece at the new position
            moved_piece = Piece(
                id=piece.id,
                type=piece.type,
                side=piece.side,
                posx=move['posx'],
                posy=move['posy'],
                has_moved=piece.has_moved
            )
            
            # Check if it can protect from new position
            return self._piece_protects_square(moved_piece, target_x, target_y)
        except:
            return False
    
    def _piece_is_protected(self, piece: Piece) -> bool:
        """Check if any friendly piece can protect this piece's current position."""
        friendly_pieces = [p for p in self.board_state.pieces if p.side == piece.side and p.id != piece.id]
        
        return any(self._piece_protects_square(protector, piece.posx, piece.posy) 
                  for protector in friendly_pieces)
    
    def _piece_will_be_protected_after_move(self, piece: Piece, move: Dict[str, Any]) -> bool:
        """Check if any friendly piece will protect this piece's new position."""
        friendly_pieces = [p for p in self.board_state.pieces if p.side == piece.side and p.id != piece.id]
        
        return any(self._piece_protects_square(protector, move['posx'], move['posy']) 
                  for protector in friendly_pieces)
    
    def _distance_to_center(self, x: int, y: int, center_x: int, center_y: int) -> float:
        """Calculate distance to center of board."""
        return math.sqrt((x - center_x)**2 + (y - center_y)**2)
    
    def _distance_to_upgrade_square(self, posx: int, posy: int) -> float:
        """Get distance to nearest upgrade square."""
        key = (posx, posy)
        return self.distance_to_upgrade_matrix.get(key, float('inf'))
    
    def _calculate_distance_to_upgrade_matrix(self) -> Dict[Tuple[int, int], float]:
        """Calculate distance matrix from all squares to upgrade squares."""
        if not self.upgrade_squares:
            return {}
        
        matrix = {}
        
        # Initialize all squares with maximum distance
        for x in range(self.board_width):
            for y in range(self.board_height):
                matrix[(x, y)] = float('inf')
        
        # Set upgrade squares to distance 0
        for square in self.upgrade_squares:
            x, y = square.posx, square.posy
            matrix[(x, y)] = 0
        
        # Use BFS to find shortest paths from upgrade squares
        for square in self.upgrade_squares:
            start_x, start_y = square.posx, square.posy
            self._bfs_from_upgrade_square(start_x, start_y, matrix)
        
        return matrix
    
    def _bfs_from_upgrade_square(self, start_x: int, start_y: int, matrix: Dict[Tuple[int, int], float]):
        """BFS to calculate distances from an upgrade square."""
        queue = [(start_x, start_y, 0)]  # (x, y, distance)
        visited = set()
        
        while queue:
            x, y, distance = queue.pop(0)
            current_key = (x, y)
            
            if current_key in visited:
                continue
            visited.add(current_key)
            
            # Update matrix if we found a shorter path
            if distance < matrix[current_key]:
                matrix[current_key] = distance
            
            # Check all 4 cardinal directions (since pawns move in cardinal directions)
            directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            
            for dx, dy in directions:
                new_x, new_y = x + dx, y + dy
                
                # Check bounds
                if (new_x < 0 or new_x >= self.board_width or 
                    new_y < 0 or new_y >= self.board_height):
                    continue
                
                # Check if square is blocked by wall
                if any(wall.posx == new_x and wall.posy == new_y for wall in self.walls):
                    continue
                
                # Check if we haven't visited this square or found a better path
                new_key = (new_x, new_y)
                if new_key not in visited and distance + 1 < matrix[new_key]:
                    queue.append((new_x, new_y, distance + 1))
