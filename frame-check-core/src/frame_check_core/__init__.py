import ast
from dataclasses import dataclass, field
from os import PathLike
from typing import NamedTuple, Self, cast

from frame_check_core._models import WrappedNode


@dataclass
class FrameInstance:
    _node: ast.Assign
    lineno: int
    id: str
    data_arg: WrappedNode[ast.Dict | None]
    keywords: list[WrappedNode[ast.keyword]]

    @property
    def columns(self) -> list[str]:
        arg = self.data_arg
        keys = arg.get("keys")
        return [key.value for key in keys.val] if keys.val is not None else []


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
        self.import_aliases: dict[str, str] = {}
        self.frames: FrameHistory = FrameHistory()
        self.column_accesses: dict[str, ColumnAccess] = {}
        self.definitions: dict[str, ast.AST] = {}

    @classmethod
    def check(cls, code: str | ast.AST | PathLike[str]) -> Self:
        checker = cls()
        match code:
            case str():
                tree = ast.parse(code)
            case PathLike():
                with open(code, "r") as f:
                    tree = ast.parse(f.read())
            case _:
                tree = code
        checker.visit(tree)
        return checker

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

    def resolve_args(
        self, args: WrappedNode[list[ast.Name | ast.Dict]]
    ) -> WrappedNode[ast.Dict | None]:
        arg0 = args[0]
        if isinstance(arg0_val := arg0.val, ast.Name):
            def_node = self.definitions.get(arg0_val.id)
            return WrappedNode(def_node)
        else:
            return cast(WrappedNode[ast.Dict | None], arg0)

    def new_frame_instance(self, node: ast.Assign) -> "FrameInstance | None":
        n = WrappedNode[ast.Assign](node)
        data_arg = self.resolve_args(n.get("value").get("args"))
        call_keywords = n.get("value").get("keywords")
        name = n.targets[0].get("id")

        if (
            name.val is not None
            and data_arg.val is not None
            and call_keywords.val is not None
        ):
            return FrameInstance(
                node,
                node.lineno,
                name.val,
                data_arg,
                [
                    WrappedNode[ast.keyword](kw)
                    for kw in call_keywords.val  # ty: ignore
                ],
            )

    def maybe_assign_df(self, node: ast.Assign) -> bool:
        maybe_df = self.maybe_get_df(node)
        if maybe_df is not None:
            if frame := self.new_frame_instance(maybe_df):
                self.frames.add(frame)
                return True
        return False

    def visit_Assign(self, node: ast.Assign):
        # Store definitions:
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.definitions[target.id] = node.value

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


def main():
    import sys

    path = sys.argv[1]
    fc = FrameChecker.check(path)
    for access in fc.column_accesses.values():
        if access.id not in access.frame.columns:
            print()
            print("-" * 78)
            print(path + f":{access.lineno}")
            print(
                f"line[{access.lineno}]: TypeError: Column '{access.id}' not found in frame '{access.frame.id}' defined at {access.frame.lineno}"
            )
            print(f"\t\tWith data defined at {access.frame.data_arg.get('lineno').val}")
