import ast
import os
from pathlib import Path
from typing import Self, override

from .ast.models import (
    Result,
    is_assigning,
    set_assigning,
    get_result,
    set_result,
)
from .ast.models import PD, DF
from .util.col_similarity import zero_deps_jaro_winkler
from .models.history import (
    ColumnHistory,
    ColumnInstance,
    FrameHistory,
    FrameInstance,
    LineIdKey,
)
from .models.diagnostic import Diagnostic, Severity


class FrameChecker(ast.NodeVisitor):
    def __init__(self) -> None:
        self.import_aliases: dict[str, str] = {}
        """
        This dictionary maps imported module names to their aliases.
        Example: {'pandas': 'pd'}
        If pandas is imported without an alias, like `import pandas`,
        then it will be {'pandas': 'pandas'}
        """

        self.frames: FrameHistory = FrameHistory()
        self.column_accesses: ColumnHistory = ColumnHistory()
        self.definitions: dict[str, Result] = {}
        self.diagnostics: list[Diagnostic] = []
        self.source = ""

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
                data_line = f"DataFrame '{access.frame.id}' created at line {access.frame.lineno}"
                if access.frame.data_source_lineno is not None:
                    data_line += (
                        f" from data defined at line {access.frame.data_source_lineno}"
                    )
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
                message = f"Column '{access.id}' does not exist"
                similar_col = zero_deps_jaro_winkler(access.id, access.frame.columns)
                if similar_col:
                    message += f", did you mean '{similar_col}'?"
                else:
                    message += "."

                diagnostic = Diagnostic(
                    column_name=access.id,
                    message=message,
                    severity=Severity.ERROR,
                    location=(access.lineno, access.start_col),
                    underline_length=access.underline_length,
                    hint=hints,
                    definition_location=definition_location,
                    data_source_location=data_source_location,
                )
                self.diagnostics.append(diagnostic)

    def get_cols_from_data_arg(self, arg: ast.AST | None) -> set[str]:
        cols: set[str] = set()

        if arg is None:
            return set()

        if isinstance(arg, ast.Dict):
            keys_nodes = arg.keys

            for k in keys_nodes:
                if isinstance(k, ast.Constant) and isinstance(k.value, str):
                    cols.add(k.value)
            return cols

        # If wrapped around Assign or other, try to get inner Dict
        if isinstance(arg, ast.Assign) and isinstance(arg.value, ast.Dict):
            inner_dict = arg.value
            keys = inner_dict.keys
            for key in keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    cols.add(key.value)
            return cols

        # If wrapped around List
        if isinstance(arg, ast.List):
            for elt in arg.elts:
                if isinstance(elt, ast.Dict):
                    keys = elt.keys
                    for k in keys:
                        if isinstance(k, ast.Constant) and isinstance(k.value, str):
                            cols.add(k.value)
            return cols

        return set()

    def _maybe_create_df(self, node: ast.Assign) -> None:
        if not isinstance(node.value, ast.Call):
            return
        func = node.value.func
        if not isinstance(func, ast.Attribute) or not isinstance(func.value, ast.Name):
            return
        method = PD.get_method(func.attr)
        if method is None:
            return
        created, error = method(node.value.args, node.value.keywords)
        if error is not None:
            pass  # TODO
        if created is not None:
            new_frame = FrameInstance(
                node,
                node.lineno,
                node.targets[0].id if isinstance(node.targets[0], ast.Name) else "",
                None,
                [],
                node.lineno,
                created.columns,
            )
            self.frames.add(new_frame)

    @override
    def visit_Assign(self, node: ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Subscript):
                set_assigning(target)

        self.generic_visit(node)

        for target in node.targets:
            if isinstance(target, ast.Name):
                # Defining a variable
                self.definitions[target.id] = get_result(node.value)

            elif isinstance(target, ast.Subscript):
                subscript = target
                if not isinstance(subscript.value, ast.Name):
                    continue

                df_name = subscript.value.id
                df_name = df_name if df_name is not None else ""
                last_frame = self.frames.get_before(node.lineno, df_name)
                if last_frame:
                    # New column assignment to existing DataFrame
                    new_frame = FrameInstance(
                        node,
                        node.lineno,
                        last_frame.id,
                        last_frame.data_arg,
                        last_frame.keywords,
                        _columns=set(last_frame._columns),
                    )
                    subscript_slice = subscript.slice

                    match subscript_slice:
                        case ast.Constant():
                            new_frame.add_column_constant(subscript_slice)
                        case ast.List():
                            new_frame.add_column_list(subscript_slice)

                    self.frames.add(new_frame)

        self._maybe_create_df(node)

    @override
    def visit_Import(self, node: ast.Import):
        self.generic_visit(node)
        for alias in node.names:
            if alias.name == "pandas":
                # Use asname if available, otherwise use the module name
                self.import_aliases["pandas"] = alias.asname or alias.name

    @override
    def visit_Name(self, node):
        self.generic_visit(node)
        if node.id in self.definitions:
            set_result(node, self.definitions[node.id])

    @override
    def visit_Subscript(self, node: ast.Subscript):
        self.generic_visit(node)

        # ignore subscript if it is a column assignment
        if is_assigning(node):
            return

        if not isinstance(node.value, ast.Name):
            self.generic_visit(node)
            return

        frame_id = node.value.id
        if frame_id not in self.frames.instance_keys():
            # not a dataframe
            self.generic_visit(node)
            return

        if not isinstance(const := node.slice, ast.Constant) or not isinstance(
            const.value, str
        ):
            # not a constant string column access
            self.generic_visit(node)
            return

        # referencing a column by string constant
        frame = self.frames.get_before(node.lineno, frame_id)
        if frame is not None:
            start_col = node.value.end_col_offset or 0
            underline_length = (node.end_col_offset or 0) - start_col
            # record this column access
            self.column_accesses[LineIdKey(node.lineno, const.value)] = ColumnInstance(
                node,
                node.lineno,
                const.value,
                frame,
                start_col,
                underline_length,
            )

        self.generic_visit(node)

    @override
    def visit_Call(self, node: ast.Call):
        self.generic_visit(node)

        if isinstance(node.func, ast.Attribute):
            frame_id = None
            df = None
            match node.func.value:
                case ast.Name():
                    frame_id = node.func.value.id
                    frame = self.frames.get_before(node.lineno, frame_id)
                    if frame is not None:
                        df = DF(frame.columns)
                case ast.Call():
                    result = get_result(node.func.value)
                    if isinstance(result, DF):
                        df = result

            if df is None:
                return

            method = df.get_method(node.func.attr)

            if method is None:
                return

            updated, returned, error = method(node.args, node.keywords)
            if error is not None:
                # self.column_accesses[LineIdKey(node.lineno, "")] = error
                pass
            if returned is not None:
                set_result(node, returned)
            if df.columns != updated.columns and frame_id is not None:
                new_frame = FrameInstance(
                    node,
                    node.lineno,
                    frame_id,
                    None,
                    [],
                    None,
                    updated.columns,
                )
                self.frames.add(new_frame)
