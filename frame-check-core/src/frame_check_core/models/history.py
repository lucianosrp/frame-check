import ast
from dataclasses import dataclass, field
from functools import cached_property
from typing import NamedTuple


@dataclass(kw_only=True)
class FrameInstance:
    lineno: int
    id: str
    data_arg: ast.List | ast.Dict | None
    keywords: list[ast.keyword]
    data_source_lineno: int | None = None
    _columns: set[str] = field(default_factory=set)

    def add_columns(self, *columns: str):
        _cols_str = list(filter(None, columns))
        self._columns.update(_cols_str)

    def add_column_constant(self, constant_node: ast.Constant):
        match constant_node.value:
            case str(col_name):
                self.add_columns(col_name)

    def add_column_list(self, list_node: ast.List):
        for elt_node in list_node.elts:
            match elt_node:
                case ast.Constant():
                    self.add_column_constant(elt_node)

    @cached_property
    def columns(self) -> list[str]:
        return sorted(self._columns)


@dataclass(kw_only=True)
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


@dataclass(kw_only=True)
class InstanceHistory[I: FrameInstance | ColumnInstance]:
    instances: dict[LineIdKey, I] = field(default_factory=dict)

    def add(self, instance: I):
        key = LineIdKey(instance.lineno, instance.id)
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
        return any(instance.id == id for instance in self.instances.values())


FrameHistory = InstanceHistory[FrameInstance]
ColumnHistory = InstanceHistory[ColumnInstance]
