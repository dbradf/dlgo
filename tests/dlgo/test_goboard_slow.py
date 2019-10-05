import pytest

from dlgo.gotypes import Point

import dlgo.goboard_slow as under_test


class TestIsOnGrid:
    @pytest.mark.parametrize("row, col", [
        (0, 2),
        (6, 2),
        (2, 0),
        (2, 6)
    ])
    def test_positions_not_on_board(self, row, col):
        board = under_test.Board(5, 5)

        assert not board.is_on_grid(Point(row, col))

    @pytest.mark.parametrize("row, col", [
        (1, 2),
        (5, 2),
        (2, 1),
        (5, 1)
    ])
    def test_position_on_board(self, row, col):
        board = under_test.Board(5, 5)

        assert board.is_on_grid(Point(row, col))
