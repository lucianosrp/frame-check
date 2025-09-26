import ast
from os import PathLike
from typing import Self, cast

from frame_check_core._ast import WrappedNode
from frame_check_core._models import (
    ColumnAccess,
    Diagnostic,
    FrameHistory,
    FrameHistoryKey,  # noqa: F401
    FrameInstance,
)


class FrameChecker(ast.NodeVisitor):
    def __init__(self):
        self.import_aliases: dict[str, str] = {}
        self.frames: FrameHistory = FrameHistory()
        self.column_accesses: dict[str, ColumnAccess] = {}
        self.definitions: dict[str, ast.AST] = {}
        self.diagnostics: list[Diagnostic] = []

    @classmethod
    def check(cls, code: str | ast.AST | PathLike[str]) -> Self:
        checker = cls()
        match code:
            case PathLike():
                with open(code, "r") as f:
                    tree = ast.parse(f.read())
            case str():
                if code.endswith(".py"):
                    with open(code, "r") as f:
                        tree = ast.parse(f.read())
                else:
                    tree = ast.parse(code)
            case ast.AST():
                tree = code

            case _:
                raise TypeError(f"Unsupported type: {type(code)}")

        checker.visit(tree)
        # Generate diagnostics
        checker._generate_diagnostics()
        return checker

    def _generate_diagnostics(self):
        """Generate diagnostics from collected column accesses."""
        for access in self.column_accesses.values():
            if access.id not in access.frame.columns:
                columns_list = "\n".join(f"  • {col}" for col in access.frame.columns)
                message = f"Column '{access.id}' does not exist"
                frame_hist = self.frames.get_before(access.lineno, access.frame.id)
                hint = None
                definition_location = None
                if frame_hist is not None:
                    hint = f"DataFrame '{access.frame.id}' was defined at line {frame_hist.lineno} with columns:\n{columns_list}"
                    definition_location = (
                        (frame_hist.data_arg.get("lineno").val or frame_hist.lineno),
                        0,
                    )

                diagnostic = Diagnostic(
                    message=message,
                    severity="error",
                    location=(access.lineno, 0),
                    hint=hint,
                    definition_location=definition_location,
                )
                self.diagnostics.append(diagnostic)

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
    for diagnostic in fc.diagnostics:
        print()
        print("-" * 78)
        print(path + f":{diagnostic.location[0]}")
        print(f"line[{diagnostic.location[0]}]: {diagnostic.message}")
