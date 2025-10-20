import ast
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import NamedTuple


def get_column_values(
    col: str | ast.expr | Iterable[str],
) -> Iterable[str]:
    match col:
        case str():
            yield from [col]
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
    lineno: int
    id: str
    data_arg: ast.List | ast.Dict | None
    keywords: list[ast.keyword]
    data_source_lineno: int | None = None
    columns: frozenset[str]

    @classmethod
    def new(
        cls,
        *,
        lineno: int,
        id: str,
        data_arg: ast.List | ast.Dict | None,
        keywords: list[ast.keyword],
        columns: Iterable[str] | ast.expr,
    ) -> "FrameInstance":
        return cls(
            lineno=lineno,
            id=id,
            data_arg=data_arg,
            keywords=keywords,
            columns=frozenset(get_column_values(columns)),
        )

    def new_instance(
        self,
        *,
        lineno: int,
        new_columns: Iterable[str] | ast.expr,
    ) -> "FrameInstance":
        return FrameInstance(
            lineno=lineno,
            id=self.id,
            data_arg=self.data_arg,
            keywords=self.keywords,
            columns=self.columns.union(get_column_values(new_columns)),
        )


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
