import ast
from dataclasses import dataclass, field
from typing import NamedTuple, cast

from frame_check_core._ast import WrappedNode


@dataclass
class FrameInstance:
    _node: ast.Assign | ast.Call
    lineno: int
    id: str
    data_arg: WrappedNode[ast.List | ast.Dict | None]
    keywords: list[WrappedNode[ast.keyword]]
    data_source_lineno: int | None = None
    _columns: set[str] = field(default_factory=set)

    def _get_cols_from_data_arg(self) -> list[str]:
        arg = self.data_arg
        if arg.val is None:
            return []
        if isinstance(arg.val, ast.Dict):
            dict_node = cast(ast.Dict, arg.val)
            keys_nodes = dict_node.keys
            cols: list[str] = []

            for k in keys_nodes:
                if isinstance(k, ast.Constant) and k.value is not None:
                    cols.append(str(k.value))
            return cols

        # If wrapped around Assign or other, try to get inner Dict
        if isinstance(arg.val, ast.Assign) and isinstance(arg.val.value, ast.Dict):
            inner_dict: WrappedNode = WrappedNode(arg.val.value)
            keys = inner_dict.get("keys")
            return [str(key.value) for key in keys.val] if keys.val is not None else []

        # If wrapped around List
        if isinstance(arg.val, ast.List):
            cols = []
            for elt in arg.val.elts:
                wrapped: WrappedNode = WrappedNode(elt)
                keys = wrapped.get("keys")
                if keys.val:
                    for k in keys.val:
                        if k.value not in cols:
                            cols.append(str(k.value))
            return cols
        return []

    def add_columns(self, *columns: str | WrappedNode[str]):
        _cols_str = list(
            filter(
                None,
                [col.val if isinstance(col, WrappedNode) else col for col in columns],
            )
        )

        self._columns.update(_cols_str)  # type: ignore

    def add_column_constant(self, constant_node: WrappedNode[ast.Constant]):
        match constant_node.get("value").val:
            case str(col_name):
                self.add_columns(col_name)

    def add_column_list(self, list_node: WrappedNode[ast.List]):
        for elt_node in list_node:
            match elt_node.val:
                case ast.Constant():
                    self.add_column_constant(elt_node)

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
