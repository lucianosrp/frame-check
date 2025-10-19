import ast
from dataclasses import dataclass
from typing import Self


@dataclass(kw_only=True, order=True)
class CodePosition:
    """Represents a point in source code."""

    row: int
    col: int = 0


@dataclass(kw_only=True, order=True)
class CodeRegion:
    """Represents an inclusive region in source code."""

    start: CodePosition
    end: CodePosition

    def __post_init__(self):
        if self.end < self.start:
            raise ValueError("End position must not be before start position.")

    @classmethod
    def from_ast_node(cls, node: ast.stmt | ast.expr) -> Self:
        start_position = CodePosition(row=node.lineno, col=node.col_offset)
        end_position = CodePosition(
            row=node.end_lineno or node.lineno,
            col=(node.end_col_offset or node.col_offset) - 1,  # make end inclusive
        )
        return cls(start=start_position, end=end_position)
