#!/usr/bin/env python3


class a:
    pass


def get_b():
    print(a.b)


if __name__ == "__main__":
    a.b = 3
    get_b()
