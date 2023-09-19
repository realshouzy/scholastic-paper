"""Demonstration of linting using AST."""
from __future__ import annotations

import argparse
import ast
from pathlib import Path
from typing import NamedTuple

from typing_extensions import override


class _ErrorInfo(NamedTuple):
    func_name: str
    lineno: int
    offset: int


class _Visitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.errors: list[_ErrorInfo] = []

    @override
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        match node:
            case ast.FunctionDef(
                name=func_name,
                body=[ast.Expr(value=ast.Constant(value=body_placeholder))],
            ):
                if body_placeholder is Ellipsis:
                    self.errors.append(
                        _ErrorInfo(
                            func_name,
                            node.body[0].value.lineno,  # type: ignore[attr-defined]
                            node.body[0].value.col_offset,  # type: ignore[attr-defined]
                        ),
                    )
            case _:
                pass
        self.generic_visit(node)


def _resolved_path_from_str(path_as_str: str) -> Path:
    return Path(path_as_str.strip()).resolve()


def _lint_file(filepath: Path) -> int:
    if filepath.suffix == ".pyi":
        return 1

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
