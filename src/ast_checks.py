"""Module containing the classes that check the AST for certain patterns."""

from __future__ import annotations

__all__: tuple[str, ...] = ("BareExceptNotAllowed", "EmptyExceptBodyNotAllowed")

import ast
import builtins
from typing import ClassVar, NamedTuple, Protocol


class ErrorInfo(NamedTuple):
    """A named tuple representing error information."""

    msg: str
    lineno: int
    offset: int


class TryBlockLinter(Protocol):
    """Protocol class for ``try`` block linters."""

    msg: ClassVar[str]

    @classmethod
    def check(cls, node: ast.Try) -> list[ErrorInfo]:
        """Check for some pattern in the provided ``try`` block AST."""


class TryBlockFormatter(Protocol):
    """Protocol class for ``try`` block formatters."""

    msg: ClassVar[str]

    @classmethod
    def check(cls, node: ast.Try) -> list[ErrorInfo]:
        """Check for some pattern in the provided ``try`` block AST."""

    @classmethod
    def fix(cls, node: ast.Try) -> tuple[ast.Try, list[ErrorInfo]]:
        """Rewrite the ``try`` block AST so that it fixes a certain problem."""


class BareExceptNotAllowed:
    """Class for handling bare ``except`` clauses."""

    msg: ClassVar[str] = "bare exception"

    @classmethod
    def check(cls, node: ast.Try) -> list[ErrorInfo]:
        """Check for a bare except clause in the provided ``try`` block AST."""
        return [
            ErrorInfo(cls.msg, handler.lineno, handler.col_offset)
            for handler in node.handlers
            if handler.type is None
        ]

    @classmethod
    def fix(cls, node: ast.Try) -> tuple[ast.Try, list[ErrorInfo]]:
        """Rewrite all bare ``except:`` blocks to ``except Exception:``."""
        fixes: list[ErrorInfo] = []
        for handler in node.handlers:
            if handler.type is None:
                handler.type = ast.Name(id="Exception", ctx=ast.Load())
                fixes.append(ErrorInfo(cls.msg, handler.lineno, handler.col_offset))
        return node, fixes


class EmptyExceptBodyNotAllowed:
    """Class for handling empty bodies of ``except`` clauses."""

    msg: ClassVar[str] = "empty except body"

    @classmethod
    def check(cls, node: ast.Try) -> list[ErrorInfo]:
        """Check for an empty ``except`` body in the provided ``try`` block AST.

        'Empty' meaning there is no exception handling, e.g.:
        >>> try:
        ...     ... # some code
        ... except SomeError:
        ...     pass # or '...'
        """
        matches: list[ErrorInfo] = []
        for handler in node.handlers:
            match handler:
                case ast.ExceptHandler(
                    body=[ast.Pass() as empty_except_body]
                    | [
                        ast.Expr(
                            value=ast.Constant(value=builtins.Ellipsis),
                        ) as empty_except_body,
                    ],
                ):
                    matches.append(
                        ErrorInfo(
                            cls.msg,
                            empty_except_body.lineno,
                            empty_except_body.col_offset,
                        ),
                    )
                case _:
                    pass
        return matches
