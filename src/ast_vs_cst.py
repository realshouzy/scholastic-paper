#!/usr/bin/env python3
"""The difference between ASTs and CSTs."""
from __future__ import annotations

__all__: tuple[str, ...] = ("main",)

import ast

import libcst as cst
import libcst.tool as cst_tool


def main() -> int:
    """Run the program."""
    source1: str = "a: int = 1 + 2"
    source2: str = "a: int = (1 + 2)  # some code comment"

    print(f"Syntax trees of {source1 = }:")
    print(f"{ast.dump(ast.parse(source1), indent=2)}")
    print(
        f"\n{cst_tool.dump(cst.parse_statement(source1), show_syntax=True, show_whitespace=True)}",  # noqa: E501 # pylint: disable=C0301
    )

    print(f"Syntax trees of {source2 = }:")
    print(f"{ast.dump(ast.parse(source2), indent=2)}")
    print(
        f"\n{cst_tool.dump(cst.parse_statement(source2), show_syntax=True, show_whitespace=True)}",  # noqa: E501 # pylint: disable=C0301
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
