import ast
from typing import Any, Callable, Iterable

from ..models.diagnostic import IllegalAccess

DFFuncResult = tuple[set[str], set[str] | None, IllegalAccess | None]
DFMethodResult = tuple["DF", "DF | None", IllegalAccess | None]
_DFFunc = Callable[[set[str], list[ast.expr], list[ast.keyword]], DFFuncResult]


class _UnknownArg:
    pass


UnknownArg = _UnknownArg()


class DF:
    func_registry: dict[str, _DFFunc] = {}

    def __init__(self, columns: Iterable[str]):
        self.columns: set[str] = set(columns)

    def get_method(self, method_name: str) -> "DFMethod | None":
        if method_name in self.func_registry:
            return DFMethod(self, self.func_registry[method_name])
        return None

    @classmethod
    def method(cls, name: str):
        def decorator(func: _DFFunc):
            cls.func_registry[name] = func
            return func

        return decorator


class DFMethod:
    def __init__(self, df: DF, func: _DFFunc):
        self.df = df
        self.func = func

    def __call__(
        self, args: list[ast.expr], keywords: list[ast.keyword]
    ) -> DFMethodResult:
        """
        Returns a tuple with three elements:
        - The first element is the updated dataframe.
        - The second element is the returned dataframe, if any.
        - The third element is an `IllegalAccess` instance representing an error if the method call is illegal, or `None` if there is no error.
        """
        updated, returned, error = self.func(self.df.columns.copy(), args, keywords)
        return DF(updated), DF(returned) if returned is not None else None, error


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


@DF.method("assign")
def df_assign(
    columns: set[str], args: list[ast.expr], keywords: list[ast.keyword]
) -> DFFuncResult:
    _, keywords_value = _parse_args(args, keywords)
    returned = columns | set(keywords_value.keys())
    return columns, returned, None


@DF.method("insert")
def insert(
    columns: set[str], args: list[ast.expr], keywords: list[ast.keyword]
) -> DFFuncResult:
    args_value, keywords_value = _parse_args(args, keywords)
    if len(args_value) >= 2 and isinstance(args_value[1], str):
        columns.add(args_value[1])
    elif "column" in keywords_value and isinstance(keywords_value["column"], str):
        columns.add(keywords_value["column"])
    return columns, None, None
