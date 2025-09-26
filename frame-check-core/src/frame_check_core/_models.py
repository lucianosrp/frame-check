import ast
from dataclasses import dataclass, field
from typing import NamedTuple

from frame_check_core._ast import WrappedNode


@dataclass
class FrameInstance:
    _node: ast.Assign
    lineno: int
    id: str
    data_arg: WrappedNode[ast.Dict | None]
    keywords: list[WrappedNode[ast.keyword]]
    _columns: set[str] = field(default_factory=set)

    def _get_cols_from_data_arg(self) -> list[str]:
        arg = self.data_arg
        keys = arg.get("keys")
        return [key.value for key in keys.val] if keys.val is not None else []

    def add_columns(self, *columns: str | WrappedNode[str]):
        _cols_str = list(
            filter(
                lambda col: col is not None,
                [col.val if isinstance(col, WrappedNode) else col for col in columns],
            )
        )

        self._columns.update(_cols_str)  # type: ignore

    @property
    def columns(self) -> list[str]:
        return sorted(set(self._get_cols_from_data_arg()).union(self._columns))


@dataclass
class ColumnInstance:
    _node: ast.Subscript
    lineno: int
    id: str
    frame: FrameInstance


class LineIdKey(NamedTuple):
    lineno: int
    id: str


@dataclass
class Diagnostic:
    message: str
    severity: str
    location: tuple[int, int]
    hint: str | None = None
    definition_location: tuple[int, int] | None = None


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
