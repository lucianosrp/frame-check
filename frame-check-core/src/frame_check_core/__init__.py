import ast
from dataclasses import dataclass, field
from typing import NamedTuple

from frame_check_core._models import WrappedNode


@dataclass
class FrameInstance:
    _node: ast.Assign
    lineno: int
    id: str
    args: list[WrappedNode[ast.arg]]
    keywords: list[WrappedNode[ast.keyword]]

    @property
    def columns(self) -> list[str]:
        arg = self.args[0]
        keys = arg.get("keys")
        return [key.value for key in keys.val] if keys.val is not None else []

    @classmethod
    def from_node(cls, node: ast.Assign) -> "FrameInstance | None":
        n = WrappedNode[ast.Assign](node)
        call_args = n.get("value").get("args")
        call_keywords = n.get("value").get("keywords")
        name = n.targets[0].get("id")

        if (
            name.val is not None
            and call_args.val is not None
            and call_keywords.val is not None
        ):
            return cls(
                node,
                node.lineno,
                name.val,
                [WrappedNode[ast.arg](arg) for arg in call_args.val],  # ty: ignore
                [
                    WrappedNode[ast.keyword](kw)
                    for kw in call_keywords.val  # ty: ignore
                ],
            )


@dataclass
class DictAssignment:
    _node: ast.Assign
    lineno: int
    id: str
    keys: list[str]

    @classmethod
    def from_node(cls, node: ast.Assign) -> "DictAssignment | None": ...  # TODO


@dataclass
class ColumnAccess:
    _node: ast.Subscript
    lineno: int
    id: str
    frame: FrameInstance


class FrameHistoryKey(NamedTuple):
    lineno: int
    id: str


@dataclass
class FrameHistory:
    frames: dict[FrameHistoryKey, FrameInstance] = field(default_factory=dict)

    def add(self, frame: FrameInstance):
        key = FrameHistoryKey(frame.lineno, frame.id)
        self.frames[key] = frame

    def get_at(self, lineno: int, id: str) -> FrameInstance | None:
        return self.frames.get(FrameHistoryKey(lineno, id))

    def get_before(self, lineno: int, id: str) -> FrameInstance | None:
        keys = sorted(self.frames.keys(), key=lambda k: k.lineno, reverse=True)
        for key in keys:
            if key.lineno < lineno and key.id == id:
                return self.frames[key]
        return None

    def frame_keys(self) -> list[str]:
        return [frame.id for frame in self.frames.values()]


class FrameChecker(ast.NodeVisitor):
    def __init__(self):
        self.import_aliases = {}
        self.dict_data: dict[str, DictAssignment] = {}
        self.frames: FrameHistory = FrameHistory()
        self.column_accesses: dict[str, ColumnAccess] = {}

    @staticmethod
    def _is_dict(node: ast.Assign) -> bool:
        return isinstance(node.value, ast.Dict)

    def maybe_get_df(self, node: ast.Assign) -> ast.Assign | None:
        """Check if an assignment creates a pandas Frame."""
        func = WrappedNode(node.value).get("func")
        val = func.get("value")
        # Check if this is a pandas Frame constructor
        if (
            val.get("id").val in self.import_aliases.values()
            and func.get("attr").val == "DataFrame"
        ):
            return node

        return None

    def maybe_assign_df(self, node: ast.Assign) -> bool:
        maybe_df = self.maybe_get_df(node)
        if maybe_df is not None:
            if frame := FrameInstance.from_node(maybe_df):
                self.frames.add(frame)
                return True
        return False

    def maybe_assign_dict(self, node: ast.Assign) -> bool:
        if self._is_dict(node):
            dict_def = WrappedNode[ast.Name](node.targets[0])
            dict_assignment = DictAssignment.from_node(node)
            if dict_assignment is not None:
                if val := dict_def.get("id").val:
                    self.dict_data[val] = dict_assignment
                    return True
        return False

    def visit_Assign(self, node: ast.Assign):
        if not self.maybe_assign_dict(node):
            self.maybe_assign_df(node)

        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            if alias.name == "pandas":
                # Use asname if available, otherwise use the module name
                self.import_aliases["pandas"] = alias.asname or alias.name

        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript):
        n = WrappedNode[ast.Subscript](node)
        if (frame_id := n.get("value").get("id").val) in self.frames.frame_keys():
            if isinstance(const := n.get("slice").val, ast.Constant):
                frame = self.frames.get_before(node.lineno, frame_id)
                if frame is not None:
                    self.column_accesses[const.value] = ColumnAccess(
                        node, node.lineno, const.value, frame
                    )

        self.generic_visit(node)


def parse_file(filename: str) -> ast.AST:
    """
    Parse a Python source file into an AST.

    Args:
        filename: Path to the Python file to parse

    Returns:
        The AST representation of the file
    """
    with open(filename, "r") as file:
        source = file.read()

    return ast.parse(source, filename=filename)


def main():
    import sys

    tree = parse_file(sys.argv[1])

    fc = FrameChecker()
    fc.visit(tree)
    fc.frames.get_before(45, "df")
    fc.column_accesses
    for access in fc.column_accesses.values():
        if access.id not in access.frame.columns:
            print(
                f"line[{access.lineno}]: TypeError: Column '{access.id}' not found in frame '{access.frame.id}' defined at {access.frame.lineno}"
            )
