
import dlgo.gotypes as under_test


class TestPlayer:
    def test_white_other_returns_black(self):
        white = under_test.Player.white
        assert under_test.Player.black == white.other

    def test_black_other_returns_white(self):
        black = under_test.Player.black
        assert under_test.Player.white == black.other


class TestPoint:
    def test_neighbors_returns_list_of_points(self):
        point = under_test.Point(3, 42)

        assert 4 == len(point.neighbors())
