import ast
import os
from pathlib import Path
from typing import Self, override

from .ast.models import (
    DF,
    PD,
    Result,
    get_result,
    is_assigning,
    set_assigning,
    set_result,
)
from .models.diagnostic import CodeSource, Diagnostic, Severity
from .models.history import (
    ColumnHistory,
    ColumnInstance,
    FrameHistory,
    FrameInstance,
    LineIdKey,
)
from .util.col_similarity import zero_deps_jaro_winkler


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
        self.source: CodeSource

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
            checker.source = CodeSource(path=Path(code), code=source)
        elif isinstance(code, str):
            tree = ast.parse(code)
            checker.source = CodeSource(code=code)
        elif isinstance(code, ast.Module):
            tree = code
            checker.source = CodeSource()
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
                data_line = f"DataFrame '{access.frame.id}' created at line {access.frame.defined_lino}"
                data_line += " with columns:"
                hints = [data_line]

                for col in sorted(access.frame.columns):
                    hints.append(f"  • {col}")
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
                    definition_location=(access.frame.defined_lino, 0),
                )
                self.diagnostics.append(diagnostic)

    def _maybe_create_df(self, node: ast.Assign) -> None:
        match node.value:
            case ast.Call(
                func=ast.Attribute(value=ast.Name(), attr=attr),
                args=args,
                keywords=keywords,
            ):
                if method := PD.get_method(attr):
                    created, error = method(args, keywords, self.definitions)
                    if error is not None:
                        pass  # TODO
                    if created is not None:
                        new_frame = FrameInstance.new(
                            lineno=node.lineno,
                            id=node.targets[0].id
                            if isinstance(node.targets[0], ast.Name)
                            else "",
                            data_arg=None,
                            keywords=[],
                            columns=created.columns,
                        )
                        self.frames.add(new_frame)

    @override
    def visit_Assign(self, node: ast.Assign):
        for target in node.targets:
            set_assigning(target)
            match target:
                case ast.Subscript(value=ast.Name(id=df_name), slice=subscript_slice):
                    df_name = df_name or ""
                    if last_frame := self.frames.get_before(node.lineno, df_name):
                        # CAM-1: direct column assignment to existing DataFrame
                        new_frame = last_frame.new_instance(
                            lineno=node.lineno, new_columns=subscript_slice
                        )
                        self.frames.add(new_frame)

                case ast.Name(id=id):
                    # any other value assignemnt like foo = "something"
                    self.definitions[id] = get_result(node.value, self.definitions)

        self.generic_visit(node)
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
            return

        frame_id = node.value.id
        if frame_id not in self.frames.instance_ids():
            return

        if not isinstance(const := node.slice, ast.Constant) or not isinstance(
            const.value, str
        ):
            return

        # referencing a column by string constant
        frame = self.frames.get_before(node.lineno, frame_id)
        if frame is not None:
            start_col = node.value.end_col_offset or 0
            underline_length = (node.end_col_offset or 0) - start_col
            # record this column access
            self.column_accesses[LineIdKey(node.lineno, const.value)] = ColumnInstance(
                _node=node,
                lineno=node.lineno,
                id=const.value,
                frame=frame,
                start_col=start_col,
                underline_length=underline_length,
            )

    @override
    def visit_Call(self, node: ast.Call):
        self.generic_visit(node)

        if isinstance(node.func, ast.Attribute):
            df = None
            match node.func.value:
                case ast.Name(frame_id):
                    if frame := self.frames.get_before(node.lineno, frame_id):
                        df = DF(frame.columns)
                case ast.Call(val):
                    result = get_result(val, self.definitions)
                    if isinstance(result, DF):
                        df = result

            if df is None:
                return

            method = df.get_method(node.func.attr)

            if method is None:
                return

            method(args=node.args, keywords=node.keywords)
            updated, returned, error = method(node.args, node.keywords)
            if error is not None:
                # self.column_accesses[LineIdKey(node.lineno, "")] = error
                pass
            if returned is not None:
                set_result(node, returned)
            if df.columns != updated.columns and frame is not None:
                new_frame = frame.new_instance(
                    lineno=node.lineno,
                    new_columns=updated.columns,
                )
                self.frames.add(new_frame)
