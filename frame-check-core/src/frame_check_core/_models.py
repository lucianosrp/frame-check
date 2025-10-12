import ast
from dataclasses import dataclass, field
from typing import NamedTuple, cast

from frame_check_core._ast import WrappedNode


@dataclass
class FrameInstance:
    _node: ast.Assign
    lineno: int
    id: str
    data_arg: WrappedNode[ast.Dict | None]
    keywords: list[WrappedNode[ast.keyword]]
    data_source_lineno: int | None = None
    _columns: set[str] = field(default_factory=set)

    def add_columns(self, *columns: str | WrappedNode[str]):
        _cols_str = list(
            filter(
                None,
                [col.val if isinstance(col, WrappedNode) else col for col in columns],
            )
        )

        self._columns.update(_cols_str)

    @property
    def columns(self) -> list[str]:
        return sorted(self._columns)


@dataclass
class ColumnInstance:
    _node: ast.Subscript
    lineno: int
    id: str
    frame: FrameInstance
    start_col: int
    underline_length: int


class LineIdKey(NamedTuple):
    lineno: int
    id: str


@dataclass
class Diagnostic:
    column_name: str
    message: str
    severity: str
    location: tuple[int, int]
    underline_length: int = 0
    hint: list[str] | None = None
    definition_location: tuple[int, int] | None = None
    data_source_location: tuple[int, int] | None = None


@dataclass
class InstanceHistory[I: FrameInstance | ColumnInstance]:
    instances: dict[LineIdKey, I] = field(default_factory=dict)

    def add(self, instance: I):
        key = LineIdKey(instance.lineno, instance.id)
        self.instances[key] = instance

    def get(self, id: str | None | WrappedNode[str]) -> list[I]:
        _id = id.val if isinstance(id, WrappedNode) else id
        return [instance for instance in self.instances.values() if instance.id == _id]

    def get_at(self, lineno: int, id: str) -> I | None:
        return self.instances.get(LineIdKey(lineno, id))

    def get_before(self, lineno: int, id: str) -> I | None:
        keys = sorted(self.instances.keys(), key=lambda k: k.lineno, reverse=True)
        for key in keys:
            if key.lineno < lineno and key.id == id:
                return self.instances[key]
        return None

    def instance_keys(self) -> list[str]:
        return [instance.id for instance in self.instances.values()]

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
        return any(instance.id == id for instance in self.instances.values())


FrameHistory = InstanceHistory[FrameInstance]
ColumnHistory = InstanceHistory[ColumnInstance]
