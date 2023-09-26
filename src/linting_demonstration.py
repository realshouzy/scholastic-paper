#!/usr/bin/env python3
"""Demonstration of linting using AST."""
from __future__ import annotations

__all__: list[str] = ["main", "lint_file", "TryBlockVisitor"]

import argparse
import ast
from typing import TYPE_CHECKING, ClassVar

from typing_extensions import override

from src.ast_checks import BareExceptNotAllowed, EmptyExceptBodyNotAllowed
from src.utils import ast_to_source, resolved_path_from_str, source_to_ast

if TYPE_CHECKING:
    from pathlib import Path

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
            self.errors.extend(check.check(node))
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


def lint_file(filepath: Path) -> int:
    """Lint the given file."""
    tree: ast.Module = source_to_ast(filepath)
    visitor: TryBlockVisitor = TryBlockVisitor()
    visitor.visit(tree)

    if not visitor.errors:
        return 0

    for msg, lineno, offset in visitor.errors:
        print(f"{filepath}:{lineno}:{offset}: Found {msg}")
    return 1


def rewrite_file(filepath: Path) -> int:
    """Rewrite the given file."""
    tree: ast.Module = source_to_ast(filepath)
    rewriter: TryBlockRewriter = TryBlockRewriter()
    new_tree: ast.Module = rewriter.visit(tree)

    if not rewriter.errors:
        return 0

    ast_to_source(new_tree, filepath)
    for msg, lineno, offset in rewriter.errors:
        print(f"{filepath}:{lineno}:{offset}: Fixed {msg}")
    return 1


def main() -> int:
    """Run the program."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*", type=resolved_path_from_str)
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Attempt to automatically fix violations that can be fixed",
    )
    args: argparse.Namespace = parser.parse_args()

    exit_code: int = 0
    for file in args.files:
        exit_code |= lint_file(file)
        if args.fix:
            exit_code |= rewrite_file(file)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
