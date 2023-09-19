"""Demonstration of linting using AST."""
from __future__ import annotations

import argparse
import ast
from pathlib import Path
from typing import Final, NamedTuple

from typing_extensions import override

_ERROR_MSG: Final[
    str
] = "'...' detected as placeholder for empty function body, use 'pass' instead"


class _ErrorInfo(NamedTuple):
    lineno: int
    offset: int
    msg: str
    cls: type


class _Visitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.errors: list[_ErrorInfo] = []

    @override
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if len(node.body) == 1 and isinstance(node.body[0], ast.Expr):
            func_body: ast.Expr = node.body[0]
            if (
                isinstance(func_body.value, ast.Constant)
                and hasattr(func_body.value, "value")
                and isinstance(
                    func_body.value.value,
                    Ellipsis.__class__,
                )
            ):
                self.errors.append(
                    _ErrorInfo(
                        func_body.value.lineno,
                        func_body.value.col_offset,
                        _ERROR_MSG,
                        self.__class__,
                    ),
                )
        self.generic_visit(node)


def _resolved_path_from_str(path_as_str: str) -> Path:
    return Path(path_as_str.strip()).resolve()


def _lint_file(filepath: Path) -> int:
    visitor: _Visitor = _Visitor()
    contents: str = filepath.read_text(encoding="utf-8")
    tree = ast.parse(contents, filename=filepath.name)
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
