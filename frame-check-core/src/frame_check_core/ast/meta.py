import ast

from .method import DFColumns, DFMethod

RESULT = DFColumns | DFMethod

_ASSIGNING_ATTR = "_frame_checker_assigning"
_RESULT_ATTR = "_frame_checker_result_columns"


def is_assigning(node: ast.Subscript) -> bool:
    return getattr(node, _ASSIGNING_ATTR, False)


def set_assigning(node: ast.Subscript) -> None:
    setattr(node, _ASSIGNING_ATTR, True)


def get_result(node: ast.AST) -> RESULT | None:
    return getattr(node, _RESULT_ATTR, None)


def set_result(node: ast.AST, result: RESULT) -> None:
    setattr(node, _RESULT_ATTR, result)
