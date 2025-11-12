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
from .models.history import FrameInstance, FrameMuseum, get_column_values
from .models.region import CodeRegion
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

        self.frame_museum: FrameMuseum = FrameMuseum()
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

        # Generate diagnostics
        checker.visit(tree)
        return checker

    def _add_illegal_access_diagnostic(
        self, frame: FrameInstance, illegal_column: str, access_region: CodeRegion
    ):
        data_line = (
            f"DataFrame '{frame.id}' created at line {frame.defined_region.start.row}"
        )
        data_line += " with columns:"
        hints = [data_line]

        for col in sorted(frame.columns):
            hints.append(f"  • {col}")
        message = f"Column '{illegal_column}' does not exist"
        similar_col = zero_deps_jaro_winkler(illegal_column, frame.columns)
        if similar_col:
            message += f", did you mean '{similar_col}'?"
        else:
            message += "."

        diagnostic = Diagnostic(
            column_name=illegal_column,
            message=message,
            severity=Severity.ERROR,
            region=access_region,
            hint=hints,
            definition_region=frame.defined_region,
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
                        df_name = (
                            node.targets[0].id
                            if isinstance(node.targets[0], ast.Name)
                            else ""
                        )
                        new_frame = FrameInstance.new(
                            region=CodeRegion.from_ast_node(node=node.targets[0]),
                            id=df_name,
                            columns=created.columns,
                        )
                        self.frame_museum.get(df_name).add(new_frame)

    @override
    def visit_Assign(self, node: ast.Assign):
        for target in node.targets:
            match target:
                case ast.Subscript(value=ast.Name(id=df_name), slice=subscript_slice):
                    set_assigning(target)
                    df_name = df_name or ""
                    timeline = self.frame_museum.get(df_name)
                    if (latest_frame := timeline.latest_instance) is not None:
                        new_frame = latest_frame.new_instance(
                            region=CodeRegion.from_ast_node(node=target),
                            added_columns=get_column_values(subscript_slice),
                        )
                        timeline.add(new_frame)
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
        if frame_id not in self.frame_museum.instance_ids:
            return

        if not isinstance(const := node.slice, ast.Constant) or not isinstance(
            const.value, str
        ):
            return

        latest_frame = self.frame_museum.get(frame_id).latest_instance
        if latest_frame is None:
            return

        # record this illegal column access with just the column name (string constant)
        if const.value not in latest_frame.columns:
            self._add_illegal_access_diagnostic(
                frame=latest_frame,
                illegal_column=const.value,
                access_region=CodeRegion.from_ast_node(node=node),
            )

    @override
    def visit_Call(self, node: ast.Call):
        self.generic_visit(node)

        if isinstance(node.func, ast.Attribute):
            df = None
            match node.func.value:
                case ast.Name(frame_id):
                    frame = self.frame_museum.get(frame_id).latest_instance
                    if frame is not None:
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

            updated, returned, error = method(node.args, node.keywords)
            if error is not None:
                # self.column_accesses[LineIdKey(node.lineno, "")] = error
                pass
            if returned is not None:
                set_result(node, returned)
            if df.columns != updated.columns and frame is not None:
                new_frame = frame.new_instance(
                    region=CodeRegion.from_ast_node(node=node),
                    added_columns=updated.columns,
                )
                self.frame_museum.get(new_frame.id).add(new_frame)
