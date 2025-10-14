import ast
from typing import Any, Callable

from ..util.column import DFColumns
from ..models.diagnostic import IllegalAccess

DFMethodResult = tuple[DFColumns, DFColumns | None, IllegalAccess | None]
_DFMethodFunc = Callable[[DFColumns, list[ast.expr], list[ast.keyword]], DFMethodResult]


class _UnknownArg:
    pass


UnknownArg = _UnknownArg()


class DFMethod:
    method_registry: dict[str, _DFMethodFunc] = {}

    def __init__(self, columns: DFColumns, func: _DFMethodFunc):
        self.columns = columns
        self.func = func

    def __call__(self, args: list[ast.expr], keywords: list[ast.keyword]):
        """
        Returns a tuple with three elements:
        - The first element is the updated columns of `self`.
        - The second element is the columns of the returned dataframe, or `None` if the method does not return a dataframe.
        - The third element is an `IllegalAccess` instance representing an error if the method call is illegal, or `None` if there is no error.
        """
        updated, returned, error = self.func(self.columns, args, keywords)
        self.columns = updated
        return updated, returned, error

    @classmethod
    def register(cls, name: str):
        def decorator(func: _DFMethodFunc):
            cls.method_registry[name] = func
            return func

        return decorator

    @classmethod
    def get_method(cls, columns: DFColumns, method_name: str) -> "DFMethod | None":
        if method_name in cls.method_registry:
            return DFMethod(columns, cls.method_registry[method_name])
        return None


def _parse_args(
    args: list[ast.expr],
    keywords: list[ast.keyword],
) -> tuple[list[Any], dict[str, Any]]:
    args_value: list[Any] = []
    keywords_value: dict[str, Any] = {}
    for arg_node in args:
        if isinstance(arg_node, ast.Constant):
            args_value.append(arg_node.value)
        else:
            args_value.append(UnknownArg)
    for keyword_node in keywords:
        if isinstance(keyword_node.arg, str):
            if isinstance(keyword_node.value, ast.Constant):
                keywords_value[keyword_node.arg] = keyword_node.value.value
            else:
                keywords_value[keyword_node.arg] = UnknownArg
    return args_value, keywords_value


@DFMethod.register("assign")
def df_assign(
    columns: DFColumns, args: list[ast.expr], keywords: list[ast.keyword]
) -> DFMethodResult:
    _, keywords_value = _parse_args(args, keywords)
    returned = columns | set(keywords_value.keys())
    return columns, returned, None


@DFMethod.register("insert")
def insert(
    columns: DFColumns, args: list[ast.expr], keywords: list[ast.keyword]
) -> DFMethodResult:
    args_value, keywords_value = _parse_args(args, keywords)
    if len(args_value) >= 2 and isinstance(args_value[1], str):
        columns.add(args_value[1])
    elif "column" in keywords_value and isinstance(keywords_value["column"], str):
        columns.add(keywords_value["column"])
    return columns, None, None
