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
    from src.ast_checks import ErrorInfo, TryBlockFormatter, TryBlockLinter


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
            if matches := check.check(node):
                self.errors.extend(matches)
        self.generic_visit(node)


class TryBlockRewriter(ast.NodeTransformer):
    """Custom AST transformer class overwriting the ``visit_Try`` method."""

    fixers: ClassVar[list[type[TryBlockFormatter]]] = [
        BareExceptNotAllowed,
    ]

    def __init__(self) -> None:
        self.errors: list[ErrorInfo] = []

    @override
    def visit_Try(self, node: ast.Try) -> ast.Try:  # pylint: disable=C0103, C0116
        for fix in self.fixers:
            node, fixes = fix.fix(node)
            self.errors.extend(fixes)
        return node


def _source_to_ast(filepath: Path) -> ast.Module:
    """Return the AST of the given Python file."""
    contents: str = filepath.read_text(encoding="utf-8")
    return ast.parse(contents, filename=filepath.name)


def _ast_to_source(tree: ast.AST, filepath: Path) -> None:
    """Convert the given AST back to source code and write it into the given file."""
    contents: str = ast.unparse(ast.fix_missing_locations(tree))
    filepath.write_text(contents, encoding="utf-8")


def lint_file(filepath: Path) -> int:
    """Lint the given file."""
    tree: ast.Module = _source_to_ast(filepath)
    visitor: TryBlockVisitor = TryBlockVisitor()
    visitor.visit(tree)

    if not visitor.errors:
        return 0

    for msg, lineno, offset in visitor.errors:
        print(f"{filepath}:{lineno}:{offset}: Found {msg}")
    return 1


def rewrite_file(filepath: Path) -> int:
    """Rewrite the given file."""
    tree: ast.Module = _source_to_ast(filepath)
    rewriter: TryBlockRewriter = TryBlockRewriter()
    new_tree: ast.Module = rewriter.visit(tree)

    if not rewriter.errors:
        return 0

    _ast_to_source(new_tree, filepath)
    for msg, lineno, offset in rewriter.errors:
        print(f"{filepath}:{lineno}:{offset}: Fixed {msg}")
    return 1


def _resolved_path_from_str(path_as_str: str) -> Path:
    """Return the absolute path given a string of a path."""
    return Path(path_as_str.strip()).resolve()


def main() -> int:
    """Run the program."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*", type=_resolved_path_from_str)
    parser.add_argument("--fix", action="store_true")
    args: argparse.Namespace = parser.parse_args()

    exit_code: int = 0
    for file in args.files:
        exit_code |= lint_file(file)
        if args.fix:
            exit_code |= rewrite_file(file)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
