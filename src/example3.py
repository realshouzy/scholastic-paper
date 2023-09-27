"""Example Nr. 3."""
from __future__ import annotations

# pylint: skip-file

a, b = 1, 2


def func() -> None:
    """Do some assertion."""
    c: int = 3
    assert a + b - c


if __name__ == "__main__":
    func()
