from pydantic import BaseModel, validator
from typing import List, Optional, Dict, Any
from enum import Enum

class PieceType(str, Enum):
    PAWN = "pawn"
    KNIGHT = "knight"
    BISHOP = "bishop"
    ROOK = "rook"
    QUEEN = "queen"
    KING = "king"

class Side(str, Enum):
    WHITE = "white"
    RED = "red"
    BLUE = "blue"

class Position(BaseModel):
    posx: int
    posy: int
    
    @validator('posx', 'posy')
    def validate_position(cls, v):
        if v < 0:
            raise ValueError('Position must be non-negative')
        return v

class Piece(BaseModel):
    id: str
    type: PieceType
    side: Side
    posx: int
    posy: int
    has_moved: bool = False
    
    @validator('posx', 'posy')
    def validate_position(cls, v):
        if v < 0:
            raise ValueError('Position must be non-negative')
        return v

class Wall(BaseModel):
    posx: int
    posy: int
    
    @validator('posx', 'posy')
    def validate_position(cls, v):
        if v < 0:
            raise ValueError('Position must be non-negative')
        return v

class UpgradeSquare(BaseModel):
    posx: int
    posy: int
    
    @validator('posx', 'posy')
    def validate_position(cls, v):
        if v < 0:
            raise ValueError('Position must be non-negative')
        return v

class BoardState(BaseModel):
    width: int
    height: int
    pieces: List[Piece]
    walls: List[Wall] = []
    upgrade_squares: List[UpgradeSquare] = []
    
    @validator('width', 'height')
    def validate_dimensions(cls, v):
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
    piece_id: str
    from_posx: int
    from_posy: int
    to_posx: int
    to_posy: int
    killed_piece: Optional[Dict[str, Any]] = None
    promotion_type: Optional[PieceType] = None
    
    @validator('from_posx', 'from_posy', 'to_posx', 'to_posy')
    def validate_positions(cls, v):
        if v < 0:
            raise ValueError('Position must be non-negative')
        return v

class MoveRequest(BaseModel):
    board_state: BoardState
    ai_type: str = "smart2"
    side: Side
    game_id: Optional[str] = None
    
    @validator('ai_type')
    def validate_ai_type(cls, v):
        valid_types = ["smart2", "greedy", "smart_fast", "random"]
        if v not in valid_types:
            raise ValueError(f'AI type must be one of: {valid_types}')
        return v

class MoveResponse(BaseModel):
    move: Move
    score: int
    thinking_time_ms: int
    ai_type: str
    side: Side
