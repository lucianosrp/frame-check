from typing import Literal, overload

Strict = Literal["strict"]
Relaxed = Literal["relaxed"]


class FrameTracker[M: Strict | Relaxed]:
    """
    Tracks column dependencies in a DataFrame-like structure.

    In 'strict' mode: All column dependencies must exist, returns Diagnostic on errors.
    In 'relaxed' mode: Missing dependencies are auto-created, never returns errors.
    """

    __slots__ = ("id_", "columns", "mode", "_is_strict")

    def __init__(self, id_: str, mode: M = "strict") -> None:
        self.id_ = id_
        self.columns: dict[str, set[str]] = {}
        self.mode = mode
        self._is_strict = mode == "strict"

    @overload
    def try_get(
        self: "FrameTracker[Relaxed]",
        column: str,
    ) -> None: ...

    @overload
    def try_get(
        self: "FrameTracker[Strict]",
        column: str,
    ) -> str | None: ...

    def try_get(self, column: str) -> str | None:
        """
        Access a column (read operation).

        Args:
            column: The column name to access

        Returns:
            None on success (or in relaxed mode)
            Name of the column if it doesn't exist in strict mode
        """
        columns = self.columns

        if column in columns:
            return None

        if self._is_strict:
            return column

        # Relaxed mode: auto-create the column
        columns[column] = set()
        return None

    @overload
    def try_add(
        self: "FrameTracker[Relaxed]",
        column: str,
        *,
        depends_on: str | list[str] | None = None,
    ) -> None: ...

    @overload
    def try_add(
        self: "FrameTracker[Strict]",
        column: str,
        *,
        depends_on: None = None,
    ) -> None: ...

    @overload
    def try_add(
        self: "FrameTracker[Strict]",
        column: str,
        *,
        depends_on: str | list[str],
    ) -> list[str] | None: ...

    def try_add(
        self, column: str, *, depends_on: str | list[str] | None = None
    ) -> list[str] | None:
        """
        Add a column to the tracker (write operation), optionally with dependencies.

        In 'strict' mode:
            - If any dependency does not exist, returns a Diagnostic describing the missing dependency.
            - Otherwise, adds the column and its dependencies.

        In 'relaxed' mode:
            - Any missing dependencies are automatically created as independent columns.
            - Always returns None.

        Args:
            column: The column name to add or write.
            depends_on: Optional dependency column name(s). Can be a single string, a list of strings, or None.

        Returns:
            None on success (or always in relaxed mode).
            Name of the columns that are required to exist in strict mode
        """
        columns = self.columns  # Local reference for faster lookups

        # Case 1: Adding a column without dependencies (e.g., df['X'] = 1)
        if depends_on is None:
            if column not in columns:
                columns[column] = set()
            return None

        # Normalize depends_on to a list for uniform processing
        dependencies = [depends_on] if isinstance(depends_on, str) else depends_on

        # Case 2: Adding a column with dependencies (e.g., df['F'] = df['A'] + df['B'])
        # In strict mode, collect all missing dependencies first
        if self._is_strict:
            return [dep for dep in dependencies if dep not in columns]

        # Relaxed mode: auto-create any missing dependencies
        for dep in dependencies:
            if dep not in columns:
                columns[dep] = set()

        # All dependencies are valid (or were created), add them
        if column not in columns:
            columns[column] = set()
        columns[column].update(dependencies)
        return None

    @classmethod
    def new_with_columns(cls, id_: str, columns: list[str]) -> "FrameTracker[Strict]":
        """
        Create a new strict-mode tracker with a predefined schema.

        Args:
            id_: Tracker identifier
            columns: List of column names to initialize

        Returns:
            A new FrameTracker in strict mode with columns initialized
        """
        tracker = FrameTracker(id_, mode="strict")
        for column in columns:
            tracker.columns[column] = set()
        return tracker

    def get_core(self) -> list[str]:
        """
        Get all independent columns (columns with no dependencies).

        Returns:
            List of column names that don't depend on other columns
        """
        columns = self.columns
        return [col for col in columns if not columns[col]]


if __name__ == "__main__":
    print("=" * 50)
    print("Example 1: Relaxed Mode (Schema-less)")
    print("=" * 50)

    # df = pd.read_csv("data.csv")
    df = FrameTracker(id_="df", mode="relaxed")

    # df['A'] - Read operation
    # Note: when reading in 'relaxed mode', columns are automatically added as independent
    df.try_get("A")

    # df['B'] = df['C'] - Write B, read C
    df.try_add("B", depends_on="C")

    # df['D'] - Read operation
    df.try_get("D")

    # df['F'] = df['A'] + df['B'] - Write F, read A and B
    df.try_add("F", depends_on=["A", "B"])

    print(f"Core columns: {df.get_core()}")
    print(f"All dependencies: {dict(df.columns)}")
    # Core columns: ['A', 'C', 'D']
    # C is core because it was auto-created as independent
    # F depends on both A and B, so it's not core

    print("\n" + "=" * 50)
    print("Example 2: Strict Mode (Schema-defined)")
    print("=" * 50)

    # df1 = pd.read_csv("data.csv", usecols=['A', 'B'])
    df1 = FrameTracker.new_with_columns(id_="df1", columns=["A", "B"])

    # df1['A'] - Valid read
    result = df1.try_get("A")
    print(f"Reading 'A': {result}")

    # df1['B'] = df1['C'] - Invalid: C doesn't exist (read fails)
    result = df1.try_get("C")
    if result:
        print(f"Error reading C: {result}")

    # df1['F'] = df1['A'] + df1['B'] - Valid: both A and B exist
    df1.try_add("F", depends_on=["A", "B"])

    # df1['G'] = df1['X'] + df1['Y'] - Invalid: both don't exist
    result = df1.try_add("G", depends_on=["X", "Y"])
    if result:
        print(f"Error adding G with dependencies: {result}")

    # Now add X and Y first, then G will succeed
    # df1['X'] = 1 - Valid write, no deps
    df1.try_add("X")

    # df1['Y'] = 2 - Valid write, no deps
    df1.try_add("Y")

    # df1['G'] = df1['X'] + df1['Y'] - Now valid
    result = df1.try_add("G", depends_on=["X", "Y"])
    print(f"Adding G after creating X and Y: {result}")

    print(f"Core columns: {df1.get_core()}")
    print(f"All dependencies: {dict(df1.columns)}")
    # Core columns: ['A', 'B', 'X', 'Y']
    # B remains core because the invalid dependency was rejected
    # F depends on both A and B, so it's not core
    # G depends on X and Y (which are core), so G is not core
