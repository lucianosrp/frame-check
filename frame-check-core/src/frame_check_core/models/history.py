import ast
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import NamedTuple
from .region import CodeRegion


def get_column_values(
    col: str | ast.expr | Iterable[str],
) -> Iterable[str]:
    match col:
        case str():
            yield col
        case ast.Constant():
            match col.value:
                case str(value):
                    yield value
        case ast.List():
            for elt_node in col.elts:
                match elt_node:
                    case ast.Constant():
                        yield from get_column_values(elt_node)
                    case ast.List():
                        yield from get_column_values(elt_node)
        case Iterable():
            yield from col
        case _:
            yield from []


@dataclass(kw_only=True, frozen=True, slots=True)
class FrameInstance:
    """
    Represents an immutable instance of a data frame at a specific line number.

    This class stores information about a data frame, including its source location,
    identifier, data arguments, and columns.
    """

    region: CodeRegion
    """
    Code region where this frame instance appears
    """

    defined_region: CodeRegion
    """
    Code region where this frame instance is first defined
    """

    id: str
    """
    Identifier for the frame
    """

    columns: frozenset[str]
    """
    Set of column names in this frame
    """

    @classmethod
    def new(
        cls,
        *,
        region: CodeRegion,
        id: str,
        columns: Iterable[str] | ast.expr,
    ) -> "FrameInstance":
        """
        Create a new FrameInstance with the given parameters.

        Args:
            lineno: Line number where the frame appears
            id: Identifier for the frame
            keywords: Keyword arguments for the frame
            columns: Column names to include in the frame

        Returns:
            A new FrameInstance with the specified properties
        """
        return cls(
            region=region,
            id=id,
            columns=frozenset(get_column_values(columns)),
            defined_region=region,
        )

    def new_instance(
        self,
        *,
        region: CodeRegion,
        new_columns: Iterable[str] | ast.expr,
    ) -> "FrameInstance":
        """
        Create a new FrameInstance based on the current instance with updated properties.

        This method creates a new frame instance that inherits properties from the current
        instance but with a new line number and additional columns.

        Args:
            lineno: New line number for the frame instance
            new_columns: Additional columns to merge with existing columns

        Returns:
            A new FrameInstance with updated properties
        """
        return FrameInstance(
            region=region,
            id=self.id,
            columns=self.columns.union(get_column_values(new_columns)),
            defined_region=self.defined_region,
        )


@dataclass(kw_only=True)
class ColumnInstance:
    _node: ast.Subscript
    id: str
    region: CodeRegion
    frame: FrameInstance


class LineIdKey(NamedTuple):
    lineno: int
    id: str


@dataclass(kw_only=True, slots=True)
class InstanceHistory[I: FrameInstance | ColumnInstance]:
    instances: dict[LineIdKey, I] = field(default_factory=dict)

    def add(self, instance: I):
        key = LineIdKey(instance.region.start.row, instance.id)
        self.instances[key] = instance

    def get(self, id: str | None) -> list[I]:
        return [instance for instance in self.instances.values() if instance.id == id]

    def get_at(self, lineno: int, id: str) -> I | None:
        return self.instances.get(LineIdKey(lineno, id))

    def get_before(self, lineno: int, id: str) -> I | None:
        # Filter only keys with matching id first (dictionary lookup is O(1))
        matching_keys = [k for k in self.instances.keys() if k.id == id]

        # Then sort only those keys
        matching_keys.sort(key=lambda k: k.lineno, reverse=True)
        for key in matching_keys:
            if key.lineno < lineno:
                return self.instances[key]
        return None

    def instance_ids(self) -> set[str]:
        return {instance.id for instance in self.instances.values()}

    def values(self) -> list[I]:
        return list(self.instances.values())

    def __len__(self) -> int:
        return len(self.instances)

    def __setitem__(self, key: LineIdKey, value: I):
        self.instances[key] = value

    def __getitem__(self, key: LineIdKey) -> I:
        return self.instances[key]

    def __contains__(self, item: LineIdKey) -> bool:
        return item in self.instances

    def contains_id(self, id: str) -> bool:
        return id in self.instance_ids()


FrameHistory = InstanceHistory[FrameInstance]
ColumnHistory = InstanceHistory[ColumnInstance]
