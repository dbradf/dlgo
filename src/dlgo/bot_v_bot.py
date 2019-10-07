import logging
import time

import click
import structlog

from dlgo.gotypes import Player, Point
from dlgo.goboard_fast import Move, Board, GameState
from dlgo.agent.naive import RandomBot
from dlgo.agent.monte_carlo import MCTSBot
from dlgo.scoring import compute_game_result

LOGGER = structlog.get_logger(__name__)

COLS = 'ABCDEFGHJKLMNOPQRST'
STONE_TO_CHAR = {
    None: ' . ',
    Player.black: ' x ',
    Player.white: ' o ',
}

BOTS = {
    'random': RandomBot,
    'mc': MCTSBot,
}


def print_move(player: Player, move: Move):
    if move.is_pass:
        move_str = 'passes'
    elif move.is_resign:
        move_str = 'resigns'
    else:
        move_str = f"{COLS[move.point.col - 1]}{move.point.row}"
    print(f"{player} {move_str}")


def print_board(board: Board):
    for row in range(board.num_rows, 0, -1):
        bump = " " if row <= 9 else ""
        line = []
        for col in range(1, board.num_cols + 1):
            stone = board.get(Point(row=row, col=col))
            line.append(STONE_TO_CHAR[stone])

        print(f"{bump}{row} {''.join(line)}")
    print('    ' + '  '.join(COLS[:board.num_cols]))


def config_logging(verbose):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level)
    structlog.configure(logger_factory=structlog.stdlib.LoggerFactory())


@click.command()
@click.option("-w", "--white", "bot_white", required=True)
@click.option("-b", "--black", "bot_black", required=True)
@click.option("--verbose", is_flag=True, default=False)
def main(bot_white, bot_black, verbose):
    config_logging(verbose)
    board_size = 9
    game = GameState.new_game(board_size)

    bots = {
        Player.black: BOTS[bot_black](),
        Player.white: BOTS[bot_white](),
    }

    while not game.is_over():
        time.sleep(0.3)

        print(chr(27) + "[2J")
        print_board(game.board)
        bot_move = bots[game.next_player].select_move(game)
        print_move(game.next_player, bot_move)
        game = game.apply_move(bot_move)

    print(compute_game_result(game))


if __name__ == '__main__':
    main()
