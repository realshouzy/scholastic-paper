"""Example code for linting."""
from __future__ import annotations


def f1() -> None:
    ...


def f2() -> None:
    pass


def f3(arg: str) -> None:  # noqa: ARG001 # pylint: disable=W0613
    """Do nothing."""
    pass  # noqa: PIE790 # pylint: disable=W0107
