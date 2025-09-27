from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from frame_check_core import FrameChecker


def print_diagnostics(fc: "FrameChecker", path: str) -> None:
    """Print formatted diagnostics to stdout, matching README style."""
    if not fc.diagnostics:
        return

    lines = fc.source.splitlines() if fc.source else []
    import re

    for diag in fc.diagnostics:
        line_num = diag.location[0]
        col_num = diag.location[1]
        column_match = re.search(r"Column '([^']+)' does not exist", diag.message)
        colored_message = diag.message
        if column_match:
            column = column_match.group(1)
            colored_message = f"Column '{column}' does not exist"
        print(f"{path}:{line_num}:{col_num + 1} - {diag.severity}: {colored_message}")
        print("  |")
        if 0 <= line_num - 1 < len(lines):
            original_line = lines[line_num - 1]
            indent = len(original_line) - len(original_line.lstrip())
            code_line = original_line.lstrip()
            relative_col = max(0, col_num - indent)
            code_before = code_line[:relative_col]
            colored_part = (
                f"{code_line[relative_col : relative_col + diag.underline_length]}"
            )
            code_after = code_line[relative_col + diag.underline_length :]
            print(f"{line_num}|{code_before}{colored_part}{code_after}")
            spaces = " " * relative_col
            underlines = "^" * diag.underline_length
            print(f"  |{spaces}{underlines}")
        else:
            print(f"{line_num}| <line not available>")
            print("  |          ^^^")
        print("  |")
        if diag.hint:
            for hline in diag.hint:
                if hline.startswith("  • "):
                    prefix = hline[:4]
                    col_name = hline[4:]
                    print(f"  | {prefix}{col_name}")
                else:
                    print(f"  | {hline}")
            print("  |")
        print()

        # Note for data source if available
        if (
            hasattr(diag, "data_source_location")
            and diag.data_source_location is not None
        ):
            data_line_num = diag.data_source_location[0]
            print("--- Note: Data defined here with these columns ---")
            print("  |")
            if 0 <= data_line_num - 1 < len(lines):
                original_line = lines[data_line_num - 1]
                indent = len(original_line) - len(original_line.lstrip())
                code_line = original_line.lstrip()
                print(f" {data_line_num}|{code_line}")
                print(f"  |{'~' * len(code_line)}")
            else:
                print(f" {data_line_num}| <line not available>")
                print("  |          ~~~")
            print("  |")
            if diag.hint and len(diag.hint) > 1:
                for hline in diag.hint[1:]:
                    if hline.startswith("  • "):
                        prefix = hline[:4]
                        col_name = hline[4:]
                        print(f"  | {prefix}{col_name}")
                    else:
                        print(f"  | {hline}")
            print("  |")
            print()
