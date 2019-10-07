import logging

import click
import numpy as np
import structlog

from dlgo.agent.monte_carlo import MCTSBot
from dlgo.encoders.base import get_encoder_by_name
from dlgo import goboard_fast as goboard


def generate_game(board_size, rounds, max_moves, temperature):
    boards, moves = [], []

    encoder = get_encoder_by_name('oneplane', board_size)
    game = goboard.GameState.new_game(board_size)
    bot = MCTSBot(rounds, temperature)

    num_moves = 0
    while not game.is_over():
        move = bot.select_move(game)
        if move.is_play:
            boards.append(encoder.encode(game))

            move_one_hot = np.zeros(encoder.num_points())
            move_one_hot[encoder.encode_point(move.point)] = 1
            moves.append(move_one_hot)

        game = game.apply_move(move)
        num_moves += 1
        if num_moves > max_moves:
            break

    return np.array(boards), np.array(moves)


def config_logging(verbose):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level)
    structlog.configure(logger_factory=structlog.stdlib.LoggerFactory())


@click.command()
@click.option("-b", "--board-size", type=int, default=9)
@click.option("-r", "--rounds", type=int, default=1000)
@click.option("-t", "--temperature", type=float, default=0.8)
@click.option("-m", "--max-moves", type=int, default=60)
@click.option("-n", "--num-games", type=int, default=10)
@click.option("--board-out")
@click.option("--move-out")
def main(board_size, rounds, temperature, max_moves, num_games, board_out, move_out):
    config_logging(False)

    xs = []
    ys = []

    for i in range(num_games):
        print(f"Generating game {i + 1}/{num_games}...")
        x, y = generate_game(board_size, rounds, max_moves, temperature)
        xs.append(x)
        ys.append(y)

    x = np.concatenate(xs)
    y = np.concatenate(ys)

    np.save(board_out, x)
    np.save(move_out, y)
