import pytest


def test_ala():
    assert True


def test_ala2():
    assert False


def suma(a, b):
    return a + b


def test_ala3():
    assert suma(1, 2) == 3


@pytest.mark.parametrize('a, b, result',
                         [
                             (1, 1, 3),
                             (2, 2, 4),
                             (0, 0, 0),
                         ])
def test_suma1(a, b, result):
    assert suma(a, b) == result
