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
        Filters out moves that leave the king capturable.
        """
        all_moves = []
        current_turn_pieces = [p for p in self.board_state.pieces if p.side == self.side]
        
        for piece in current_turn_pieces:
            piece_moves = self._calculate_moves_for_piece(piece)
            for move in piece_moves:
                all_moves.append((piece, move))
        
        # Filter out moves that leave the king capturable (king safety)
        safe_moves = []
        for piece, move in all_moves:
            if self._is_move_safe_for_king(piece, move):
                safe_moves.append((piece, move))
        
        return safe_moves
    
    def _is_move_safe_for_king(self, piece: Piece, move: Dict[str, Any]) -> bool:
        """Check if a move does not leave the king capturable by opponents."""
        # Find the king
        king = None
        for p in self.board_state.pieces:
            if p.side == self.side and p.type == PieceType.KING:
                king = p
                break
        
        # If no king, all moves are safe (king can be captured, side is out)
        if not king:
            return True
        
        # Simulate the move to get the board state after the move
        sim_state = self._simulate_move(piece, move)
        
        # Determine king position after the move
        king_posx = king.posx
        king_posy = king.posy
        if piece.id == king.id:
            # King is moving - find it in simulated state
            for p in sim_state.pieces:
                if p.id == king.id:
                    king_posx = p.posx
                    king_posy = p.posy
                    break
        
        # Check if any opponent piece can capture the king in the simulated state
        for opponent in sim_state.pieces:
            if opponent.side == self.side:
                continue
            
            # Check if opponent can move to king position on simulated board
            if self._can_piece_reach_on_board(opponent, king_posx, king_posy, sim_state):
                return False
        
        return True
    
    def _can_piece_reach_on_board(self, piece: Piece, target_x: int, target_y: int, board: BoardState) -> bool:
        """Check if a piece can move to a specific square in one move on a given board state."""
        piece_type = piece.type.value if hasattr(piece.type, 'value') else piece.type
        
        dx = target_x - piece.posx
        dy = target_y - piece.posy
        adx = abs(dx)
        ady = abs(dy)
        
        if piece_type == 'pawn':
            # Pawn captures diagonally one square
            if adx == 1 and ady == 1:
                # Check if target has an enemy piece
                target_piece = board.get_piece_at(target_x, target_y)
                return target_piece is not None and target_piece.side != piece.side
            return False
        
        elif piece_type == 'knight':
            if (adx == 2 and ady == 1) or (adx == 1 and ady == 2):
                # Cannot land on wall or friendly piece
                target_piece = board.get_piece_at(target_x, target_y)
                if target_piece and target_piece.side == piece.side:
                    return False
                for w in board.walls:
                    if w.posx == target_x and w.posy == target_y:
                        return False
                return True
            return False
        
        elif piece_type == 'king':
            if adx <= 1 and ady <= 1:
                target_piece = board.get_piece_at(target_x, target_y)
                if target_piece and target_piece.side == piece.side:
                    return False
                for w in board.walls:
                    if w.posx == target_x and w.posy == target_y:
                        return False
                return True
            return False
        
        elif piece_type == 'bishop':
            if adx != ady:
                return False
            return self._is_path_clear_on_board(piece.posx, piece.posy, target_x, target_y, board)
        
        elif piece_type == 'rook':
            if adx != 0 and ady != 0:
                return False
            return self._is_path_clear_on_board(piece.posx, piece.posy, target_x, target_y, board)
        
        elif piece_type == 'queen':
            if adx != 0 and ady != 0 and adx != ady:
                return False
            return self._is_path_clear_on_board(piece.posx, piece.posy, target_x, target_y, board)
        
        return False
    
    def _is_path_clear_on_board(self, from_x: int, from_y: int, to_x: int, to_y: int, board: BoardState) -> bool:
        """Check if path between two points is clear on a given board state.
        Only intermediate squares must be empty; destination is checked separately by caller."""
        step_x = 1 if to_x > from_x else -1 if to_x < from_x else 0
        step_y = 1 if to_y > from_y else -1 if to_y < from_y else 0
        
        x, y = from_x + step_x, from_y + step_y
        while x != to_x or y != to_y:
            if board.is_square_occupied(x, y):
                return False
            x += step_x
            y += step_y
        
        # Destination must not be a wall
        for w in board.walls:
            if w.posx == to_x and w.posy == to_y:
                return False
        
        return True
    
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
        """Generate pawn moves for the variant rules.
        
        Pawns have no direction:
        - Step: one square in any cardinal direction onto empty square (non-capturing)
        - Capture: one square in any diagonal direction onto enemy piece
        - First move: two squares in one cardinal direction if both squares empty
        - Promotion: pawn becomes queen when ending on upgrade square
        """
        move_set = []
        
        # Cardinal directions (step moves, non-capturing)
        for direction in self._cardinal_directions().values():
            result = self._try_once(piece, direction)
            if result and result.get('killed_piece') is None:
                move_set.append(self._add_promotion(piece, result))
        
        # Two-square first move in cardinal directions
        if not piece.has_moved:
            for direction in self._cardinal_directions().values():
                result = self._try_pawn_double_step(piece, direction)
                if result:
                    move_set.append(self._add_promotion(piece, result))
        
        # Diagonal directions (captures only)
        for direction in self._diagonal_directions().values():
            result = self._try_once(piece, direction)
            if result and result.get('killed_piece') is not None:
                move_set.append(self._add_promotion(piece, result))
        
        return move_set
    
    def _try_pawn_double_step(self, piece: Piece, direction: Dict[str, int]) -> Optional[Dict[str, Any]]:
        """Try a two-square pawn move. Both squares must be empty."""
        # First square
        mid_space = {
            'posx': piece.posx + direction['x'],
            'posy': piece.posy + direction['y']
        }
        mid_result = self._space_available(piece, mid_space)
        if not mid_result.get('movable') or mid_result.get('killed_piece'):
            return None
        
        # Second square
        end_space = {
            'posx': piece.posx + 2 * direction['x'],
            'posy': piece.posy + 2 * direction['y']
        }
        end_result = self._space_available(piece, end_space)
        if not end_result.get('movable') or end_result.get('killed_piece'):
            return None
        
        # Remove movable flag
        del end_result['movable']
        return end_result
    
    def _add_promotion(self, piece: Piece, move: Dict[str, Any]) -> Dict[str, Any]:
        """Add promotion_type if move ends on upgrade square."""
        for sq in self.board_state.upgrade_squares:
            if sq.posx == move['posx'] and sq.posy == move['posy']:
                move['promotion_type'] = PieceType.QUEEN
                break
        return move
    
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
    
    def _simulate_move(self, piece: Piece, move: Dict[str, Any]) -> BoardState:
        """Create a new board state after applying a move."""
        from copy import deepcopy
        new_state = deepcopy(self.board_state)
        
        # Find and move the piece
        for p in new_state.pieces:
            if p.id == piece.id:
                p.posx = move['posx']
                p.posy = move['posy']
                p.has_moved = True
                break
        
        # Remove killed piece
        if move.get('killed_piece'):
            killed_id = move['killed_piece']['id']
            new_state.pieces = [p for p in new_state.pieces if p.id != killed_id]
        
        # Handle promotion
        if move.get('promotion_type'):
            for p in new_state.pieces:
                if p.id == piece.id:
                    p.type = move['promotion_type']
                    break
        
        return new_state
    
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
