"""
Reference types and type guards for AST node analysis.

This module provides:
- Type guard functions for narrowing AST expression types
- The `ColumnRef` dataclass representing a DataFrame column reference

These utilities are used by extractors to safely identify and extract
DataFrame column access patterns from Python AST nodes.
"""

import ast
from dataclasses import dataclass

from typing_extensions import TypeIs


def is_name(node: ast.expr) -> TypeIs[ast.Name]:
    """
    Check if an AST expression is a Name node.

    Args:
        node: The AST expression to check.

    Returns:
        True if the node is an `ast.Name`, narrowing the type for static analysis.

    Example:
        >>> node = ast.parse("df", mode="eval").body
        >>> is_name(node)
        True
    """
    return type(node) is ast.Name


def is_constant(node: ast.expr) -> TypeIs[ast.Constant]:
    """
    Check if an AST expression is a Constant node.

    Args:
        node: The AST expression to check.

    Returns:
        True if the node is an `ast.Constant`, narrowing the type for static analysis.

    Example:
        >>> node = ast.parse("'column_name'", mode="eval").body
        >>> is_constant(node)
        True
    """
    return type(node) is ast.Constant


def is_subscript(node: ast.expr) -> TypeIs[ast.Subscript]:
    """
    Check if an AST expression is a Subscript node.

    Args:
        node: The AST expression to check.

    Returns:
        True if the node is an `ast.Subscript`, narrowing the type for static analysis.

    Example:
        >>> node = ast.parse("df['A']", mode="eval").body
        >>> is_subscript(node)
        True
    """
    return type(node) is ast.Subscript


def is_binop(node: ast.expr) -> TypeIs[ast.BinOp]:
    """
    Check if an AST expression is a BinOp (binary operation) node.

    Args:
        node: The AST expression to check.

    Returns:
        True if the node is an `ast.BinOp`, narrowing the type for static analysis.

    Example:
        >>> node = ast.parse("df['A'] + df['B']", mode="eval").body
        >>> is_binop(node)
        True
    """
    return type(node) is ast.BinOp


def is_call(node: ast.expr) -> TypeIs[ast.Call]:
    """
    Check if an AST expression is a Call node.

    Args:
        node: The AST expression to check.

    Returns:
        True if the node is an `ast.Call`, narrowing the type for static analysis.

    Example:
        >>> node = ast.parse("df.sum()", mode="eval").body
        >>> is_call(node)
        True
    """
    return type(node) is ast.Call


def is_attribute(node: ast.expr) -> TypeIs[ast.Attribute]:
    """
    Check if an AST expression is an Attribute node.

    Args:
        node: The AST expression to check.

    Returns:
        True if the node is an `ast.Attribute`, narrowing the type for static analysis.

    Example:
        >>> node = ast.parse("df.columns", mode="eval").body
        >>> is_attribute(node)
        True
    """
    return type(node) is ast.Attribute


@dataclass(slots=True)
class ColumnRef:
    """
    Represents a DataFrame column reference extracted from AST.

    A column reference captures patterns like `df['col']` or `df[['a', 'b']]`
    where one or more columns are accessed.

    Attributes:
        node: The original `ast.Subscript` node for location tracking.
        df_name: The name of the DataFrame variable (e.g., 'df').
        col_names: List of column names being accessed (e.g., ['A'] or ['a', 'b']).

    Example:
        For the expression `df['amount']`:
        - `node`: The Subscript AST node
        - `df_name`: "df"
        - `col_names`: ["amount"]

        For the expression `df[['a', 'b']]`:
        - `node`: The Subscript AST node
        - `df_name`: "df"
        - `col_names`: ["a", "b"]
    """

    node: ast.Subscript
    df_name: str
    col_names: list[str]
