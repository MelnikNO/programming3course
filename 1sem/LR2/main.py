import functools


def fib_elem_gen():
    """Генератор, возвращающий элементы ряда Фибоначчи"""
    a = 0
    b = 1

    while True:
        yield a
        res = a + b
        a = b
        b = res


def fib_coroutine(g):
    @functools.wraps(g)
    def inner(*args, **kwargs):
        gen = g(*args, **kwargs)
        gen.send(None)
        return gen

    return inner


@fib_coroutine
def my_genn():
    """Сопрограмма"""
    l = []

    while True:
        number_of_fib_elem = yield l
        l = []

        if number_of_fib_elem <= 0:
            continue

        fib_gen = fib_elem_gen()
        for i in range(number_of_fib_elem):
            l.append(next(fib_gen))

        yield l


# часть 2
class FibonacchiLst():

    def __init__(self, instance):
        self.instance = instance
        self.idx = 0
        max_val = max(instance) if instance else 0
        self.fib_numbers = set()
        fib_gen = fib_elem_gen()

        while True:
            num = next(fib_gen)
            if num > max_val:
                break
            self.fib_numbers.add(num)

    def __iter__(self):
        return self  # возвращает экземпляр класса, реализующего протокол итераторов

    def __next__(self):  # возвращает следующий по порядку элемент итератора
        while True:
            try:
                res = self.instance[self.idx]  # получаем очередной элемент из iterable

            except IndexError:
                raise StopIteration

            if res in self.fib_numbers:  # проверяем на четность элемента
                self.idx += 1  # если четный, возвращаем значение и увеличиваем индекс
                return res

            self.idx += 1  # если нечетный, то просто увеличиваем индекс


if __name__ == "__main__":
    i = int(input("Введите количество для вывода чисел Фибоначчи: ", ))
    gen = my_genn()
    print(gen.send(i))

    print("\nТестирование FibonacchiLst:")
    numbers = list(map(int, input("Введите числа через пробел: ").split()))
    fib_iterator = FibonacchiLst(numbers)
    result = list(fib_iterator)
    print(f"Исходный список: {numbers}")
    print(f"Числа Фибоначчи: {result}")
