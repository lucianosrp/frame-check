from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path


class IllegalAccess:
    pass


class Severity(StrEnum):
    ERROR = "error"


@dataclass(kw_only=True, frozen=True, slots=True)
class CodeSource:
    path: Path | None = field(default=None)
    code: str = ""

    @property
    def is_traceable(self) -> bool:
        """Check if the code is traceable to a source file or code string."""
        return self.path is not None or self.code != ""


@dataclass(kw_only=True)
class Diagnostic:
    column_name: str
    message: str
    severity: Severity
    location: tuple[int, int]
    underline_length: int = 0
    hint: list[str] | None = None
    name_suggestion: str | None = None
    definition_location: tuple[int, int] | None = None
    data_source_location: tuple[int, int] | None = None
