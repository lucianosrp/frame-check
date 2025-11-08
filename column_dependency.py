from collections import defaultdict


class ColumnDependency:
    def __init__(self):
        self.dependencies: defaultdict[str, set[str]] = defaultdict(set)

    def _add_dependency(self, dependent: str, dependency: str):
        self.dependencies[dependent].add(dependency)
        if dependency not in self.dependencies:
            self.dependencies[dependency] = set()

    def add_column(self, column: str, *, depends_on: str | None = None) -> None:
        if depends_on is not None:
            self._add_dependency(column, depends_on)

        if column not in self.dependencies:
            self.dependencies[column] = set()

    def get_independent_columns(self) -> list[str]:
        all_dependencies = {dep for deps in self.dependencies.values() for dep in deps}
        independent_columns = [
            col for col in self.dependencies if col not in all_dependencies
        ]
        return independent_columns


if __name__ == "__main__":
    tracker = ColumnDependency()
    tracker.add_column("column_b", depends_on="column_a")
    tracker.add_column("column_c", depends_on="column_a")
    tracker.add_column("column_d", depends_on="column_b")
    tracker.add_column("column_d", depends_on="column_c")
    tracker.add_column("column_e")
    print(tracker.dependencies)

    print(tracker.get_independent_columns())
