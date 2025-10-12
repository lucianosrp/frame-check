import ast
import os
from pathlib import Path
from typing import Self, cast, override

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
        """
        This dictionary maps imported module names to their aliases.
        Example: {'pandas': 'pd'}
        If pandas is imported without an alias, like `import pandas`,
        then it will be {'pandas': 'pandas'}
        """

        self.frames: FrameHistory = FrameHistory()
        self.column_accesses: ColumnHistory = ColumnHistory()
        self.definitions: dict[str, ast.AST] = {}
        self.diagnostics: list[Diagnostic] = []
        self._col_assignment_subscripts: set[ast.Subscript] = set()
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
    
    def jaro_winkler(self, s1, s2):
        s1, s2 = s1.lower(), s2.lower()
        if s1 == s2:
            return 1.0

        len1, len2 = len(s1), len(s2)
        max_dist = int(max(len1, len2) / 2) - 1

        match = 0
        hash_s1 = [0] * len1
        hash_s2 = [0] * len2

        for i in range(len1):
            for j in range(max(0, i - max_dist), min(len2, i + max_dist + 1)):
                if s1[i] == s2[j] and hash_s2[j] == 0:
                    hash_s1[i] = 1
                    hash_s2[j] = 1
                    match += 1
                    break

        if match == 0:
            return 0.0

        t = 0
        point = 0
        for i in range(len1):
            if hash_s1[i]:
                while hash_s2[point] == 0:
                    point += 1
                if s1[i] != s2[point]:
                    t += 1
                point += 1
        t = t // 2

        jaro = (match / len1 + match / len2 + (match - t) / match) / 3.0

        # Jaro-Winkler adjustment
        prefix = 0
        for i in range(min(len1, len2)):
            if s1[i] == s2[i]:
                prefix += 1
            else:
                break
        prefix = min(4, prefix)

        return jaro + 0.1 * prefix * (1 - jaro)
        
    def zero_deps_jaro_winkler(self, target_col, existing_cols):
        jw_distances_dict = {
            col: abs(self.jaro_winkler(target_col, col))
            for col in existing_cols
        }
        
        target_value = max(jw_distances_dict.values())
        if target_value > 0.9:
            index = list(jw_distances_dict.values()).index(target_value)
            result = list(jw_distances_dict.keys())[index]
            return f"Column '{target_col}' does not exist, did you mean '{result}'?"
        else:
            return f"Column '{target_col}' does not exist"

    def _generate_diagnostics(self):
        """Generate diagnostics from collected column accesses."""
        for access in self.column_accesses.values():
            if access.id not in access.frame.columns:
                # zero-deps implementations of Jaro-Winkler distance (similarity >= 0.9)\
                message = self.zero_deps_jaro_winkler(access.id, access.frame.columns)
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

    def new_frame_instance(self, node: ast.Assign) -> "FrameInstance | None":  # type: ignore[return]
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
            )

    def maybe_assign_df(self, node: ast.Assign) -> bool:
        maybe_df = self.maybe_get_df(node)
        if maybe_df is not None:
            if frame := self.new_frame_instance(maybe_df):
                self.frames.add(frame)
                return True
        return False

    @override
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
                    )
                    subscript_slice = subscript.get("slice")
                    
                    match subscript_slice.val:
                        case ast.Constant():
                            new_frame.add_column_constant(subscript_slice.as_type(ast.Constant))
                        case ast.List():
                            new_frame.add_column_list(subscript_slice.as_type(ast.List))
                    
                    self.frames.add(new_frame)
                    # Store subscript as it is a column assignment
                    self._col_assignment_subscripts.add(target)

        self.maybe_assign_df(node)
        self.generic_visit(node)

    @override
    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            if alias.name == "pandas":
                # Use asname if available, otherwise use the module name
                self.import_aliases["pandas"] = alias.asname or alias.name

        self.generic_visit(node)

    @override
    def visit_Subscript(self, node: ast.Subscript):
        if (  # ignore subscript if it is a column assignment
            node not in self._col_assignment_subscripts
        ):
            n = WrappedNode[ast.Subscript](node)
            if (
                frame_id := n.get("value").get("id").val
            ) in self.frames.instance_keys():
                if isinstance(const := n.get("slice").val, ast.Constant) and isinstance(
                    const.value, str
                ):
                    frame = self.frames.get_before(node.lineno, frame_id)
                    if frame is not None:
                        start_col = node.value.end_col_offset or 0
                        underline_length = (node.end_col_offset or 0) - start_col
                        self.column_accesses[LineIdKey(node.lineno, const.value)] = (
                            ColumnInstance(
                                node,
                                node.lineno,
                                const.value,
                                frame,
                                start_col,
                                underline_length,
                            )
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
