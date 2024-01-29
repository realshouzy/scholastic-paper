#!/usr/bin/env python3
"""Running custom ``assert`` statements AST manipulation."""
from __future__ import annotations

__all__: list[str] = ["AssertTransformer", "main"]

import argparse
import ast
from typing import TYPE_CHECKING

from typing_extensions import override

from src.utils import exce_ast, resolved_path_from_str, source_to_ast

if TYPE_CHECKING:
    from pathlib import Path


class AssertTransformer(ast.NodeTransformer):
    """Custom AST node visitor overriding the ``visit_Assert`` method."""

    def __init__(self, file: Path) -> None:
        self.file: Path = file

    @override
    def visit_Assert(self, node: ast.Assert) -> ast.If:  # pylint: disable=C0103, C0116
        return self.rewrite_assert(node)

    def rewrite_assert(self, node: ast.Assert) -> ast.If:
        """Rewrite the given assert statement.

        E.g.:
        >>> a, b, c = 1, 2, 3
        >>> assert a + b < c
        >>> # will be transformed to
        >>> if a + b < c:
        ...     print(f"<filepath>:<linenumber><columnoffset> assert a + b < c failed ({a=}, {b=}, {c=})")
        """  # noqa: E501 # pylint: disable=C0301
        variables: set[str] = self._get_variables_from_expression(node.test)

        formatted_variables: list[ast.Constant | ast.FormattedValue] = (
            self._get_formatted_vars_as_ast(variables)
        )

        if_stmt_body: ast.Expr = self._get_if_stmt_body_as_ast(
            node,
            formatted_variables,
        )

        return ast.If(
            test=ast.UnaryOp(op=ast.Not(), operand=node.test),
            body=[if_stmt_body],
            orelse=None,
        )

    def _get_variables_from_expression(self, node: ast.expr) -> set[str]:
        """Extract recursivly all variables from the given expression."""
        variables: set[str] = set()
        if isinstance(node, ast.Name):
            variables.add(node.id)
        elif isinstance(node, ast.UnaryOp):
            variables.update(self._get_variables_from_expression(node.operand))
        elif isinstance(node, ast.BoolOp):
            for val in node.values:
                variables.update(self._get_variables_from_expression(val))
        elif isinstance(node, ast.BinOp):
            variables.update(self._get_variables_from_expression(node.left))
            variables.update(self._get_variables_from_expression(node.right))
        elif isinstance(node, ast.Compare):
            for child in [*node.comparators, node.left]:
                variables.update(self._get_variables_from_expression(child))
        else:
            raise NotImplementedError
        return variables

    def _get_formatted_vars_as_ast(
        self,
        variables: set[str],
    ) -> list[ast.Constant | ast.FormattedValue]:
        """Get the formatted string of variables as the AST given a set of variables."""
        formatted_variables: list[ast.Constant | ast.FormattedValue] = []
        for pos, var in enumerate(variables, start=1):
            formatted_variables.append(ast.Constant(value=f"{var}="))
            formatted_variables.append(
                ast.FormattedValue(
                    value=ast.Name(id=var, ctx=ast.Load()),
                    conversion=114,
                ),
            )
            if pos != len(variables):
                formatted_variables.append(ast.Constant(value=", "))
        return formatted_variables

    def _get_if_stmt_body_as_ast(
        self,
        node: ast.Assert,
        formatted_variables: list[ast.Constant | ast.FormattedValue],
    ) -> ast.Expr:
        """Get the body of the ``if`` statement."""
        return ast.Expr(
            value=ast.Call(
                func=ast.Name(id="print", ctx=ast.Load()),
                args=[
                    ast.JoinedStr(
                        values=[
                            ast.Constant(
                                value=f"{self.file}:{node.lineno}:{node.col_offset} {ast.unparse(node)} failed (",  # noqa: E501 # pylint: disable=C0301
                            ),
                            *formatted_variables,
                            ast.Constant(value=")"),
                        ],
                    ),
                ],
                keywords=[],
            ),
        )


def _run_custom_asserts(filepath: Path) -> int:
    """Run custom assert statements in the provided file."""
    tree: ast.Module = source_to_ast(filepath)
    transformer: AssertTransformer = AssertTransformer(filepath)
    new_tree: ast.Module = transformer.visit(tree)
    exce_ast(new_tree)
    return 0


def main() -> int:
    """Run the program."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument(
        "files",
        nargs="*",
        type=resolved_path_from_str,
        help="Files to be processed",
    )
    args: argparse.Namespace = parser.parse_args()

    exit_code: int = 0
    for file in args.files:
        exit_code |= _run_custom_asserts(file)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
