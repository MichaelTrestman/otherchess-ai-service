"""Pydantic models describing the game board, pieces, moves, and API payloads."""
from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
from enum import Enum

class PieceType(str, Enum):
    """Types of pieces that can occupy the board.

    Standard chess piece kinds, used both for the initial setup and for
    promotion choices.
    """
    PAWN = "pawn"
    KNIGHT = "knight"
    BISHOP = "bishop"
    ROOK = "rook"
    QUEEN = "queen"
    KING = "king"

class Side(str, Enum):
    """Player sides that can participate in a game.

    Each piece belongs to exactly one side, and every move request must
    specify which side the AI is playing.
    """
    WHITE = "white"
    RED = "red"
    BLUE = "blue"

class Position(BaseModel):
    """A coordinate on the board.

    Positions are integer ``(posx, posy)`` pairs; both values must be
    non-negative.
    """
    posx: int
    posy: int
    
    @validator('posx', 'posy')
    def validate_position(cls, v):
        """Ensure the coordinate values are non-negative.

        Raises:
            ValueError: If either coordinate is negative.
        """
        if v < 0:
            raise ValueError('Position must be non-negative')
        return v

class Piece(BaseModel):
    """A game piece with its type, owning side, and board position.

    ``has_moved`` tracks whether the piece has left its starting square,
    which AI implementations may use for special-move logic.
    """
    id: str
    type: PieceType
    side: Side
    posx: int
    posy: int
    has_moved: bool = False
    
    @validator('posx', 'posy')
    def validate_position(cls, v):
        """Ensure the piece coordinates are non-negative.

        Raises:
            ValueError: If either coordinate is negative.
        """
        if v < 0:
            raise ValueError('Position must be non-negative')
        return v

class Wall(BaseModel):
    """A wall segment placed on a board square.

    Walls are impassable markers identified only by their coordinates.
    """
    posx: int
    posy: int
    
    @validator('posx', 'posy')
    def validate_position(cls, v):
        """Ensure the wall coordinates are non-negative.

        Raises:
            ValueError: If either coordinate is negative.
        """
        if v < 0:
            raise ValueError('Position must be non-negative')
        return v

class UpgradeSquare(BaseModel):
    """A special square where pieces can be upgraded.

    When a piece ends its move on an upgrade square, game rules may
    allow it to be promoted to a stronger piece type.
    """
    posx: int
    posy: int
    
    @validator('posx', 'posy')
    def validate_position(cls, v):
        """Ensure the square coordinates are non-negative.

        Raises:
            ValueError: If either coordinate is negative.
        """
        if v < 0:
            raise ValueError('Position must be non-negative')
        return v

class BoardState(BaseModel):
    """The full state of the board, including pieces, walls, and upgrade squares.

    ``width`` and ``height`` must be positive; pieces, walls, and upgrade
    squares are stored as lists of their respective models. Helper
    methods provide validation and square-lookup utilities.
    """
    width: int
    height: int
    pieces: List[Piece]
    walls: List[Wall] = []
    upgrade_squares: List[UpgradeSquare] = []
    
    @validator('width', 'height')
    def validate_dimensions(cls, v):
        """Ensure the board dimensions are positive.

        Raises:
            ValueError: If a dimension is zero or negative.
        """
        if v <= 0:
            raise ValueError('Board dimensions must be positive')
        return v
    
    def is_valid(self) -> bool:
        """Validate the board state"""
        try:
            # Check that all pieces are within board bounds
            for piece in self.pieces:
                if piece.posx >= self.width or piece.posy >= self.height:
                    return False
            
            # Check that walls are within board bounds
            for wall in self.walls:
                if wall.posx >= self.width or wall.posy >= self.height:
                    return False
            
            # Check that upgrade squares are within board bounds
            for square in self.upgrade_squares:
                if square.posx >= self.width or square.posy >= self.height:
                    return False
            
            # Check for duplicate piece positions
            positions = [(p.posx, p.posy) for p in self.pieces]
            if len(positions) != len(set(positions)):
                return False
            
            return True
        except Exception:
            return False
    
    def get_piece_at(self, x: int, y: int) -> Optional[Piece]:
        """Get piece at specific position"""
        for piece in self.pieces:
            if piece.posx == x and piece.posy == y:
                return piece
        return None
    
    def is_square_occupied(self, x: int, y: int) -> bool:
        """Check if a square is occupied by a piece or wall"""
        # Check pieces
        if self.get_piece_at(x, y):
            return True
        
        # Check walls
        for wall in self.walls:
            if wall.posx == x and wall.posy == y:
                return True
        
        return False

class Move(BaseModel):
    """A move of a piece from one square to another.

    ``killed_piece`` describes the removed opponent piece (if any) and
    ``promotion_type`` selects the new piece type when the move promotes
    a piece. All coordinates must be non-negative.
    """
    piece_id: str
    from_posx: int
    from_posy: int
    to_posx: int
    to_posy: int
    killed_piece: Optional[Dict[str, Any]] = None
    promotion_type: Optional[PieceType] = None
    
    @validator('from_posx', 'from_posy', 'to_posx', 'to_posy')
    def validate_positions(cls, v):
        """Ensure the move coordinates are non-negative.

        Raises:
            ValueError: If any coordinate is negative.
        """
        if v < 0:
            raise ValueError('Position must be non-negative')
        return v

class MoveRequest(BaseModel):
    """A request for the AI to compute a move for the given board state.

    ``ai_type`` selects the AI implementation (default ``"smart2"``) and
    ``side`` indicates which side the AI is playing. ``game_id`` is an
    optional correlation identifier.
    """
    board_state: BoardState
    ai_type: str = "smart2"
    side: Side
    game_id: Optional[str] = None
    
    @validator('ai_type')
    def validate_ai_type(cls, v):
        """Ensure the AI type refers to an available AI implementation.

        The set of valid types is looked up from the AI engine registry.

        Raises:
            ValueError: If the requested AI type is not available.
        """
        from ai_engine import AIEngine
        engine = AIEngine()
        valid_types = engine.get_available_ai_types()
        if v not in valid_types:
            raise ValueError(f'AI type must be one of: {valid_types}')
        return v

class MoveResponse(BaseModel):
    """The AI's chosen move along with score, timing, and side metadata.

    Returned by the service after the AI has selected a move for the
    supplied board state.
    """
    move: Move
    score: int
    thinking_time_ms: int
    ai_type: str
    side: Side
