from dataclasses import dataclass, field
from pathlib import Path
from functools import cached_property


@dataclass(kw_only=True, frozen=True)
class CodeSource:
    code: str = ""
    path: Path | None = field(default=None)

    @cached_property
    def is_file(self) -> bool:
        return self.path is not None

    @cached_property
    def is_ast(self) -> bool:
        return not self.is_file and self.code == ""

    @cached_property
    def is_code(self) -> bool:
        return not self.is_file and not self.is_code
