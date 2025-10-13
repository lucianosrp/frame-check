import ast
from typing import Any, Iterable

from frame_check_core._models import ColumnInstance


CallResult = tuple[
    set[str], set[str] | None, ColumnInstance | None
]  # (updated, returned, error)


def _maybe_constant_str(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _parse_str_args(
    args: list[ast.expr],
    keywords: list[ast.keyword],
) -> tuple[list[str | None], dict[str, Any]]:
    args_value: list[str | None] = []
    keywords_value: dict[str, Any] = {}
    for arg_node in args:
        arg_value = _maybe_constant_str(arg_node)
        args_value.append(arg_value)
    for keyword_node in keywords:
        if keyword_node.arg is not None:
            keyword_arg = _maybe_constant_str(keyword_node)
            if keyword_arg is not None:
                keywords_value[keyword_arg] = keyword_arg
    return args_value, keywords_value


class DF:
    """
    Each method in this class represents a DataFrame method.

    Each method returns a tuple with three elements:
    - The first element is the updated columns of `self`.
    - The second element is the columns of the returned dataframe, or `None` if the method does not return a dataframe.
    - The third element is a `ColumnInstance` representing an error if the method call is illegal, or `None` if there is no error.

    Currently we suppose column names are `str`, so args can only be `str` or `None`. All non-str args are supposed be converted to `None`.

    The internal state of the class will also be updated if the method modifies the dataframe in place.
    """

    def __init__(self, columns: Iterable[str]):
        self._columns = set(columns)

    @property
    def columns(self) -> set[str]:
        return self._columns.copy()

    def assign(self, args: list[ast.expr], keywords: list[ast.keyword]) -> CallResult:
        _, keywords_value = _parse_str_args(args, keywords)
        returned = self._columns | set(keywords_value.keys())
        return self.columns, returned, None

    def insert(self, args: list[ast.expr], keywords: list[ast.keyword]) -> CallResult:
        args_value, keywords_value = _parse_str_args(args, keywords)
        if len(args_value) >= 2 and isinstance(args_value[1], str):
            self._columns.add(args_value[1])
        if "column" in keywords_value and isinstance(keywords_value["column"], str):
            self._columns.add(keywords_value["column"])
        return self.columns, None, None
