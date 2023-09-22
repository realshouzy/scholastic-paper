#!/usr/bin/env python3
"""Demonstration of linting using AST."""
from __future__ import annotations

__all__: list[str] = ["main", "lint_file", "TryBlockVisitor"]

import argparse
import ast
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from typing_extensions import override

from src.ast_checks import BareExceptNotAllowed, EmptyExceptBodyNotAllowed

if TYPE_CHECKING:
    from src.ast_checks import ErrorInfo, TryBlockLinter


class TryBlockVisitor(ast.NodeVisitor):
    """Custom AST visitor class overwriting the ``visit_Try`` method."""

    checks: ClassVar[list[type[TryBlockLinter]]] = [
        BareExceptNotAllowed,
        EmptyExceptBodyNotAllowed,
    ]

    def __init__(self) -> None:
        self.errors: list[ErrorInfo] = []

    @override
    def visit_Try(self, node: ast.Try) -> None:  # pylint: disable=C0103, C0116
        for check in self.checks:
            if (match := check.check(node)) is not None:
                self.errors.append(match)
        self.generic_visit(node)


def lint_file(filepath: Path) -> int:
    """Lint the given file."""
    contents: str = filepath.read_text(encoding="utf-8")
    tree: ast.Module = ast.parse(contents, filename=filepath.name)

    visitor: TryBlockVisitor = TryBlockVisitor()
    visitor.visit(tree)
    for rule, lineno, offset in visitor.errors:
        print(f"{rule} {filepath.name}:{lineno}:{offset}")
    return 0


def _resolved_path_from_str(path_as_str: str) -> Path:
    """Return the absolute path given a string of a path."""
    return Path(path_as_str.strip()).resolve()


def main() -> int:
    """Run the program."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*", type=_resolved_path_from_str)
    args: argparse.Namespace = parser.parse_args()

    exit_code: int = 0
    for file in args.files:
        exit_code |= lint_file(file)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
