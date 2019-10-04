from __future__ import annotations

from dlgo.goboard_slow import GameState


class Agent:
    def __init__(self):
        pass

    def select_move(self, game_state: GameState):
        raise NotImplementedError()
