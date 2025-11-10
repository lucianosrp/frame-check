from __future__ import annotations
import ast
from abc import ABC
import bisect
from collections.abc import Iterable
from dataclasses import dataclass, field
from functools import cached_property, total_ordering
from .region import CodeRegion
from enum import IntEnum


class ColumnEventType(IntEnum):
    ADDED, REMOVED = range(2)


@dataclass(kw_only=True, frozen=True, slots=True)
class ColumnEvent:
    """Represents a change to a column in a data frame."""

    type: ColumnEventType = ColumnEventType.ADDED
    column_name: str


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
@total_ordering
class FrameInstance(ABC):
    """
    Represents an immutable event related to a data frame at a specific line number.

    This class stores information about a data frame, including its source location,
    identifier, data arguments, and columns.
    """

    id: str
    """
    Identifier for the frame
    """

    region: CodeRegion
    """
    Code region where this frame instance appears. By definition,
    it is impossible to have two frame instances within the same
    code region
    """

    column_events: list[ColumnEvent] = field(default_factory=list)
    """
    List of column events (additions, removals) associated with this frame instance.
    """

    _parent: FrameInstance | None = None
    """
    Parent frame event, if any
    """

    @cached_property
    def columns(self) -> set[str]:
        """Get the set of columns in this frame instance."""
        cols = set[str]()
        if self._parent:
            cols.update(self._parent.columns)
        for change in self.column_events:
            # We only care about added and removed columns here
            match change.type:
                case ColumnEventType.ADDED:
                    cols.add(change.column_name)
                case ColumnEventType.REMOVED:
                    cols.discard(change.column_name)
        return cols

    @cached_property
    def defined_region(self) -> CodeRegion:
        if self._parent:
            return self._parent.region
        return self.region

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, FrameInstance):
            return NotImplemented
        return self.id == other.id and self.region.end < other.region.start

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, FrameInstance):
            return NotImplemented
        return self.region == other.region and self.id == other.id

    @classmethod
    def new(
        cls,
        *,
        region: CodeRegion,
        id: str,
        columns: Iterable[str] | ast.expr,
    ) -> FrameInstance:
        """
        Create a new FrameCreationEvent with the specified properties.

        Args:
            region: Code region where this frame event appears
            id: Identifier for the frame
            columns: Column names to include in the event

        Returns:
            A new FrameInstance with the specified properties
        """
        return cls(
            region=region,
            id=id,
            column_events=[
                ColumnEvent(column_name=col) for col in get_column_values(columns)
            ],
        )

    def new_instance(
        self,
        *,
        region: CodeRegion,
        added_columns: Iterable[str] | None = None,
        removed_columns: Iterable[str] | None = None,
    ) -> FrameInstance:
        """
        Create a new FrameInstance based on the current instance with updated properties.

        This method creates a new frame instance that inherits properties from the current
        instance but with a new line number and additional columns.

        Args:
            region: Code region for the new frame instance
            new_column_definitions: Additional column definitions to merge with existing ones
            removed_columns: Columns to remove from the existing columns

        Returns:
            A new FrameInstance with updated properties
        """
        column_events: list[ColumnEvent] = []
        for added_column in added_columns or []:
            column_events.append(
                ColumnEvent(
                    type=ColumnEventType.ADDED,
                    column_name=added_column,
                )
            )
        for removed_column in removed_columns or []:
            column_events.append(
                ColumnEvent(
                    type=ColumnEventType.REMOVED,
                    column_name=removed_column,
                )
            )
        return FrameInstance(
            region=region,
            id=self.id,
            column_events=column_events,
            _parent=self,
        )


@dataclass(kw_only=True, slots=True)
class InstanceTimeline[I: FrameInstance]:
    id: str
    _instances: list[I] = field(default_factory=list)

    @property
    def latest_instance(self) -> I | None:
        if self._instances:
            return self._instances[-1]
        return None

    def add(self, instance: I):
        if instance.id != self.id:
            raise ValueError("Instance ID does not match timeline ID")
        # Fast path for appending at the end
        if self.latest_instance < instance:
            self._instances.append(instance)
        bisect.insort(self._instances, instance)

    def get_at_line(self, lineno: int) -> list[I]:
        """Retrieve all instances that cover the given line number."""

        left_inclusive = bisect.bisect_left(
            self._instances,
            FrameInstance(
                region=CodeRegion.from_tuples(start=(lineno, 0), end=(lineno + 1, 0)),
                id=self.id,
            ),
        )
        right_inclusive = bisect.bisect_right(
            self._instances,
            FrameInstance(
                region=CodeRegion.from_tuples(start=(lineno, 0), end=(lineno + 1, 0)),
                id=self.id,
            ),
        )
        return self._instances[left_inclusive:right_inclusive]

    def get_before_line(self, lineno: int) -> I | None:
        """Retrieve the latest instance before the given line number."""
        index = bisect.bisect_left(
            self._instances,
            FrameInstance(
                region=CodeRegion.from_tuples(start=(lineno, 0), end=(lineno + 1, 0)),
                id=self.id,
            ),
        )
        if index > 0:
            return self._instances[index - 1]
        return None


class InstanceMuseum[I: FrameInstance]:
    """Wrapper around multiple InstanceTimelines for easier access."""

    _timelines: dict[str, InstanceTimeline[I]] = field(default_factory=dict)

    def get(self, id: str) -> InstanceTimeline[I]:
        """Get the timeline for the given instance ID, creating it if it doesn't exist."""
        return self._timelines.setdefault(id, InstanceTimeline[I](id=id))

    def items(self):
        """Iterate over all timelines in the museum."""
        yield from self._timelines.items()

    @property
    def instance_ids(self) -> set[str]:
        """Get all instance IDs in the museum."""
        return set(self._timelines.keys())


FrameMuseum = InstanceMuseum[FrameInstance]
