#!/usr/bin/env python3
"""Running custom ``assert`` statements AST manipulation."""
from __future__ import annotations

import argparse
import ast
from typing import TYPE_CHECKING

from typing_extensions import override

from src.utils import exce_ast, resolved_path_from_str, source_to_ast

if TYPE_CHECKING:
    from pathlib import Path


def _get_variables_from_expression(node: ast.expr) -> set[str]:
    """Extract recursivly all variables from the given expression."""
    variables: set[str] = set()
    if isinstance(node, ast.Name):
        variables.add(node.id)
    elif isinstance(node, ast.BinOp):
        variables.update(_get_variables_from_expression(node.left))
        variables.update(_get_variables_from_expression(node.right))
    return variables


def _get_formatted_vars_as_ast(
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


def _get_if_body_as_ast(
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
                        ast.Constant(value=f"{ast.unparse(node.test)} = "),
                        ast.FormattedValue(
                            value=node.test,
                            conversion=114,
                        ),
                        ast.Constant(value=" ("),
                        *formatted_variables,
                        ast.Constant(value=")"),
                    ],
                ),
            ],
            keywords=[],
        ),
    )


def _rewrite_assert(node: ast.Assert) -> ast.If:
    new_body: list[ast.stmt] = []

    variables: set[str]
    formatted_variables: list[ast.Constant | ast.FormattedValue]
    if isinstance(node.test, ast.Name):
        new_body.append(
            ast.Expr(
                value=ast.Call(
                    func=ast.Name(id="print", ctx=ast.Load()),
                    args=[
                        ast.JoinedStr(
                            values=[
                                ast.Constant(value=f"{node.test.id} ="),
                                ast.FormattedValue(
                                    value=ast.Name(id=node.test.id, ctx=ast.Load()),
                                    conversion=114,
                                ),
                            ],
                        ),
                    ],
                    keywords=[],
                ),
            ),
        )
    elif isinstance(node.test, ast.Compare):
        variables = set()
        for sub_comp in [*node.test.comparators, node.test.left]:
            if isinstance(sub_comp, ast.Name):
                variables.add(sub_comp.id)
            elif isinstance(sub_comp, ast.BinOp):
                variables.update(_get_variables_from_expression(sub_comp))

        formatted_variables = _get_formatted_vars_as_ast(variables)

        new_body.append(_get_if_body_as_ast(node, formatted_variables))
    elif isinstance(node.test, ast.BinOp):
        variables = _get_variables_from_expression(node.test)

        formatted_variables = _get_formatted_vars_as_ast(variables)

        new_body.append(_get_if_body_as_ast(node, formatted_variables))
    else:
        new_body.append(ast.Pass())

    return ast.If(
        test=ast.UnaryOp(op=ast.Not(), operand=node.test),
        body=new_body,
        orelse=None,
    )


class AssertTransformer(ast.NodeTransformer):
    """Custom AST node visitor."""

    @override
    def visit_Assert(self, node: ast.Assert) -> ast.If:  # pylint: disable=C0103, C0116
        return _rewrite_assert(node)


def _run_custom_asserts(filepath: Path) -> int:
    tree: ast.Module = source_to_ast(filepath)
    rewriter: AssertTransformer = AssertTransformer()
    new_tree: ast.Module = rewriter.visit(tree)
    exce_ast(new_tree, filepath)
    return 0


def main() -> int:
    """Run the program."""
    parser: argparse.ArgumentParser = argparse.ArgumentParser()
    parser.add_argument("files", nargs="*", type=resolved_path_from_str)
    args: argparse.Namespace = parser.parse_args()

    exit_code: int = 0
    for file in args.files:
        exit_code |= _run_custom_asserts(file)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
