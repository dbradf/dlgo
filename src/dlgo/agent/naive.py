import random

from structlog import get_logger

from dlgo.agent.base import Agent
from dlgo.agent.helpers import is_point_an_eye
from dlgo.goboard_slow import Move, GameState
from dlgo.gotypes import Point

LOGGER = get_logger(__name__)


class RandomBot(Agent):
    def select_move(self, game_state: GameState):
        """Choose a random valid move that preserves our own eyes."""
        LOGGER.debug("Looking for move", player=game_state.next_player)
        candidates = []
        for r in range(1, game_state.board.num_rows + 1):
            for c in range(1, game_state.board.num_cols + 1):
                candidate = Point(row=r, col=c)
                if all([
                    game_state.is_valid_move(Move.play(candidate)),
                    not is_point_an_eye(game_state.board, candidate, game_state.next_player)
                ]):
                    LOGGER.debug("adding candidate move", candidate=candidate)
                    candidates.append(candidate)

        if not candidates:
            LOGGER.debug("No move found, passing")
            return Move.pass_turn()
        move = random.choice(candidates)
        LOGGER.debug("random move", move=move)
        return Move.play(move)
