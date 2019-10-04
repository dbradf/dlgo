from __future__ import annotations

from collections import namedtuple
import enum
from typing import List


class Player(enum.Enum):
    black = 1
    white = 2

    @property
    def other(self) -> Player:
        return Player.black if self == Player.white else Player.white


class Point(namedtuple('Point', ['row', 'col'])):
    def neighbors(self) -> List[Point]:
        return [
            Point(self.row - 1, self.col),
            Point(self.row + 1, self.col),
            Point(self.row, self.col - 1),
            Point(self.row, self.col + 1),
        ]
