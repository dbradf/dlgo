from __future__ import annotations

import copy
from typing import Optional, Dict

from dlgo.gotypes import Player, Point
from dlgo import zobrist
from dlgo.scoring import compute_game_result
from dlgo.utils import MoveAge


__all__ = [
    'Board',
    'GameState',
    'Move',
]

neighbor_tables = {}
corner_tables = {}


def init_neighbor_table(dim: (int, int)):
    rows, cols = dim
    new_table = {}
    for r in range(1, rows + 1):
        for c in range(1, cols + 1):
            p = Point(row=r, col=c)
            full_neighbors = p.neighbors()
            true_neighbors = [
                n for n in full_neighbors
                if 1 <= n.row <= rows and 1 < n.col <= cols]
            new_table[p] = true_neighbors
    neighbor_tables[dim] = new_table


def init_corner_table(dim: (int, int)):
    rows, cols = dim
    new_table = {}
    for r in range(1, rows + 1):
        for c in range(1, cols + 1):
            p = Point(row=r, col=c)
            full_corners = [
                Point(row=p.row - 1, col=p.col - 1),
                Point(row=p.row - 1, col=p.col + 1),
                Point(row=p.row + 1, col=p.col - 1),
                Point(row=p.row + 1, col=p.col + 1),
            ]
            true_corner = [
                n for n in full_corners
                if 1 <= n.row <= rows and 1 <= n.col <= cols]
            new_table[p] = true_corner
    corner_tables[dim] = new_table


class IllegalMoveError(Exception):
    pass


class GoString:
    def __init__(self, color, stones, liberties):
        self.color = color
        self.stones = frozenset(stones)
        self.liberties = frozenset(liberties)

    def without_liberty(self, point):
        new_liberties = self.liberties - {point}
        return GoString(self.color, self.stones, new_liberties)

    def with_liberty(self, point: Point):
        new_liberties = self.liberties | {point}
        return GoString(self.color, self.stones, new_liberties)

    def merged_with(self, go_string: GoString) -> GoString:
        assert go_string.color == self.color
        combined_stones = self.stones | go_string.stones
        return GoString(self.color, combined_stones,
                        (self.liberties | go_string.liberties) - combined_stones)

    @property
    def num_liberties(self) -> int:
        return len(self.liberties)

    def __eq__(self, other) -> bool:
        return all([
            isinstance(other, GoString),
            self.color == other.color,
            self.stones == other.stones,
            self.liberties == other.liberties
        ])

    def __repr__(self) -> str:
        return f"GoString({self.color}, {self.stones}, {self.liberties})"

    def __deepcopy__(self, memodict={}):
        return GoString(self.color, self.stones, copy.deepcopy(self.liberties))


class Board:
    def __init__(self, num_rows: int, num_cols: int):
        self.num_rows = num_rows
        self.num_cols = num_cols
        self._grid: Dict[Point, Optional[GoString]] = {}
        self._hash = zobrist.EMPTY_BOARD

        global neighbor_tables
        dim = (num_rows, num_cols)
        if dim not in neighbor_tables:
            init_neighbor_table(dim)
        if dim not in corner_tables:
            init_corner_table(dim)

        self.neighbor_table = neighbor_tables[dim]
        self.corner_table = corner_tables[dim]
        self.move_ages = MoveAge(self)

    def neighbors(self, point: Point):
        return self.neighbor_table[point]

    def corners(self, point: Point):
        return self.corner_table[point]

    def place_stone(self, player: Player, point: Point):
        assert self.is_on_grid(point)
        if self._grid.get(point) is not None:
            print(f"Illegal play on {point}")
        assert self._grid.get(point) is None

        adjacent_same_color = []
        adjacent_opposite_color = []
        liberties = []
        self.move_ages.increment_all()
        self.move_ages.add(point)
        for neighbor in self.neighbor_table[point]:
            neighbor_string = self._grid.get(neighbor)
            if neighbor_string is None:
                liberties.append(neighbor)
            elif neighbor_string.color == player:
                if neighbor_string not in adjacent_same_color:
                    adjacent_same_color.append(neighbor_string)
            else:
                if neighbor_string not in adjacent_opposite_color:
                    adjacent_opposite_color.append(neighbor_string)

        new_string = GoString(player, [point], liberties)

        for same_color_string in adjacent_same_color:
            new_string = new_string.merged_with(same_color_string)
        for new_string_point in new_string.stones:
            self._grid[new_string_point] = new_string

        self._hash ^= zobrist.HASH_CODE[point, None]
        self._hash ^= zobrist.HASH_CODE[point, player]

        for other_color_string in adjacent_opposite_color:
            replacement = other_color_string.without_liberty(point)
            if replacement.num_liberties:
                self._replace_string(other_color_string.without_liberty(point))
            else:
                self._remove_string(other_color_string)

    def is_on_grid(self, point: Point) -> bool:
        return 1 <= point.row <= self.num_rows and 1 <= point.col <= self.num_cols

    def get(self, point: Point) -> Optional[Player]:
        string = self._grid.get(point)
        if string is None:
            return None
        return string.color

    def get_go_string(self, point: Point) -> Optional[GoString]:
        string = self._grid.get(point)
        if string is None:
            return None
        return string

    def zobrist_hash(self) -> int:
        return self._hash

    def _replace_string(self, new_string: GoString):
        for point in new_string.stones:
            self._grid[point] = new_string

    def _remove_string(self, string: GoString):
        for point in string.stones:
            self.move_ages.reset_age(point)
            for neighbor in self.neighbor_table[point]:
                neighbor_string = self._grid.get(neighbor)
                if neighbor_string is None:
                    continue
                if neighbor_string is not string:
                    self._replace_string(neighbor_string.with_liberty(point))
            self._grid[point] = None

            self._hash ^= zobrist.HASH_CODE[point, string.color]
            self._hash ^= zobrist.HASH_CODE[point, None]

    def is_self_capture(self, player: Player, point: Point) -> bool:
        friendly_strings = []
        for neighbor in self.neighbor_table[point]:
            neighbor_string = self._grid.get(neighbor)
            if neighbor_string is None:
                return False
            elif neighbor_string.color == player:
                friendly_strings.append(neighbor_string)
            else:
                if neighbor_string.num_liberties == 1:
                    return False
        if all(neighbor.num_liberties == 1 for neighbor in friendly_strings):
            return True

        return False

    def will_capture(self, player: Player, point: Point) -> bool:
        for neighbor in self.neighbor_table[point]:
            neighbor_string = self._grid.get(neighbor)
            if neighbor_string is None:
                continue
            elif neighbor_string.color == player:
                continue
            else:
                if neighbor_string.num_liberties == 1:
                    return True

        return False

    def __eq__(self, other):
        return isinstance(other, Board) and \
                self.num_rows == other.num_rows and \
                self.num_cols == other.num_cols and \
                self._hash() == other._hash()

    def __deepcopy__(self, memodict={}):
        copied = Board(self.num_rows, self.num_cols)
        copied._grid = copy.copy(self._grid)
        copied._hash = self._hash
        return copied


class Move:
    def __init__(self, point: Optional[Point] = None, is_pass: bool = False,
                 is_resign: bool = False):
        assert (point is not None) ^ is_pass ^ is_resign
        self.point = point
        self.is_play = (self.point is not None)
        self.is_pass = is_pass
        self.is_resign = is_resign

    @classmethod
    def play(cls, point) -> Move:
        return Move(point=point)

    @classmethod
    def pass_turn(cls) -> Move:
        return Move(is_pass=True)

    @classmethod
    def resign(cls) -> Move:
        return Move(is_resign=True)

    def __str__(self):
        if self.is_pass:
            return 'pass'
        if self.is_resign:
            return 'resign'
        return f"(r {self.point.row}, c {self.point.col}"

    def __hash__(self):
        return hash((
            self.is_play,
            self.is_pass,
            self.is_resign,
            self.point))

    def __eq__(self, other):
        return (
            self.is_play,
            self.is_pass,
            self.is_resign,
            self.point) == (
            other.is_play,
            other.is_pass,
            other.is_resign,
            other.point)


class GameState:
    def __init__(self, board: Board, next_player: Player, previous: Optional[GameState],
                 move: Optional[Move]):
        self.board = board
        self.next_player = next_player
        self.previous_state = previous
        if not self.previous_state:
            self.previous_states = frozenset()
        else:
            self.previous_states = frozenset(
                previous.previous_states | {(previous.next_player, previous.board.zobrist_hash())}
            )
        self.last_move = move

    def apply_move(self, move: Move) -> GameState:
        if move.is_play:
            next_board = copy.deepcopy(self.board)
            next_board.place_stone(self.next_player, move.point)
        else:
            next_board = self.board
        return GameState(next_board, self.next_player.other, self, move)

    @classmethod
    def new_game(cls, board_size) -> GameState:
        if isinstance(board_size, int):
            board_size = (board_size, board_size)
        board = Board(*board_size)
        return GameState(board, Player.black, None, None)

    def is_over(self) -> bool:
        if self.last_move is None:
            return False

        if self.last_move.is_resign:
            return True

        second_last_move = self.previous_state.last_move
        if second_last_move is None:
            return False

        return self.last_move.is_pass and second_last_move.is_pass

    def is_move_self_capture(self, player: Player, move: Move) -> bool:
        if not move.is_play:
            return False
        return self.board.is_self_capture(player, move.point)

    @property
    def situation(self) -> (Player, Board):
        return self.next_player, self.board

    def does_move_violate_ko(self, player: Player, move: Move) -> bool:
        if not move.is_play:
            return False

        if not self.board.will_capture(player, move.point):
            return False

        next_board = copy.deepcopy(self.board)
        next_board.place_stone(player, move.point)
        next_situation = (player.other, next_board.zobrist_hash())
        return next_situation in self.previous_states

    def is_valid_move(self, move: Move) -> bool:
        if self.is_over():
            return False

        if move.is_pass or move.is_resign:
            return True

        return self.board.get(move.point) is None and \
               not self.is_move_self_capture(self.next_player, move) and \
               not self.does_move_violate_ko(self.next_player, move)

    def legal_moves(self) -> [Move]:
        if self.is_over():
            return []

        moves = []
        for row in range(1, self.board.num_rows + 1):
            for col in range(1, self.board.num_cols + 1):
                move = Move.play(Point(row, col))
                if self.is_valid_move(move):
                    moves.append(move)
        # These two moves are always legal.
        moves.append(Move.pass_turn())
        moves.append(Move.resign())

        return moves

    def winner(self):
        if not self.is_over():
            return None

        if self.last_move.is_resign:
            return self.next_player
        game_result = compute_game_result(self)
        return game_result.winner

