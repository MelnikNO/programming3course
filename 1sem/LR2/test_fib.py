import pytest
from main import my_genn, EvenNumbersIterator


def test_fib_1():
    gen = my_genn()
    assert gen.send(3) == [0, 1, 1], "Тривиальный случай n = 3, список [0, 1, 1]"


def test_fib_2():
    gen = my_genn()
    assert gen.send(5) == [0, 1, 1, 2, 3], "Пять первых членов ряда"


def test_fib_negative():
    """Крайний случай: отрицательное n"""
    gen = my_genn()
    assert gen.send(-5) == []


def test_fibonacci_lst_all_fib():
    """Список только с числами Фибоначчи"""
    test_list = [0, 1, 1, 2, 3, 5, 8, 13]
    result = list(EvenNumbersIterator(test_list))
    assert result == [0, 1, 1, 2, 3, 5, 8, 13]


def test_fibonacci_lst_negative():
    """Список с отрицательными числами"""
    test_list = [-5, -3, 0, 1, 2]
    result = list(EvenNumbersIterator(test_list))
    assert result == [0, 1, 2]