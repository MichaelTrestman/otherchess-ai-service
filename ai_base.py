from typing import List, Dict, Any, Optional, Tuple
from models import BoardState, Piece, Side, PieceType

class AIBase:
    """
    Base class for all AI implementations.
    Provides common functionality for move generation and evaluation.
    Ported directly from Ruby AiBase and MovesCalculator logic.
    """
    
    def __init__(self, board_state: BoardState, side: Side):
        self.board_state = board_state
        self.side = side
        self.space_occupancy_registry = self._populate_space_occupancy_registry()
        self.piece_values = {
            'pawn': 100,
            'knight': 350,
            'bishop': 350,
            'rook': 525,
            'queen': 1000,
            'king': 20000
        }
    
    def select_move(self) -> Optional[Tuple[Piece, Dict[str, Any]]]:
        """
        Select the best move. Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement select_move")
    
    def _populate_space_occupancy_registry(self) -> Dict[int, Dict[int, Any]]:
        """Create a registry of what occupies each space on the board."""
        registry = {}
        
        # Add walls to registry
        for wall in self.board_state.walls:
            x, y = wall.posx, wall.posy
            if x not in registry:
                registry[x] = {}
            registry[x][y] = 'wall'
        
        # Add pieces to registry
        for piece in self.board_state.pieces:
            x, y = piece.posx, piece.posy
            if x not in registry:
                registry[x] = {}
            registry[x][y] = {
                'side': piece.side,
                'type': piece.type,
                'id': piece.id
            }
        
        return registry
    
    def _assemble_possible_moves(self) -> List[Tuple[Piece, Dict[str, Any]]]:
        """
        Get all possible moves for the current side.
        Uses the Ruby logic from assemble_possible_moves.
        """
        all_moves = []
        current_turn_pieces = [p for p in self.board_state.pieces if p.side == self.side]
        
        for piece in current_turn_pieces:
            piece_moves = self._calculate_moves_for_piece(piece)
            for move in piece_moves:
                all_moves.append((piece, move))
        
        return all_moves
    
    def _calculate_moves_for_piece(self, piece: Piece) -> List[Dict[str, Any]]:
        """
        Calculate moves for a specific piece using Ruby MovesCalculator logic.
        """
        if piece.side != self.side:
            return []
        
        # Route to piece-specific move calculation
        piece_type = piece.type.value if hasattr(piece.type, 'value') else piece.type
        method_name = f"_moves_for_{piece_type}"
        
        if hasattr(self, method_name):
            return getattr(self, method_name)(piece)
        else:
            return []
    
    def _moves_for_pawn(self, piece: Piece) -> List[Dict[str, Any]]:
        """Generate pawn moves using Ruby logic."""
        move_set = []
        
        # First try cardinal directions (forward moves)
        for direction in self._cardinal_directions().values():
            result = self._try_once(piece, direction)
            if result:
                move_set.append(result)
        
        # Filter to only non-kill moves
        no_kill_moves = [move for move in move_set if move.get('killed_piece') is None]
        move_set = []
        
        # Then try diagonal directions (captures)
        for direction in self._diagonal_directions().values():
            result = self._try_once(piece, direction)
            if result:
                move_set.append(result)
        
        # Filter to only kill moves
        kill_moves = [move for move in move_set if move.get('killed_piece') is not None]
        
        return no_kill_moves + kill_moves
    
    def _moves_for_bishop(self, piece: Piece) -> List[Dict[str, Any]]:
        """Generate bishop moves using Ruby logic."""
        move_set = []
        for direction in self._diagonal_directions().values():
            move_set.extend(self._try_until_hit_something(piece, direction))
        return move_set
    
    def _moves_for_king(self, piece: Piece) -> List[Dict[str, Any]]:
        """Generate king moves using Ruby logic."""
        move_set = []
        for direction in self._cardinal_directions().values():
            result = self._try_once(piece, direction)
            if result:
                move_set.append(result)
        
        for direction in self._diagonal_directions().values():
            result = self._try_once(piece, direction)
            if result:
                move_set.append(result)
        
        return move_set
    
    def _moves_for_queen(self, piece: Piece) -> List[Dict[str, Any]]:
        """Generate queen moves using Ruby logic."""
        move_set = []
        for direction in self._cardinal_directions().values():
            move_set.extend(self._try_until_hit_something(piece, direction))
        
        for direction in self._diagonal_directions().values():
            move_set.extend(self._try_until_hit_something(piece, direction))
        
        return move_set
    
    def _moves_for_rook(self, piece: Piece) -> List[Dict[str, Any]]:
        """Generate rook moves using Ruby logic."""
        move_set = []
        for direction in self._cardinal_directions().values():
            move_set.extend(self._try_until_hit_something(piece, direction))
        return move_set
    
    def _moves_for_knight(self, piece: Piece) -> List[Dict[str, Any]]:
        """Generate knight moves using Ruby logic."""
        move_set = []
        for direction in self._knight_moves().values():
            result = self._try_once(piece, direction)
            if result:
                move_set.append(result)
        return move_set
    
    def _try_once(self, piece: Piece, direction: Dict[str, int]) -> Optional[Dict[str, Any]]:
        """Try to move once in a direction. Returns move if valid, None otherwise."""
        candidate_space = {
            'posx': piece.posx + direction['x'],
            'posy': piece.posy + direction['y']
        }
        result = self._space_available(piece, candidate_space)
        if result.get('movable'):
            # Remove movable flag and return the move
            del result['movable']
            return result
        return None
    
    def _try_until_hit_something(self, piece: Piece, direction: Dict[str, int]) -> List[Dict[str, Any]]:
        """Try to move in a direction until hitting something. Returns list of valid moves."""
        moves = []
        current_pos = {'posx': piece.posx, 'posy': piece.posy}
        
        while True:
            candidate_space = {
                'posx': current_pos['posx'] + direction['x'],
                'posy': current_pos['posy'] + direction['y']
            }
            result = self._space_available(piece, candidate_space)
            
            if result.get('movable'):
                # Remove movable flag and add to moves
                del result['movable']
                moves.append(result)
                
                # Stop if we captured a piece
                if result.get('killed_piece'):
                    break
                
                # Update current position for next iteration
                current_pos = candidate_space
            else:
                # Can't move here, stop
                break
        
        return moves
    
    def _space_available(self, piece: Piece, candidate_space: Dict[str, int]) -> Dict[str, Any]:
        """Check if a space is available for movement. Based on Ruby space_available logic."""
        if self._space_is_off_board(candidate_space):
            return {'movable': False, 'killed_piece': None}
        
        x, y = candidate_space['posx'], candidate_space['posy']
        
        # Check if space is empty
        if x not in self.space_occupancy_registry:
            return {
                'movable': True,
                'killed_piece': None,
                'posx': x,
                'posy': y
            }
        
        if y not in self.space_occupancy_registry[x]:
            return {
                'movable': True,
                'killed_piece': None,
                'posx': x,
                'posy': y
            }
        
        occupant = self.space_occupancy_registry[x][y]
        
        if occupant == 'wall':
            return {'movable': False, 'killed_piece': None}
        
        # If occupied by friendly piece
        if isinstance(occupant, dict) and occupant.get('side') == piece.side:
            return {'movable': False, 'killed_piece': None}
        
        # If occupied by enemy piece
        if isinstance(occupant, dict):
            return {
                'movable': True,
                'posx': x,
                'posy': y,
                'killed_piece': {
                    'id': occupant.get('id'),
                    'type': occupant.get('type'),
                    'side': occupant.get('side')
                }
            }
        
        # Default case (shouldn't happen)
        return {'movable': False, 'killed_piece': None}
    
    def _space_is_off_board(self, candidate_space: Dict[str, int]) -> bool:
        """Check if a space is off the board."""
        x, y = candidate_space['posx'], candidate_space['posy']
        return (x < 0 or y < 0 or 
                x >= self.board_state.width or 
                y >= self.board_state.height)
    
    def _cardinal_directions(self) -> Dict[str, Dict[str, int]]:
        """Cardinal directions from Ruby MovesCalculator."""
        return {
            'north': {'x': 0, 'y': -1},
            'south': {'x': 0, 'y': 1},
            'east': {'x': 1, 'y': 0},
            'west': {'x': -1, 'y': 0}
        }
    
    def _diagonal_directions(self) -> Dict[str, Dict[str, int]]:
        """Diagonal directions from Ruby MovesCalculator."""
        return {
            'north_east': {'x': 1, 'y': -1},
            'south_east': {'x': 1, 'y': 1},
            'north_west': {'x': -1, 'y': -1},
            'south_west': {'x': -1, 'y': 1}
        }
    
    def _knight_moves(self) -> Dict[str, Dict[str, int]]:
        """Knight moves from Ruby MovesCalculator."""
        return {
            'north_north_east': {'x': 1, 'y': -2},
            'north_north_west': {'x': -1, 'y': -2},
            'south_south_east': {'x': 1, 'y': 2},
            'south_south_west': {'x': -1, 'y': 2},
            'east_east_north': {'x': 2, 'y': -1},
            'east_east_south': {'x': 2, 'y': 1},
            'west_west_north': {'x': -2, 'y': -1},
            'west_west_south': {'x': -2, 'y': 1}
        }
    
    def _get_piece_possible_moves(self, piece: Piece) -> List[Dict[str, Any]]:
        """
        Legacy method for compatibility. Use _calculate_moves_for_piece instead.
        """
        return self._calculate_moves_for_piece(piece)
    
    def _value_for_move(self, piece: Piece, move: Dict[str, Any]) -> int:
        """Calculate base material value for a move."""
        score = 0
        
        # Capture value
        if move.get('killed_piece'):
            killed_type = move['killed_piece']['type']
            # Handle both string and enum types
            if hasattr(killed_type, 'value'):
                killed_type = killed_type.value
            score += self.piece_values.get(killed_type, 100)
        
        # Piece development bonus (small)
        piece_type = piece.type.value if hasattr(piece.type, 'value') else piece.type
        if piece_type in ['knight', 'bishop', 'rook']:
            starting_rank = 0 if piece.side == Side.WHITE else self.board_state.height - 1
            if piece.posy == starting_rank and move['posy'] != starting_rank:
                score += 10
        
        return score
