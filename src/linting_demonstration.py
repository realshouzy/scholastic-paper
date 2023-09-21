#!/usr/bin/env python3
"""Demonstration of linting using AST."""
from __future__ import annotations

import argparse
import ast
import builtins
from pathlib import Path
from typing import NamedTuple

from typing_extensions import override


class ErrorInfo(NamedTuple):
    func_name: str
    lineno: int
    offset: int


class Visitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.errors: list[ErrorInfo] = []

    @override
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        found: bool = False
        match node.body:
            case [
                ast.Expr(value=ast.Constant(value=val)),
                ast.Expr(value=ast.Constant(value=builtins.Ellipsis)),
            ] | [ast.Expr(value=ast.Constant(value=val)), ast.Pass()]:
                if isinstance(val, str):
                    found = True
            case [ast.Expr(value=ast.Constant(value=builtins.Ellipsis))] | [ast.Pass()]:
                found = True
            case _:
                pass

        if found:
            self.errors.append(
                ErrorInfo(
                    node.name,
                    node.body[0].lineno,
                    node.body[0].col_offset,
                ),
            )

        self.generic_visit(node)


def _resolved_path_from_str(path_as_str: str) -> Path:
    return Path(path_as_str.strip()).resolve()


def _lint_file(filepath: Path) -> int:
    if filepath.suffix == ".pyi":
        return 1

    visitor: Visitor = Visitor()
    contents: str = filepath.read_text(encoding="utf-8")
    tree: ast.Module = ast.parse(contents, filename=filepath.name)
    visitor.visit(tree)
    print(visitor.errors)
    return 0


def main() -> int:
    """Run the program."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*", type=_resolved_path_from_str)
    args: argparse.Namespace = parser.parse_args()

    exit_code: int = 0
    for file in args.files:
        exit_code |= _lint_file(file)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
