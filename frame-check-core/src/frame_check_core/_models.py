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

    @property
    def columns(self) -> list[str]:
        arg = self.data_arg
        keys = arg.get("keys")
        return [key.value for key in keys.val] if keys.val is not None else []


@dataclass
class ColumnAccess:
    _node: ast.Subscript
    lineno: int
    id: str
    frame: FrameInstance


class FrameHistoryKey(NamedTuple):
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
class FrameHistory:
    frames: dict[FrameHistoryKey, FrameInstance] = field(default_factory=dict)

    def add(self, frame: FrameInstance):
        key = FrameHistoryKey(frame.lineno, frame.id)
        self.frames[key] = frame

    def get(self, id: str) -> list[FrameInstance]:
        return [frame for frame in self.frames.values() if frame.id == id]

    def get_at(self, lineno: int, id: str) -> FrameInstance | None:
        return self.frames.get(FrameHistoryKey(lineno, id))

    def get_before(self, lineno: int, id: str) -> FrameInstance | None:
        keys = sorted(self.frames.keys(), key=lambda k: k.lineno, reverse=True)
        for key in keys:
            if key.lineno < lineno and key.id == id:
                return self.frames[key]
        return None

    def frame_keys(self) -> list[str]:
        return [frame.id for frame in self.frames.values()]
