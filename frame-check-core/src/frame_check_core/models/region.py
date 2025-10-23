import ast
from dataclasses import dataclass
from typing import Self


@dataclass(kw_only=True, order=True, slots=True, frozen=True)
class CodePosition:
    """Represents a point in source code."""

    row: int
    col: int = 0


@dataclass(kw_only=True, order=True, slots=True, frozen=True)
class CodeRegion:
    """Represents a region (end exclusive) in source code."""

    start: CodePosition
    end: CodePosition

    def __post_init__(self):
        if self.end < self.start:
            raise ValueError("End position must not be before start position.")

    @property
    def is_empty(self) -> bool:
        """Check if the region is empty"""

        return self.start == self.end

    @property
    def is_same_row(self) -> bool:
        """Check if the region is within the same row"""

        return self.start.row == self.end.row

    @property
    def is_same_column(self) -> bool:
        """Check if the region is within the same column"""

        return self.start.col == self.end.col

    @classmethod
    def from_ast_node(cls, node: ast.stmt | ast.expr) -> Self:
        """Construct a CodeRegion from an AST node."""

        start_position = CodePosition(row=node.lineno, col=node.col_offset)

        #! lineno and end_lineno are not exclusive, so we add 1
        exclusive_end_row = (node.end_lineno or node.lineno) + 1
        exclusive_end_col_offset = node.end_col_offset or node.col_offset
        end_position = CodePosition(
            row=exclusive_end_row,
            col=exclusive_end_col_offset,
        )
        return cls(start=start_position, end=end_position)
