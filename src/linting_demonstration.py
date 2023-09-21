#!/usr/bin/env python3
"""Demonstration of linting using AST."""
from __future__ import annotations

__all__: list[str] = ["main", "lint_file", "Visitor"]

import argparse
import ast
from pathlib import Path
from typing import NamedTuple

from typing_extensions import override


class ErrorInfo(NamedTuple):
    lineno: int
    offset: int


class Visitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.errors: list[ErrorInfo] = []

    @override
    def visit_Try(self, node: ast.Try) -> None:
        match node.handlers:
            # TODO(realshouzy): Fix this
            # case [
            #     *_,
            #     ast.ExceptHandler(
            #         type=ast.Name(id=_, ctx=ast.Load()),
            #         body=[ast.Pass() as empty_body]
            #         | [
            #             ast.Expr(
            #                 value=ast.Constant(value=builtins.Ellipsis),
            #             ) as empty_body,
            #         ],
            #     ),
            # ]:
            #     self.errors.append(
            #         ErrorInfo(
            #             empty_body.lineno,
            #             empty_body.col_offset,
            #         ),
            #     )
            case [*_, ast.ExceptHandler(body=_) as bare_except]:
                self.errors.append(
                    ErrorInfo(
                        bare_except.lineno,
                        bare_except.col_offset,
                    ),
                )
            case _:
                pass
        self.generic_visit(node)


def _resolved_path_from_str(path_as_str: str) -> Path:
    return Path(path_as_str.strip()).resolve()


def lint_file(filepath: Path) -> int:
    """Lint the given file."""
    contents: str = filepath.read_text(encoding="utf-8")
    tree: ast.Module = ast.parse(contents, filename=filepath.name)

    visitor: Visitor = Visitor()
    visitor.visit(tree)
    for (
        lineno,
        offset,
    ) in visitor.errors:
        print(f"{filepath.name}:{lineno}:{offset}")
    return 0


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
