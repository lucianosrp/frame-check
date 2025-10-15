import argparse
import ast
import glob
import os
import sys
from pathlib import Path
from typing import Callable, Self, cast, override

from frame_check_core._ast import WrappedNode
from frame_check_core._calls import DF, CallResult
from frame_check_core._col_similarity import zero_deps_jaro_winkler
from frame_check_core._message import print_diagnostics
from frame_check_core._models import (
    ColumnHistory,
    ColumnInstance,
    Diagnostic,
    FrameHistory,
    FrameInstance,
    LineIdKey,
)

ASSIGNING = "_frame_checker_assigning"
RESULT_COLS = "_frame_checker_result_columns"


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
                # zero-deps implementations of Jaro-Winkler distance (similarity >= 0.9)\
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
    ) -> WrappedNode[ast.List | ast.Dict | None]:
        arg0 = args[0]
        if isinstance(arg0_val := arg0.val, ast.Name):
            def_node = self.definitions.get(arg0_val.id)
            return WrappedNode(def_node)
        else:
            return cast(WrappedNode[ast.List | ast.Dict | None], arg0)

    def get_cols_from_data_arg(
        self, data_arg: WrappedNode[ast.List | ast.Dict | None]
    ) -> set[str]:
        arg = data_arg
        cols: set[str] = set()
        if arg.val is None:
            return set()
        if isinstance(arg.val, ast.Dict):
            dict_node = cast(ast.Dict, arg.val)
            keys_nodes = dict_node.keys

            for k in keys_nodes:
                if isinstance(k, ast.Constant) and k.value is not None:
                    cols.add(str(k.value))
            return cols

        # If wrapped around Assign or other, try to get inner Dict
        if isinstance(arg.val, ast.Assign) and isinstance(arg.val.value, ast.Dict):
            inner_dict: WrappedNode = WrappedNode(arg.val.value)
            keys = inner_dict.get("keys")
            return {key.value for key in keys.val} if keys.val is not None else set()  # type: ignore

        # If wrapped around List
        if isinstance(arg.val, ast.List):
            for elt in arg.val.elts:
                wrapped: WrappedNode = WrappedNode(elt)
                keys = wrapped.get("keys")
                if keys.val:
                    for k in keys.val:
                        if k.value not in cols:
                            cols.add(str(k.value))
            return cols
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
        usecols_value = WrappedNode[ast.List | ast.Name](usecols_kw.value)
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
        if not all(isinstance(e, ast.Constant) for e in elts):
            return None
        elts_const = cast(list[ast.Constant], elts)
        if all(isinstance(e.value, int) for e in elts_const):
            # Passing indices not column names
            return None
        if all(isinstance(e.value, str) for e in elts_const):
            columns = cast(list[str], [e.value for e in elts_const])
        else:
            return None

        return FrameInstance(
            node,
            node.lineno,
            df_name,
            WrappedNode(None),
            [WrappedNode[ast.keyword](kw) for kw in call_keywords.val or []],
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
                cast(WrappedNode[ast.List | ast.Dict | None], data_arg),
                [
                    WrappedNode[ast.keyword](kw)
                    for kw in call_keywords.val  # ty: ignore
                ],
                data_source_lineno=data_source_lineno,
                _columns=self.get_cols_from_data_arg(data_arg),
            )
        return None

    def maybe_assign_df(self, node: ast.Assign) -> bool:
        maybe_df = self.maybe_get_df(node)
        if maybe_df is not None:
            if frame := self.handle_df_creation(maybe_df):
                self.frames.add(frame)
                return True
        return False

    @override
    def visit_Assign(self, node: ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Subscript):
                setattr(target, ASSIGNING, True)

        self.generic_visit(node)

        for target in node.targets:
            if isinstance(target, ast.Name):
                # Defining a variable
                self.definitions[target.id] = node

            elif isinstance(target, ast.Subscript):
                subscript = WrappedNode[ast.Subscript](target)
                df_name = subscript.get("value").get("id").val
                df_name = df_name if df_name is not None else ""
                last_frame = self.frames.get_before(node.lineno, df_name)
                if last_frame:
                    # New column assignment to existing DataFrame
                    new_frame = FrameInstance(
                        node,
                        node.lineno,
                        last_frame.id,
                        cast(
                            WrappedNode[ast.List | ast.Dict | None], last_frame.data_arg
                        ),
                        last_frame.keywords,
                        _columns=set(last_frame._columns),
                    )
                    _col = subscript.get("slice").as_type(ast.Constant).get("value")
                    subscript_slice = subscript.get("slice")

                    match subscript_slice.val:
                        case ast.Constant():
                            new_frame.add_column_constant(
                                subscript_slice.as_type(ast.Constant)
                            )
                            new_frame.add_column_constant(
                                subscript_slice.as_type(ast.Constant)
                            )
                        case ast.List():
                            new_frame.add_column_list(subscript_slice.as_type(ast.List))

                    self.frames.add(new_frame)

        self.maybe_assign_df(node)

    @override
    def visit_Import(self, node: ast.Import):
        self.generic_visit(node)
        for alias in node.names:
            if alias.name == "pandas":
                # Use asname if available, otherwise use the module name
                self.import_aliases["pandas"] = alias.asname or alias.name

    @override
    def visit_Subscript(self, node: ast.Subscript):
        self.generic_visit(node)

        # ignore subscript if it is a column assignment
        if getattr(node, ASSIGNING, False):
            return

        n = WrappedNode[ast.Subscript](node)
        frame_id = n.get("value").get("id").val
        if frame_id not in self.frames.instance_keys():
            # not a dataframe
            self.generic_visit(node)
            return

        if not isinstance(const := n.get("slice").val, ast.Constant) or not isinstance(
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
            columns = None
            match node.func.value:
                case ast.Name():
                    frame_id = node.func.value.id
                    frame = self.frames.get_before(node.lineno, frame_id)
                    if frame is not None:
                        columns = set(frame.columns)
                case ast.Call():
                    if hasattr(node.func.value, RESULT_COLS):
                        columns = getattr(node.func.value, RESULT_COLS)

            if columns is None:
                return

            dfc = DF(columns)
            method: Callable[..., CallResult] | None = getattr(
                dfc, node.func.attr, None
            )
            if not callable(method):
                return

            updated, returned, error = method(node.args, node.keywords)
            if error is not None:
                self.column_accesses[LineIdKey(node.lineno, "")] = error
            if returned is not None:
                setattr(node, RESULT_COLS, returned)
            if updated != columns and frame_id is not None:
                new_frame = FrameInstance(
                    node,
                    node.lineno,
                    frame_id,
                    WrappedNode(None),
                    [],
                    None,
                    updated,
                )
                self.frames.add(new_frame)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser for frame-check CLI.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="frame-check",
        description="A static checker for dataframes!",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "files",
        type=str,
        nargs="*",
        help="Python files, directories, or glob patterns to check. "
        "If not specified, checks all .py files in current directory.",
    )

    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )

    return parser


def collect_python_files(paths: list[str]) -> list[Path]:
    """Collect all Python files from the given paths.

    Args:
        paths: List of file paths, directory paths, or glob patterns.
               If empty, defaults to all .py files in current directory recursively.

    Returns:
        List of Path objects for Python files to check.
    """
    if not paths:
        # Default: all .py files in current directory and subdirectories (recursive)
        return sorted(Path.cwd().rglob("*.py"))

    collected_files: set[Path] = set()

    for path_str in paths:
        path = Path(path_str)

        if path.is_file() and path.suffix == ".py":
            collected_files.add(path.resolve())
        elif path.is_dir():
            # Recursively find all .py files in the directory
            collected_files.update(path.rglob("*.py"))
        else:
            # treat as a glob pattern
            for matched_path in glob.glob(path_str, recursive=True):
                matched = Path(matched_path)
                if matched.is_file() and matched.suffix == ".py":
                    collected_files.add(matched.resolve())

    return sorted(collected_files)


def main(argv: list[str] | None = None) -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args(argv)

    # Collect all Python files to check
    python_files = collect_python_files(args.files)

    if not python_files:
        print("No Python files found to check.", file=sys.stderr)
        return 0

    # Track if any file has diagnostics
    has_errors = False

    # Process each file
    for file_path in python_files:
        try:
            fc = FrameChecker.check(file_path)
            if fc.diagnostics:
                has_errors = True
                print_diagnostics(fc, str(file_path))

        except SyntaxError as e:
            print(f"Syntax error in {file_path}:\n{e}", file=sys.stderr)
            has_errors = True
        except Exception as e:
            print(f"Error checking {file_path}:\n{e}", file=sys.stderr)
            has_errors = True

    return 1 if has_errors else 0
