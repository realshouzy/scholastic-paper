"""Module containing the classes that check the AST for certain patterns."""
from __future__ import annotations

__all__: list[str] = ["BareExceptNotAllowed", "EmptyExceptBodyNotAllowed"]

import ast
import builtins
from typing import ClassVar, NamedTuple, Protocol


class ErrorInfo(NamedTuple):
    """A named tuple representing error information."""

    rule: str
    lineno: int
    offset: int


class TryBlockLinter(Protocol):
    """Class protocol for ``try`` block linters."""

    rule: ClassVar[str]

    @classmethod
    def check(cls, node: ast.Try) -> ErrorInfo | None:
        """Check for some pattern in the provided ``try`` block AST."""


class BareExceptNotAllowed:
    """Class for checking bare ``except`` clauses."""

    rule: ClassVar[str] = "TRY01"

    @classmethod
    def check(cls, node: ast.Try) -> ErrorInfo | None:
        """Check for a bare except clause in the provided ``try`` block AST."""
        match node.handlers:
            case [*_, ast.ExceptHandler(body=_) as bare_except]:
                return ErrorInfo(cls.rule, bare_except.lineno, bare_except.col_offset)
            case _:
                return None


class EmptyExceptBodyNotAllowed:
    """Class for checking empty bodies of ``except`` clauses."""

    rule: ClassVar[str] = "TRY02"

    @classmethod
    def check(cls, node: ast.Try) -> ErrorInfo | None:
        """Check for an empty ``except`` body in the provided ``try`` block AST.

        'Empty' meaning there is no exception handling, e.g.:
        >>> try:
        ...     # some code
        ... except SomeError:
        ...     pass # or '...'
        """
        match node.handlers:
            case [
                *_,
                ast.ExceptHandler(
                    type=_,
                    body=[ast.Pass() as empty_except_body]
                    | [
                        ast.Expr(
                            value=ast.Constant(value=builtins.Ellipsis),
                        ) as empty_except_body,
                    ],
                ),
            ]:
                return ErrorInfo(
                    cls.rule,
                    empty_except_body.lineno,
                    empty_except_body.col_offset,
                )
            case _:
                return None
