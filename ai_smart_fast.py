from typing import List, Dict, Any, Optional, Tuple, Set
from ai_base import AIBase
from models import BoardState, Piece, Side, PieceType

class AiSmartFast(AIBase):
    """
    Fast AI agent that combines pathfinding intelligence with heuristic evaluation.
    Designed for speed over depth - no recursive lookahead, but smart positional play.
    
    Key features:
    - Threat map calculation for safety evaluation
    - Capture prioritization
    - Pawn advancement toward upgrade squares
    - Piece development bonuses
    - Safety-conscious positioning
    """
    
    def __init__(self, board_state: BoardState, side: Side):
        super().__init__(board_state, side)
        
        # Pre-calculate static data
        self.upgrade_squares = board_state.upgrade_squares
        self.board_width = board_state.width
        self.board_height = board_state.height
        self.board_center = (self.board_width // 2, self.board_height // 2)
        
        # Cache for expensive calculations
        self.threat_maps_cache = {}
        self.distance_cache = {}
        
        # Calculate threat maps once
        self.threatened_squares, self.defended_squares = self._calculate_threat_maps()
    
    def select_move(self) -> Optional[Tuple[Piece, Dict[str, Any]]]:
        """Select the best move using fast heuristic evaluation."""
        all_moves = self._assemble_possible_moves()
        if not all_moves:
            return None
        
        # Limit evaluation scope for performance (only top 10 moves)
        top_moves = all_moves[:10]
        
        evaluated_moves = []
        for piece, move in top_moves:
            score = self._evaluate_move_fast(piece, move)
            evaluated_moves.append((piece, move, score))
        
        # Sort by score (best first)
        evaluated_moves.sort(key=lambda x: x[2], reverse=True)
        
        # Return best move
        selected_move = evaluated_moves[0]
        return selected_move[0], selected_move[1]
    
    def _calculate_threat_maps(self) -> Tuple[Set[Tuple[int, int]], Set[Tuple[int, int]]]:
        """Calculate which squares are threatened by opponent and defended by friendly pieces."""
        threatened_squares = set()
        defended_squares = set()
        
        # Get opponent and friendly pieces
        opponent_pieces = [p for p in self.board_state.pieces if p.side != self.side]
        friendly_pieces = [p for p in self.board_state.pieces if p.side == self.side]
        
        # Calculate squares threatened by opponent
        for piece in opponent_pieces:
            piece_moves = self._calculate_moves_for_piece(piece)
            for move in piece_moves:
                threatened_squares.add((move['posx'], move['posy']))
        
        # Calculate squares defended by friendly pieces
        for piece in friendly_pieces:
            piece_moves = self._calculate_moves_for_piece(piece)
            for move in piece_moves:
                defended_squares.add((move['posx'], move['posy']))
        
        return threatened_squares, defended_squares
    
    def _evaluate_move_fast(self, piece: Piece, move: Dict[str, Any]) -> int:
        """Fast move evaluation using heuristics without recursion."""
        score = 0
        
        # 1. Capture Value (highest priority)
        if move.get('killed_piece'):
            killed_type = move['killed_piece']['type']
            if hasattr(killed_type, 'value'):
                killed_type = killed_type.value
            score += self.piece_values.get(killed_type, 100) + 200
        
        # 2. Safety Score
        target_square = (move['posx'], move['posy'])
        if target_square in self.threatened_squares:
            # Heavy penalty for moving into threat
            piece_type = piece.type.value if hasattr(piece.type, 'value') else piece.type
            score -= int(self.piece_values.get(piece_type, 100) * 0.5)
        elif target_square in self.defended_squares:
            # Bonus for moving to protected square
            score += 100
        
        # 3. Positional Bonuses (piece-specific)
        score += self._positional_bonus(piece, move)
        
        return score
    
    def _positional_bonus(self, piece: Piece, move: Dict[str, Any]) -> int:
        """Calculate piece-specific positional bonuses."""
        piece_type = piece.type.value if hasattr(piece.type, 'value') else piece.type
        
        if piece_type == 'pawn':
            return self._pawn_positional_bonus(piece, move)
        elif piece_type in ['knight', 'bishop']:
            return self._minor_piece_positional_bonus(piece, move)
        elif piece_type == 'rook':
            return self._rook_positional_bonus(piece, move)
        elif piece_type == 'queen':
            return self._queen_positional_bonus(piece, move)
        elif piece_type == 'king':
            return self._king_positional_bonus(piece, move)
        else:
            return 0
    
    def _pawn_positional_bonus(self, piece: Piece, move: Dict[str, Any]) -> int:
        """Pawn-specific positional evaluation."""
        score = 0
        
        # Distance to upgrade square (main goal)
        current_dist = self._distance_to_upgrade_square(piece.posx, piece.posy)
        new_dist = self._distance_to_upgrade_square(move['posx'], move['posy'])
        
        if new_dist == 0:
            score += 1000  # Promotion!
        elif new_dist < current_dist:
            improvement = current_dist - new_dist
            score += improvement * 150  # Strong advancement bonus
        elif new_dist > current_dist and not move.get('killed_piece'):
            score -= 200  # Penalty for moving backward (unless capturing)
        
        return score
    
    def _minor_piece_positional_bonus(self, piece: Piece, move: Dict[str, Any]) -> int:
        """Knight and Bishop positional evaluation."""
        score = 0
        
        # Center control bonus
        center_distance = self._distance_to_center(move['posx'], move['posy'])
        score += (5 - center_distance) * 20
        
        # Development bonus
        starting_rank = 0 if piece.side == Side.WHITE else self.board_height - 1
        if piece.posy == starting_rank:
            score += 50
        
        return score
    
    def _rook_positional_bonus(self, piece: Piece, move: Dict[str, Any]) -> int:
        """Rook positional evaluation."""
        score = 0
        
        # File/rank control (prefer edges and center lines)
        if (move['posx'] == 0 or move['posx'] == self.board_width - 1 or
            move['posy'] == 0 or move['posy'] == self.board_height - 1):
            score += 25
        
        # Development bonus
        starting_rank = 0 if piece.side == Side.WHITE else self.board_height - 1
        if piece.posy == starting_rank and move['posy'] != starting_rank:
            score += 30
        
        return score
    
    def _queen_positional_bonus(self, piece: Piece, move: Dict[str, Any]) -> int:
        """Queen positional evaluation."""
        score = 0
        
        # Avoid early development
        starting_rank = 0 if piece.side == Side.WHITE else self.board_height - 1
        if piece.posy == starting_rank and move['posy'] != starting_rank:
            score -= 150  # Heavy penalty for early queen development
        
        # Modest centralization bonus
        center_distance = self._distance_to_center(move['posx'], move['posy'])
        if center_distance < 3:
            score += 20
        
        return score
    
    def _king_positional_bonus(self, piece: Piece, move: Dict[str, Any]) -> int:
        """King positional evaluation."""
        score = 0
        
        # Safety first - stay on back rank
        starting_rank = 0 if piece.side == Side.WHITE else self.board_height - 1
        if piece.posy == starting_rank:
            score += 100
        
        # Avoid center
        center_distance = self._distance_to_center(move['posx'], move['posy'])
        if center_distance > 3:
            score += 30
        
        return score
    
    def _distance_to_upgrade_square(self, posx: int, posy: int) -> int:
        """Calculate Manhattan distance to nearest upgrade square."""
        if not self.upgrade_squares:
            return 0
        
        min_distance = float('inf')
        for square in self.upgrade_squares:
            sqx = square.posx if hasattr(square, 'posx') else square['posx']
            sqy = square.posy if hasattr(square, 'posy') else square['posy']
            distance = abs(posx - sqx) + abs(posy - sqy)
            min_distance = min(min_distance, distance)
        
        return min_distance if min_distance != float('inf') else 0
    
    def _distance_to_center(self, posx: int, posy: int) -> int:
        """Calculate Manhattan distance to board center."""
        center_x, center_y = self.board_center
        return abs(posx - center_x) + abs(posy - center_y)
    
    def get_move_score(self, move_result: Tuple[Piece, Dict[str, Any]]) -> int:
        """Get the score for a specific move."""
        piece, move = move_result
        return self._evaluate_move_fast(piece, move)
