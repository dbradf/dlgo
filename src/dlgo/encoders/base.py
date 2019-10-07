import abc
import importlib

import numpy as np

from dlgo.gotypes import Point
from dlgo.goboard import GameState


class Encoder(abc.ABC):
    @abc.abstractmethod
    def name(self) -> str:
        pass

    @abc.abstractmethod
    def encode(self, game_state: GameState) -> np.array:
        pass

    @abc.abstractmethod
    def encode_point(self, point: Point) -> int:
        pass

    @abc.abstractmethod
    def decode_point_index(self, index: int) -> Point:
        pass

    @abc.abstractmethod
    def num_points(self) -> int:
        pass

    @abc.abstractmethod
    def shape(self) -> (int, int, int):
        pass


def get_encoder_by_name(name: str, board_size) -> Encoder:
    if isinstance(board_size, int):
        board_size = (board_size, board_size)
    module = importlib.import_module(f'dlgo.encoders.{name}')
    constructor = getattr(module, 'create')
    return constructor(board_size)
