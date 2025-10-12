import ast
import os
from pathlib import Path
from typing import Self, cast

from frame_check_core._ast import WrappedNode
from frame_check_core._message import print_diagnostics
from frame_check_core._models import (
    ColumnHistory,
    ColumnInstance,
    Diagnostic,
    FrameHistory,
    FrameInstance,
    LineIdKey,
)


class FrameChecker(ast.NodeVisitor):
    def __init__(self):
        self.import_aliases: dict[str, str] = {}
        self.frames: FrameHistory = FrameHistory()
        self.column_accesses: ColumnHistory = ColumnHistory()
        self.definitions: dict[str, ast.AST] = {}
        self.diagnostics: list[Diagnostic] = []
        self._col_assignment_subscripts: set[ast.Subscript] = set()
        self.source = ""
        self.df_creation_handlers = {
            "DataFrame": self.new_frame_instance,
            "read_csv": self.frame_from_read_csv,
        }

    @classmethod
    def check(cls, code: str | ast.Module | Path) -> Self:
        """Check the given code for DataFrame column access issues.
        This is the main entry point for the FrameChecker.

        Parses the provided code, analyzes it for potential column access errors
        in pandas DataFrames, and generates diagnostics.

        Args:
            code (str | ast.Module | Path): The code to check. Can be a string of Python code,
                a file path to a Python file, or an already parsed AST module.

        Returns:
            Self: An instance of FrameChecker with the analysis completed and diagnostics generated.

        Raises:
            TypeError: If the code parameter is not one of the supported types.
        """
        checker = cls()
        if isinstance(code, (str, Path)) and os.path.isfile(str(code)):
            with open(str(code), "r") as f:
                source = f.read()
                tree = ast.parse(source)
            checker.source = source
        elif isinstance(code, str):
            tree = ast.parse(code)
            checker.source = code
        elif isinstance(code, ast.Module):
            tree = code
            checker.source = ""
        else:
            raise TypeError(f"Unsupported type: {type(code)}")

        checker.visit(tree)
        # Generate diagnostics
        checker._generate_diagnostics()
        return checker

    def _generate_diagnostics(self):
        """Generate diagnostics from collected column accesses."""
        for access in self.column_accesses.values():
            if access.id not in access.frame.columns:
                message = f"Column '{access.id}' does not exist"
                data_line = f"DataFrame '{access.frame.id}' created at line {access.frame.lineno}"
                if access.frame.data_source_lineno is not None:
                    data_line += f" from data defined at line {access.frame.data_source_lineno}"
                data_line += " with columns:"
                hints = [data_line]
                for col in sorted(access.frame.columns):
                    hints.append(f"  • {col}")
                definition_location = (access.frame.lineno, 0)
                data_source_location = (
                    (access.frame.data_source_lineno, 0)
                    if access.frame.data_source_lineno is not None
                    else None
                )

                diagnostic = Diagnostic(
                    column_name=access.id,
                    message=message,
                    severity="error",
                    location=(access.lineno, access.start_col),
                    underline_length=access.underline_length,
                    hint=hints,
                    definition_location=definition_location,
                    data_source_location=data_source_location,
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
            and func.get("attr").val in self.df_creation_handlers
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

    def get_cols_from_data_arg(
        self, data_arg: WrappedNode[ast.Dict | None]
    ) -> set[str]:
        arg = data_arg
        if arg.val is None:
            return set()
        if isinstance(arg.val, ast.Dict):
            keys = arg.get("keys")
            return (
                {cast(str, key.value) for key in keys.val}
                if keys.val is not None
                else set()
            )

        # If wrapped around Assign or other, try to get inner Dict
        if isinstance(arg.val, ast.Assign) and isinstance(
            arg.val.value, ast.Dict
        ):
            inner_dict = WrappedNode(arg.val.value)
            keys = inner_dict.get("keys")
            return (
                {key.value for key in keys.val}
                if keys.val is not None
                else set()
            )  # type: ignore
        return set()

    def handle_df_creation(self, node: ast.Assign) -> FrameInstance | None:
        """Routes DataFrame creation calls to the appropriate handler."""
        df_creator = WrappedNode(node.value).get("func").get("attr").val or ""
        handler = self.df_creation_handlers.get(df_creator)
        return handler and handler(node)

    def frame_from_read_csv(self, node: ast.Assign) -> FrameInstance | None:
        """
        Handle pd.read_csv calls to create FrameInstance.
        Reads the column list from the 'usecols' keyword argument if present.
        If not, ignores the DataFrame.
        """
        # Basic implementation reads list contents of usecols kwarg iff
        # This is a list of string constants or a variable assigned to such a list.
        # TODO: Handle longer assignment chains, including variables within the list
        n = WrappedNode[ast.Assign](node)
        call_keywords = n.get("value").get("keywords")
        usecols_kw: ast.keyword | None = None
        for kw in call_keywords.val or []:
            if kw.arg == "usecols":
                usecols_kw = kw
                break
        if usecols_kw is None:
            return None
        usecols_value = WrappedNode(usecols_kw.value)
        df_name = n.targets[0].get("id").val
        assert df_name is not None
        data_source_lineno = None
        match usecols_value.val:
            case ast.List(elts):
                pass
            case ast.Name(name):
                def_node = self.definitions.get(name)
                if not isinstance(def_node, ast.Assign):
                    return None
                if not isinstance(def_node.value, ast.List):
                    return None
                data_source_lineno = def_node.lineno
                elts = def_node.value.elts
            case _:
                return None
        if not all(
            isinstance(e, ast.Constant)
            for e in elts
        ):
            return None
        elts = cast(list[ast.Constant], elts)
        if all(isinstance(e.value, int) for e in elts):
            # Passing indices not column names
            return None
        if all(isinstance(e.value, str) for e in elts):
            columns = cast(list[str], [e.value for e in elts])
        else:
            return None
    
        return FrameInstance(
            node,
            node.lineno,
            df_name,
            WrappedNode(None),
            [
                WrappedNode[ast.keyword](kw)
                for kw in call_keywords.val or []
            ],
            data_source_lineno=data_source_lineno,
            _columns=set(columns),
        )

    def new_frame_instance(self, node: ast.Assign) -> FrameInstance | None:
        n = WrappedNode[ast.Assign](node)
        original_arg = n.get("value").get("args")[0]
        data_arg = self.resolve_args(n.get("value").get("args"))
        call_keywords = n.get("value").get("keywords")
        name = n.targets[0].get("id")

        data_source_lineno = None
        if isinstance(original_arg.val, ast.Name):
            def_node = self.definitions.get(original_arg.val.id)
            if isinstance(def_node, ast.Assign):
                data_source_lineno = def_node.lineno

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
                data_source_lineno=data_source_lineno,
                _columns=self.get_cols_from_data_arg(data_arg),
            )

    def maybe_assign_df(self, node: ast.Assign) -> bool:
        maybe_df = self.maybe_get_df(node)
        if maybe_df is not None:
            if frame := self.handle_df_creation(maybe_df):
                self.frames.add(frame)
                return True
        return False

    def visit_Assign(self, node: ast.Assign):
        # Store definitions:
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.definitions[target.id] = node

            elif isinstance(target, ast.Subscript):
                subscript = WrappedNode[ast.Subscript](target)
                subscript_value = subscript.get("value")
                frames = self.frames.get(subscript_value.get("id"))
                if frames:
                    last_frame = frames[-1]
                    # Create a new frame instance for the column
                    new_frame = FrameInstance(
                        node,
                        node.lineno,
                        last_frame.id,
                        last_frame.data_arg,
                        last_frame.keywords,
                        _columns=set(last_frame._columns)
                    )
                    col = (
                        subscript.get("slice")
                        .as_type(ast.Constant)
                        .get("value")
                    )
                    new_frame.add_columns(col)
                    self.frames.add(new_frame)
                    # Store subscript as it is a column assignment
                    self._col_assignment_subscripts.add(target)

        self.maybe_assign_df(node)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            if alias.name == "pandas":
                # Use asname if available, otherwise use the module name
                self.import_aliases["pandas"] = alias.asname or alias.name

        self.generic_visit(node)

    def visit_Subscript(self, node: ast.Subscript):
        if (  # ignore subscript if it is a column assignment
            node not in self._col_assignment_subscripts
        ):
            n = WrappedNode[ast.Subscript](node)
            if (
                frame_id := n.get("value").get("id").val
            ) in self.frames.instance_keys():
                if isinstance(
                    const := n.get("slice").val, ast.Constant
                ) and isinstance(const.value, str):
                    frame = self.frames.get_before(node.lineno, frame_id)
                    if frame is not None:
                        start_col = node.value.end_col_offset or 0
                        underline_length = (
                            node.end_col_offset or 0
                        ) - start_col
                        self.column_accesses[
                            LineIdKey(node.lineno, const.value)
                        ] = ColumnInstance(
                            node,
                            node.lineno,
                            const.value,
                            frame,
                            start_col,
                            underline_length,
                        )

            self.generic_visit(node)


def main():
    import sys

    if len(sys.argv) != 2:
        print("Usage: python -m frame_check_core <file.py>", file=sys.stderr)
        sys.exit(1)
    path = sys.argv[1]
    fc = FrameChecker.check(path)
    print_diagnostics(fc, path)
