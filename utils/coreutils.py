def rangeCheck(v: int, r: tuple[int, int], d: int = None):
    if r[0] <= v <= r[1]:
        return v
    else:
        return d if d is not None else r[0]


def printf(formatStr: str, *args):
    print(formatStr % args, end='')


def inRange(__i: int, __range: tuple[int, int]):
    return __range[0] <= __i <= __range[1]


def minCheck(__v: int, __min: int, __default: int):
    return __v if __v > __min else __default


def maxCheck(__v: int, __max: int, __default: int):
    return __v if __v < __max else __default
